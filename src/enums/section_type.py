from enum import Enum

class SectionType(str, Enum):
    # Document structure
    PREAMBLE = "preamble"
    ENACTING_CLAUSE = "enacting_clause"
    TITLE = "title"

    # Statute sections
    ARTICLE = "article"
    SECTION = "section"
    PARAGRAPH = "paragraph"
    SUBSECTION = "subsection"

    # Case decision sections
    SYLLABUS = "syllabus"
    FACTS = "facts"
    ISSUES = "issues"
    RULING = "ruling"
    DISPOSITIVE = "dispositive"
    CONCURRING = "concurring"
    DISSENTING = "dissenting"

    # Generic
    BODY = "body"
    FOOTNOTE = "footnote"
    ANNEX = "annex"