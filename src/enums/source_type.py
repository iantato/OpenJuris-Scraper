from enum import Enum

class SourceType(str, Enum):
    OFFICIAL_GAZETTE = "Official Gazette"
    GOVERNMENT_REPO = "Government Repo"     # SC E-Library, Senate.gov
    ACADEMIC = "Academic"                   # UP Law Center
    PRIVATE_AGGREGATOR = "Private"          # Lawphil