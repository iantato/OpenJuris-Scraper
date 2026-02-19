from enums.document_type import DocumentType

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec"
]

SC_ELIB_PATHS: dict[DocumentType, str] = {
    DocumentType.ACT: "/thebookshelf/28",
    DocumentType.BATAS_PAMBANSA: "/thebookshelf/25",
    DocumentType.COMMONWEALTH_ACT: "/thebookshelf/29",
    DocumentType.CONSTITUTION: "/thebookshelf/3",
    DocumentType.GENERAL_ORDER: "/thebookshelf/30",
    DocumentType.LETTER_OF_IMPLEMENTATION: "/thebookshelf/33",
    DocumentType.LETTER_OF_INSTRUCTION: "/thebookshelf/34",
    # DocumentType.PRESIDENTIAL_DECREE: "/thebookshelf/26",
    DocumentType.REPUBLIC_ACT: "/thebookshelf/2",
    DocumentType.RULES_OF_COURT: "/thebookshelf/11",

    # Both of them are in a singular page.
    DocumentType.DECISION: "/thebookshelf/1",
    DocumentType.RESOLUTION: "/thebookshelf/1",

    DocumentType.ADMINISTRATIVE_ORDER: "/thebookshelf/6",
    DocumentType.EXECUTIVE_ORDER: "/thebookshelf/5",
    DocumentType.MEMORANDUM_CIRCULAR: "/thebookshelf/8",
    DocumentType.MEMORANDUM_ORDER: "/thebookshelf/9",
    # DocumentType.PRESIDENTIAL_DECREE: "/thebookshelf/7",
}