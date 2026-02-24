import os
import csv
import json
import tarfile
import tempfile
import asyncio
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import httpx
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.document import Document
from models.document_part import DocumentPart
from models.subject import Subject
from models.source import Source
from models.document_relation import DocumentRelation
from config import Settings


class JSONEncoderExtended(json.JSONEncoder):
    """Extended JSON encoder for UUID, date, datetime objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class ExportService:
    """Service for exporting data to CSV, JSON, and tar.gz archives."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = Settings()

    async def export_all(self, output_dir: str = "exports") -> str:
        """
        Export all data to CSV and JSON files, then compress to tar.gz.

        Returns the path to the generated tar.gz file.
        """
        # Create a temporary directory for export files
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Exporting data to temporary directory: {temp_dir}")

            # Export each model
            await self._export_sources(temp_dir)
            await self._export_subjects(temp_dir)
            await self._export_documents(temp_dir)
            await self._export_document_parts(temp_dir)
            await self._export_document_relations(temp_dir)
            await self._export_raw_html(temp_dir)

            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"openjuris_export_{timestamp}.tar.gz"
            archive_path = os.path.join(output_dir, archive_name)

            # Create tar.gz archive
            self._create_tar_gz(temp_dir, archive_path)

            logger.info(f"Export completed: {archive_path}")
            return archive_path

    async def _export_sources(self, output_dir: str) -> None:
        """Export sources to CSV and JSON."""
        logger.info("Exporting sources...")

        result = await self.session.execute(select(Source))
        sources = result.scalars().all()

        data = []
        for source in sources:
            record = {
                "id": str(source.id),
                "name": source.name.value if source.name else None,
                "short_code": source.short_code,
                "base_url": source.base_url,
                "type": source.type.value if source.type else None,
                "created_at": source.created_at.isoformat() if source.created_at else None,
            }
            data.append(record)

        self._write_csv(data, os.path.join(output_dir, "sources.csv"))
        self._write_json(data, os.path.join(output_dir, "sources.json"))
        logger.info(f"Exported {len(data)} sources")

    async def _export_subjects(self, output_dir: str) -> None:
        """Export subjects to CSV and JSON."""
        logger.info("Exporting subjects...")

        result = await self.session.execute(select(Subject))
        subjects = result.scalars().all()

        data = []
        for subject in subjects:
            record = {
                "id": str(subject.id),
                "name": subject.name,
                "description": subject.description,
                "parent_id": str(subject.parent_id) if subject.parent_id else None,
            }
            data.append(record)

        self._write_csv(data, os.path.join(output_dir, "subjects.csv"))
        self._write_json(data, os.path.join(output_dir, "subjects.json"))
        logger.info(f"Exported {len(data)} subjects")

    async def _export_documents(self, output_dir: str) -> None:
        """Export documents to CSV and JSON."""
        logger.info("Exporting documents...")

        result = await self.session.execute(
            select(Document).options(selectinload(Document.subjects))
        )
        documents = result.scalars().all()

        data = []
        for doc in documents:
            record = {
                "id": str(doc.id),
                "canonical_citation": doc.canonical_citation,
                "title": doc.title,
                "short_title": doc.short_title,
                "category": doc.category.value if doc.category else None,
                "doc_type": doc.doc_type.value if doc.doc_type else None,
                "date_promulgated": doc.date_promulgated.isoformat() if doc.date_promulgated else None,
                "date_published": doc.date_published.isoformat() if doc.date_published else None,
                "date_effectivity": doc.date_effectivity.isoformat() if doc.date_effectivity else None,
                "source_id": str(doc.source_id) if doc.source_id else None,
                "source_url": doc.source_url,
                "content_markdown": doc.content_markdown,
                "metadata_fields": json.dumps(doc.metadata_fields, cls=JSONEncoderExtended),
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "subject_ids": json.dumps([str(s.id) for s in doc.subjects]) if doc.subjects else "[]",
            }
            data.append(record)

        self._write_csv(data, os.path.join(output_dir, "documents.csv"))
        self._write_json(data, os.path.join(output_dir, "documents.json"))
        logger.info(f"Exported {len(data)} documents")

    async def _export_document_parts(self, output_dir: str) -> None:
        """Export document parts to CSV and JSON."""
        logger.info("Exporting document parts...")

        result = await self.session.execute(select(DocumentPart))
        parts = result.scalars().all()

        data = []
        for part in parts:
            record = {
                "id": str(part.id),
                "document_id": str(part.document_id) if part.document_id else None,
                "part_type": part.part_type.value if hasattr(part, 'part_type') and part.part_type else None,
                "section_number": getattr(part, 'section_number', None),
                "title": getattr(part, 'title', None),
                "content": getattr(part, 'content', None),
                "order_index": getattr(part, 'order_index', None),
                "parent_id": str(part.parent_id) if hasattr(part, 'parent_id') and part.parent_id else None,
            }
            data.append(record)

        self._write_csv(data, os.path.join(output_dir, "document_parts.csv"))
        self._write_json(data, os.path.join(output_dir, "document_parts.json"))
        logger.info(f"Exported {len(data)} document parts")

    async def _export_document_relations(self, output_dir: str) -> None:
        """Export document relations to CSV and JSON."""
        logger.info("Exporting document relations...")

        result = await self.session.execute(select(DocumentRelation))
        relations = result.scalars().all()

        data = []
        for rel in relations:
            record = {
                "id": str(rel.id),
                "source_id": str(rel.source_id),
                "target_id": str(rel.target_id),
                "target_part_id": str(rel.target_part_id) if rel.target_part_id else None,
                "relation_type": rel.relation_type.value if rel.relation_type else None,
                "target_scope": rel.target_scope,
                "verbatim_text": rel.verbatim_text,
                "created_at": rel.created_at.isoformat() if rel.created_at else None,
            }
            data.append(record)

        self._write_csv(data, os.path.join(output_dir, "document_relations.csv"))
        self._write_json(data, os.path.join(output_dir, "document_relations.json"))
        logger.info(f"Exported {len(data)} document relations")

    def _get_category_folder(self, doc: Document) -> str:
        """Determine the category folder path for a document."""
        category = doc.category.value if doc.category else "Unknown"
        doc_type = doc.doc_type.value if doc.doc_type else "Other"

        # Clean up names for folder structure
        category_clean = self._sanitize_folder_name(category)
        doc_type_clean = self._sanitize_folder_name(doc_type)

        return os.path.join(category_clean, doc_type_clean)

    def _sanitize_folder_name(self, name: str) -> str:
        """Convert a string to a safe folder name."""
        # Replace problematic characters
        safe = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        safe = safe.replace(":", "-").replace("*", "").replace("?", "")
        safe = safe.replace('"', "").replace("<", "").replace(">", "")
        safe = safe.replace("|", "-")
        return safe

    async def _export_raw_html(self, output_dir: str) -> None:
        """Export raw HTML content by fetching from source URLs, organized by category and type.
           Also export document markdown files into a parallel category folder structure.
        """
        logger.info("Exporting raw HTML and markdown from source URLs...")

        html_base_dir = os.path.join(output_dir, "raw_html")
        markdown_base_dir = os.path.join(output_dir, "markdown")
        os.makedirs(html_base_dir, exist_ok=True)
        os.makedirs(markdown_base_dir, exist_ok=True)

        result = await self.session.execute(select(Document))
        documents = result.scalars().all()

        count_success = 0
        count_failed = 0
        failed_urls = []
        index_data = []
        category_stats = {}

        # Prepare headers from scraper settings
        headers = {
            "User-Agent": "OpenJuris | Legal Document Archive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # Create HTTP client with scraper settings
        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout,
            follow_redirects=True,
            headers=headers,
            limits=httpx.Limits(
                max_keepalive_connections=self.settings.max_concurrent_requests,
                max_connections=self.settings.max_concurrent_requests
            )
        ) as client:
            for idx, doc in enumerate(documents):
                if not doc.source_url:
                    logger.debug(f"Skipping document {doc.id}: No source URL")
                    continue

                try:
                    logger.debug(f"Fetching HTML for {doc.canonical_citation} from {doc.source_url}")

                    # Respect rate limiting
                    if idx > 0 and self.settings.requests_per_second > 0:
                        await asyncio.sleep(self.settings.requests_per_second)

                    # Fetch the HTML from the source URL
                    response = await client.get(doc.source_url)
                    response.raise_for_status()

                    # Get the HTML content
                    html_content = response.text

                    # Determine category folder
                    category_folder = self._get_category_folder(doc)
                    html_category_path = os.path.join(html_base_dir, category_folder)
                    md_category_path = os.path.join(markdown_base_dir, category_folder)
                    os.makedirs(html_category_path, exist_ok=True)
                    os.makedirs(md_category_path, exist_ok=True)

                    # Create a safe filename from the citation
                    safe_name = self._sanitize_filename(doc.canonical_citation)
                    html_filename = f"{safe_name}.html"
                    html_path = os.path.join(html_category_path, html_filename)

                    # Write the HTML to file
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    # Write markdown if available
                    md_written = False
                    md_filename = f"{safe_name}.md"
                    md_path = os.path.join(md_category_path, md_filename)
                    if doc.content_markdown:
                        try:
                            with open(md_path, "w", encoding="utf-8") as mf:
                                mf.write(doc.content_markdown)
                            md_written = True
                        except Exception:
                            md_written = False

                    # Add to index
                    html_relative = os.path.join(category_folder, html_filename)
                    md_relative = os.path.join(category_folder, md_filename) if md_written else None
                    index_item = {
                        "id": str(doc.id),
                        "canonical_citation": doc.canonical_citation,
                        "category": doc.category.value if doc.category else None,
                        "doc_type": doc.doc_type.value if doc.doc_type else None,
                        "source_url": doc.source_url,
                        "html_filepath": html_relative,
                        "html_filename": html_filename,
                        "html_status": "success",
                        "html_content_length": len(html_content),
                        "markdown_filepath": md_relative,
                        "markdown_filename": md_filename if md_written else None,
                        "markdown_status": "success" if md_written else "missing",
                        "markdown_content_length": len(doc.content_markdown) if md_written else 0
                    }
                    index_data.append(index_item)

                    # Update category statistics
                    category_key = category_folder
                    if category_key not in category_stats:
                        category_stats[category_key] = {
                            "html_count": 0,
                            "html_total_size": 0,
                            "markdown_count": 0,
                            "markdown_total_size": 0
                        }
                    category_stats[category_key]["html_count"] += 1
                    category_stats[category_key]["html_total_size"] += len(html_content)
                    if md_written:
                        category_stats[category_key]["markdown_count"] += 1
                        category_stats[category_key]["markdown_total_size"] += len(doc.content_markdown)

                    count_success += 1

                    # Log progress every 10 documents
                    if count_success % 10 == 0:
                        logger.info(f"Progress: {count_success} documents fetched...")

                except httpx.HTTPStatusError as e:
                    logger.warning(f"HTTP error fetching {doc.source_url}: {e.response.status_code}")
                    failed_urls.append({
                        "id": str(doc.id),
                        "canonical_citation": doc.canonical_citation,
                        "category": doc.category.value if doc.category else None,
                        "doc_type": doc.doc_type.value if doc.doc_type else None,
                        "source_url": doc.source_url,
                        "error": f"HTTP {e.response.status_code}",
                        "error_type": "http_status_error"
                    })
                    count_failed += 1

                except httpx.TimeoutException as e:
                    logger.warning(f"Timeout fetching {doc.source_url}: {str(e)}")
                    failed_urls.append({
                        "id": str(doc.id),
                        "canonical_citation": doc.canonical_citation,
                        "category": doc.category.value if doc.category else None,
                        "doc_type": doc.doc_type.value if doc.doc_type else None,
                        "source_url": doc.source_url,
                        "error": f"Timeout after {self.settings.request_timeout}s",
                        "error_type": "timeout"
                    })
                    count_failed += 1

                except httpx.RequestError as e:
                    logger.warning(f"Request error fetching {doc.source_url}: {str(e)}")
                    failed_urls.append({
                        "id": str(doc.id),
                        "canonical_citation": doc.canonical_citation,
                        "category": doc.category.value if doc.category else None,
                        "doc_type": doc.doc_type.value if doc.doc_type else None,
                        "source_url": doc.source_url,
                        "error": str(e),
                        "error_type": "request_error"
                    })
                    count_failed += 1

                except Exception as e:
                    logger.error(f"Unexpected error fetching {doc.source_url}: {str(e)}")
                    failed_urls.append({
                        "id": str(doc.id),
                        "canonical_citation": doc.canonical_citation,
                        "category": doc.category.value if doc.category else None,
                        "doc_type": doc.doc_type.value if doc.doc_type else None,
                        "source_url": doc.source_url,
                        "error": str(e),
                        "error_type": "unexpected_error"
                    })
                    count_failed += 1

        # Write the index file with successful fetches
        self._write_json(index_data, os.path.join(html_base_dir, "_index.json"))

        # Write category statistics
        stats_summary = {
            "total_documents": count_success + count_failed,
            "successful": count_success,
            "failed": count_failed,
            "categories": {}
        }

        for category_path, stats in category_stats.items():
            stats_summary["categories"][category_path] = {
                "html_count": stats["html_count"],
                "html_total_size_bytes": stats["html_total_size"],
                "html_total_size_mb": round(stats["html_total_size"] / (1024 * 1024), 2),
                "markdown_count": stats["markdown_count"],
                "markdown_total_size_bytes": stats["markdown_total_size"],
                "markdown_total_size_mb": round(stats["markdown_total_size"] / (1024 * 1024), 2)
            }

        self._write_json(stats_summary, os.path.join(html_base_dir, "_statistics.json"))
        # also write a copy of statistics for markdown root
        self._write_json(stats_summary, os.path.join(markdown_base_dir, "_statistics.json"))

        # Write failed URLs log if any
        if failed_urls:
            self._write_json(failed_urls, os.path.join(html_base_dir, "_failed.json"))
            self._write_json(failed_urls, os.path.join(markdown_base_dir, "_failed.json"))
            logger.warning(f"Failed to fetch {count_failed} documents. See _failed.json for details.")

        # Log category summary
        logger.info(f"Exported {count_success} raw HTML files across {len(category_stats)} categories")
        for category_path, stats in sorted(category_stats.items()):
            logger.info(f"  {category_path}: {stats['html_count']} HTML, {stats['markdown_count']} MD")

    def _sanitize_filename(self, name: str) -> str:
        """Convert a string to a safe filename."""
        # Replace problematic characters
        safe = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        safe = safe.replace(":", "-").replace("*", "").replace("?", "")
        safe = safe.replace('"', "").replace("<", "").replace(">", "")
        safe = safe.replace("|", "-").replace(".", "_")
        # Limit length
        return safe[:100]

    def _write_csv(self, data: list[dict], filepath: str) -> None:
        """Write data to a CSV file."""
        if not data:
            # Write empty file with no headers
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                pass
            return

        fieldnames = list(data[0].keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(data)

    def _write_json(self, data: list[dict] | dict, filepath: str) -> None:
        """Write data to a JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, cls=JSONEncoderExtended)

    def _create_tar_gz(self, source_dir: str, output_path: str) -> None:
        """Create a tar.gz archive from a directory."""
        logger.info(f"Creating tar.gz archive: {output_path}")

        with tarfile.open(output_path, "w:gz") as tar:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    tar.add(file_path, arcname=arcname)

        # Log file size
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Archive created: {size_mb:.2f} MB")