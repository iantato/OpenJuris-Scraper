from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.document_part import DocumentPart
from schemas.scraped_document import ScrapedPart

class DocumentBuilder:
    """Build ORM models from scraped document data"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def build_document_parts(
        self,
        scraped_parts: list[ScrapedPart],
        document_id: UUID,
        parent_id: Optional[UUID] = None,
    ) -> list[DocumentPart]:
        """
        Recursively convert ScrapedPart trees into flat list of DocumentPart models.
        """
        result: list[DocumentPart] = []

        for part in scraped_parts:
            doc_part = DocumentPart(
                document_id=document_id,
                parent_id=parent_id,
                section_type=part.section_type,
                label=part.label,
                content_text=part.content_text or "",
                content_markdown=part.content_markdown or "",
                content_html=part.content_html,
                sort_order=part.sort_order,
            )

            result.append(doc_part)

            # Recursively process children
            if part.children:
                children = self.build_document_parts(
                    part.children,
                    document_id,
                    parent_id=doc_part.id,
                )
                result.extend(children)

        return result