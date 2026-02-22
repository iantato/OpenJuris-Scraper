from enum import Enum

class IssueType(str, Enum):
    TYPO = "Typo/Grammar"
    FORMATTING = "Formatting"
    FACTUAL_ERROR = "Factual Error"
    OUTDATED = "Outdated Info"