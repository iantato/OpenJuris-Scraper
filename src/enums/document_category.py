from enum import Enum

class DocumentCategory(str, Enum):
    CONSTITUTION = "Constitution"
    STATUTE = "Statute"
    EXECUTIVE = "Executive"
    JURISPRUDENCE = "Jurisprudence"