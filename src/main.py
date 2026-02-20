# import os
# import asyncio

# from sqlmodel import SQLModel, create_engine
# from bs4 import BeautifulSoup

# from config import Settings

# # Import models to register them with SQLModel.metadata
# from models.source import Source                        # noqa: F401
# from models.subject import Subject                      # noqa: F401
# from models.document import Document                    # noqa: F401
# from models.scrape_job import ScrapeJob                 # noqa: F401
# from models.vector import DocumentVector                # noqa: F401
# from models.document_part import DocumentPart           # noqa: F401
# from models.subject_link import DocumentSubjectLink     # noqa: F401
# from models.document_relation import DocumentRelation   # noqa: F401

# from enums.source_name import SourceName
# from schemas.scraper_context import ScraperContext
# from scrapers.sc_elibrary.scraper import SCELibraryScraper
# from scrapers.lawphil.scraper import LawphilScraper

# from enums.document_type import DocumentType

# from storage.database import Database

# from transformers.markdown_transformer import MarkdownTransformer

# async def main():
#     settings = Settings()

#     db = Database(settings)
#     await db.create_tables()

#     ctx = ScraperContext(
#         db=db,
#         settings=settings,
#         target_document_types=[DocumentType.REPUBLIC_ACT]
#     )

#     # scraper = SCELibraryScraper(settings, ctx)
#     # await scraper.scrape_document("https://elibrary.judiciary.gov.ph/thebookshelf/showdocs/29/21733")

#     scraper = LawphilScraper(settings, ctx)
#     document = await scraper.scrape_document("https://lawphil.net/statutes/repacts/ra2025/ra_12313_2025.html", DocumentType.REPUBLIC_ACT)
#     # document = await scraper.scrape_document("https://lawphil.net/statutes/repacts/ra1946/ra_81_1946.html", DocumentType.REPUBLIC_ACT)
#     # document = await scraper.scrape_document("https://lawphil.net/statutes/repacts/ra1946/ra_1_1946.html", DocumentType.REPUBLIC_ACT)

#     print(document.content_markdown)

#     # final = 0
#     # async for document in scraper.run():
#     #     if final == 20:
#     #         break

#     #     transformer = MarkdownTransformer()
#     #     markdown = transformer.transform(document)

#     #     os.makedirs("output", exist_ok=True)
#     #     output_path = f"output/{document.canonical_citation.replace(' ', '_')}.md"
#     #     transformer.save_to_file(document, output_path)
#     #     print(f"Saved to: {output_path}")

#     #     final += 1

#     # if document:
#     #     print(f"Scraped: {document.canonical_citation}")
#     #     print(f"Title: {document.title}")
#     #     print(f"Parts: {len(document.parts)}")

#     #     transformer = MarkdownTransformer()
#     #     markdown = transformer.transform(document)

#     #     # Save to file
#     #     os.makedirs("output", exist_ok=True)
#     #     output_path = f"output/{document.canonical_citation.replace(' ', '_')}.md"
#     #     transformer.save_to_file(document, output_path)
#     #     print(f"Saved to: {output_path}")

#     #     # Print preview
#     #     print("\n--- Markdown Preview (first 500 chars) ---")
#     #     print(markdown[:500])

#     await db.close()
#     await scraper.close()

# if __name__ == "__main__":
#     asyncio.run(main())

import uvicorn

from api.api import app

if __name__ == "__main__":
    uvicorn.run(
        "api.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )