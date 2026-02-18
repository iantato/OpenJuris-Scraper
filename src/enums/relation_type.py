from enum import Enum

class RelationType(str, Enum):
    # --- References ---
    CITES = "Cites"
    QUOTES = "Quotes"
    Distinguishes = "DISTINGUISHES"

    # --- Modifications ---
    AMENDS = "Amends"           # Change specific text
    REPEALS = "Repeals"         # Kills the target law entirely
    REINSTATES = "Reinstates"   # Brings a dead law back
    SUSPENDS = "Suspends"       # Temporarily stops effectively

    # --- Heirarchy ---
    IMPLEMENTS = "Implements"       # IRR Implements RA
    INTERPRETS = "Interprets"       # SC Decision interprets RA
    CONSTITUTIONAL_CHALLENGE = "Unconstitutional"   # Declares void