from enum import Enum

class DocumentType(str, Enum):
    # --- Constitution ---
    CONSTITUTION = "Constitution"

    # --- Legislative Acts (Statutes) ---
    REPUBLIC_ACT = "Republic Act"                # 1946-Present
    BATAS_PAMBANSA = "Batas Pambansa"            # 1978-1985 (Marcos Parliament)
    COMMONWEALTH_ACT = "Commonwealth Act"        # 1935-1946
    ACT = "Act"                                  # 1900-1935 (Philippine Commission/Assembly)

    # --- Executive Issuances ---
    PRESIDENTIAL_DECREE = "Presidential Decree"
    EXECUTIVE_ORDER = "Executive Order"
    ADMINISTRATIVE_ORDER = "Administrative Order"
    MEMORANDUM_ORDER = "Memorandum Order"
    MEMORANDUM_CIRCULAR = "Memorandum Circular"
    PROCLAMATION = "Proclamation"
    GENERAL_ORDER = "General Order"
    SPECIAL_ORDER = "Special Order"
    LETTER_OF_IMPLEMENTATION = "Letter of Implementation"
    LETTER_OF_INSTRUCTION = "Letter of Instruction"

    # --- Jurisprudence ---
    DECISION = "Decision"
    RESOLUTION = "Resolution"

    # --- Court Issuances ---
    RULES_OF_COURT = "Rules of Court"