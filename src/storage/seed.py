from loguru import logger

from storage.database import Database
from storage.repositories.source import SourceRepository
from models.source import Source
from enums.source_name import SourceName
from enums.source_type import SourceType


async def seed_sources(db: Database):
    """Seed initial sources into the database."""
    sources_data = [
        {
            "name": SourceName.LAWPHIL,
            "short_code": "LP",
            "base_url": "https://lawphil.net",
            "type": SourceType.PRIVATE_AGGREGATOR,
            "description": "The LawPhil Project - Philippine Laws and Jurisprudence",
        },
        # {
        #     "name": SourceName.SC_ELIBRARY,
        #     "short_code": "SC",
        #     "base_url": "https://elibrary.judiciary.gov.ph",
        #     "type": "official",
        #     "description": "Supreme Court E-Library",
        # },
        # {
        #     "name": SourceName.CHAN_ROBLES,
        #     "short_code": "CR",
        #     "base_url": "https://www.chanrobles.com",
        #     "type": "commercial",
        #     "description": "Chan Robles Virtual Law Library",
        # },
        # {
        #     "name": SourceName.OFFICIAL_GAZETTE,
        #     "short_code": "OG",
        #     "base_url": "https://www.officialgazette.gov.ph",
        #     "type": "official",
        #     "description": "Official Gazette of the Republic of the Philippines",
        # },
    ]

    async with db.session() as session:
        repo = SourceRepository(session)

        created = 0
        skipped = 0

        for source_data in sources_data:
            existing = await repo.get_by_name(source_data["name"])

            if existing:
                logger.debug(f"Source already exists: {source_data['name'].value}")
                skipped += 1
                continue

            source = Source(**source_data)
            await repo.create(source)
            created += 1
            logger.info(f"Created source: {source_data['name'].value}")

        await session.commit()

    logger.info(f"Seeding complete. Created: {created}, Skipped: {skipped}")


async def reset_sources(db: Database):
    """Reset all sources (dangerous - deletes all sources)."""
    async with db.session() as session:
        from sqlalchemy import delete

        statement = delete(Source)
        result = await session.execute(statement)
        await session.commit()

        logger.warning(f"Deleted {result.rowcount} sources")


async def seed_all(db: Database):
    """Seed all initial data."""
    logger.info("Starting database seeding...")
    await seed_sources(db)
    # Add other seed functions here as needed
    logger.info("Database seeding complete")