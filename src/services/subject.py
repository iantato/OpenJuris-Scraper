import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from embedder.providers.base import BaseEmbedder
from models.subject import Subject
from models.subject_link import DocumentSubjectLink
from schemas.scraped_document import ScrapedDocument


class SubjectExtractionService:
    """Service for extracting subjects from documents using LLM."""

    # Common Philippine legal subject areas
    LEGAL_SUBJECT_KEYWORDS = {
        "Criminal Law": ["crime", "criminal", "penalty", "imprisonment", "fine", "prosecution", "accused", "conviction", "acquittal"],
        "Civil Law": ["civil", "contract", "obligation", "property", "ownership", "damages", "tort", "negligence"],
        "Constitutional Law": ["constitution", "constitutional", "rights", "due process", "equal protection", "bill of rights"],
        "Administrative Law": ["administrative", "government agency", "regulation", "public service", "civil service"],
        "Commercial Law": ["business", "corporation", "commercial", "trade", "securities", "partnership", "banking"],
        "Labor Law": ["employment", "worker", "labor", "wages", "benefits", "union", "nlrc", "dole"],
        "Tax Law": ["tax", "taxation", "revenue", "customs", "duties", "bir", "assessment"],
        "Family Law": ["marriage", "family", "child", "custody", "adoption", "annulment", "support"],
        "Remedial Law": ["procedure", "jurisdiction", "venue", "appeal", "certiorari", "mandamus", "injunction"],
        "Evidence": ["evidence", "witness", "testimony", "hearsay", "burden of proof", "admissibility"],
        "Land Registration": ["land", "title", "registration", "torrens", "cadastral", "reconstitution"],
        "Election Law": ["election", "suffrage", "comelec", "electoral", "campaign", "voting"],
        "Environmental Law": ["environment", "pollution", "denr", "natural resources", "mining", "forestry"],
        "Agrarian Reform": ["agrarian", "land reform", "dar", "tenant", "agricultural land", "carp"],
        "Intellectual Property": ["patent", "trademark", "copyright", "intellectual property", "infringement"],
        "Public International Law": ["treaty", "international", "extradition", "diplomatic", "sovereignty"],
    }

    SUBJECT_EXTRACTION_PROMPT = """You are a legal document analysis expert specializing in Philippine law.
Analyze the following legal document and extract the main legal subjects/topics.

Focus on identifying:
1. Primary areas of law (e.g., Criminal Law, Civil Law, Constitutional Law)
2. Specific legal doctrines or principles discussed
3. Key legal procedures or remedies mentioned
4. Relevant government agencies or institutions

Document Type: {document_type}
Document Title: {title}

Document Content:
{content}

Return your response as a JSON array of strings containing 3-8 specific legal subjects.
Example: ["Criminal Law", "Evidence", "Due Process", "Search and Seizure"]

Return ONLY the JSON array, no additional text or explanation."""

    def __init__(self, session: AsyncSession, embedder: Optional[BaseEmbedder] = None):
        self.session = session
        self.embedder = embedder

    async def extract_subjects(
        self,
        document: ScrapedDocument,
        use_llm: bool = True
    ) -> List[str]:
        """
        Extract subjects from a scraped document.

        Args:
            document: The scraped document to analyze
            use_llm: Whether to use LLM for extraction (falls back to keywords if False or LLM fails)

        Returns:
            List of subject names
        """
        subjects = []

        if use_llm and self.embedder:
            subjects = await self._extract_with_llm(document)

        # Fallback to keyword extraction if LLM fails or is disabled
        if not subjects:
            subjects = self._extract_with_keywords(document)

        # Clean and validate
        return self._clean_subjects(subjects)

    async def _extract_with_llm(self, document: ScrapedDocument) -> List[str]:
        """Extract subjects using LLM."""
        try:
            # Prepare document content
            content = self._prepare_content(document)

            prompt = self.SUBJECT_EXTRACTION_PROMPT.format(
                document_type=document.document_type.value if document.document_type else "Unknown",
                title=document.title or "Untitled",
                content=content
            )

            # Use embedder's chat completion if available
            if hasattr(self.embedder, 'chat_completion'):
                response = await self.embedder.chat_completion(prompt)
            elif hasattr(self.embedder, 'generate'):
                response = await self.embedder.generate(prompt)
            else:
                logger.warning("Embedder does not support text generation, falling back to keywords")
                return []

            # Parse JSON response
            return self._parse_llm_response(response)

        except Exception as e:
            logger.error(f"LLM subject extraction failed: {e}")
            return []

    def _extract_with_keywords(self, document: ScrapedDocument) -> List[str]:
        """Extract subjects using keyword matching."""
        content = self._prepare_content(document).lower()
        found_subjects = []

        for subject, keywords in self.LEGAL_SUBJECT_KEYWORDS.items():
            # Check if any keyword appears in the content
            matches = sum(1 for keyword in keywords if keyword.lower() in content)
            if matches >= 2:  # Require at least 2 keyword matches
                found_subjects.append((subject, matches))

        # Sort by number of matches and return top subjects
        found_subjects.sort(key=lambda x: x[1], reverse=True)
        return [subject for subject, _ in found_subjects[:6]]

    def _prepare_content(self, document: ScrapedDocument) -> str:
        """Prepare document content for analysis."""
        parts = []

        if document.title:
            parts.append(document.title)

        if document.abstract:
            parts.append(document.abstract)

        # Add content from document parts
        if document.parts:
            for part in document.parts:
                if part.content:
                    parts.append(part.content)

        # Join and truncate
        full_text = "\n\n".join(parts)
        return full_text[:10000]  # Limit for LLM context

    def _parse_llm_response(self, response: str) -> List[str]:
        """Parse LLM response to extract subject list."""
        try:
            # Clean response
            response = response.strip()

            # Try to find JSON array in response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                subjects = json.loads(json_str)

                if isinstance(subjects, list):
                    return [str(s).strip() for s in subjects if s and str(s).strip()]

            logger.warning(f"Could not parse LLM response as JSON array: {response[:100]}")
            return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []

    def _clean_subjects(self, subjects: List[str]) -> List[str]:
        """Clean and deduplicate subjects."""
        cleaned = []
        seen = set()

        for subject in subjects:
            subject = subject.strip()

            # Validate length
            if len(subject) < 3 or len(subject) > 100:
                continue

            # Check for duplicates (case-insensitive)
            subject_lower = subject.lower()
            if subject_lower in seen:
                continue

            seen.add(subject_lower)
            cleaned.append(subject)

        return cleaned[:8]  # Maximum 8 subjects

    async def get_or_create_subject(self, name: str, description: Optional[str] = None) -> Subject:
        """Get an existing subject by name or create a new one."""
        # Try to find existing subject
        stmt = select(Subject).where(Subject.name.ilike(name))
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # Create new subject
        new_subject = Subject(
            name=name,
            description=description or f"Auto-extracted legal subject: {name}"
        )
        self.session.add(new_subject)
        await self.session.flush()  # Get the ID without committing

        logger.debug(f"Created new subject: {name}")
        return new_subject

    async def get_or_create_subjects(self, names: List[str]) -> List[Subject]:
        """Get or create multiple subjects."""
        subjects = []
        for name in names:
            subject = await self.get_or_create_subject(name)
            subjects.append(subject)
        return subjects

    async def link_subjects_to_document(
        self,
        document_id: int,
        subjects: List[Subject]
    ) -> List[DocumentSubjectLink]:
        """Link subjects to a document."""
        links = []

        for subject in subjects:
            # Check if link already exists
            stmt = select(DocumentSubjectLink).where(
                DocumentSubjectLink.document_id == document_id,
                DocumentSubjectLink.subject_id == subject.id
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                links.append(existing)
                continue

            # Create new link
            link = DocumentSubjectLink(
                document_id=document_id,
                subject_id=subject.id
            )
            self.session.add(link)
            links.append(link)

        await self.session.flush()
        return links

    async def extract_and_link_subjects(
        self,
        document_id: int,
        scraped_document: ScrapedDocument,
        use_llm: bool = True
    ) -> List[Subject]:
        """
        Extract subjects from a scraped document and link them to the database document.

        Args:
            document_id: ID of the document in the database
            scraped_document: The scraped document data
            use_llm: Whether to use LLM for extraction

        Returns:
            List of linked Subject models
        """
        try:
            # Extract subject names
            subject_names = await self.extract_subjects(scraped_document, use_llm=use_llm)

            if not subject_names:
                logger.debug(f"No subjects extracted for document {document_id}")
                return []

            # Get or create subject entities
            subjects = await self.get_or_create_subjects(subject_names)

            # Link to document
            await self.link_subjects_to_document(document_id, subjects)

            logger.info(f"Linked {len(subjects)} subjects to document {document_id}: {subject_names}")
            return subjects

        except Exception as e:
            logger.error(f"Failed to extract and link subjects for document {document_id}: {e}")
            return []