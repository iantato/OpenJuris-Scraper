from enum import Enum

class SourceName(str, Enum):
    OFFICIAL_GAZETTE = "Official Gazette of the Philippines"
    SUPREME_COURT = "The Supreme Court of the Philippines"
    SC_ELIBRARY = "Supreme Court E-Library"
    CHAN_ROBLES = "Chan Robles Virtual Law Library"
    LAWPHIL = "The Lawphil Project"