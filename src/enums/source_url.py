from enum import Enum

class SourceBaseURL(str, Enum):
    OFFICIAL_GAZETTE = "https://www.officialgazette.gov.ph/"
    SC_ELIBRARY = "https://elibrary.judiciary.gov.ph"
    LAWPHIL = "https://lawphil.net/"