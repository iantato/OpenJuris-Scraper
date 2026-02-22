from enums.document_type import DocumentType

from schemas.statute_pattern import StatutePattern

LAWPHIL_PATHS: dict[DocumentType, str] = {
    DocumentType.ACT: "/statutes/acts/acts.html",
    DocumentType.BATAS_PAMBANSA: "/statutes/bataspam/bataspam.html",
    DocumentType.COMMONWEALTH_ACT: "/statutes/comacts/comacts.html",

    DocumentType.GENERAL_ORDER: "/executive/genor/genor.html",
    DocumentType.PRESIDENTIAL_DECREE: "/statutes/presdecs/legis_pd.html",
    DocumentType.REPUBLIC_ACT: "/statutes/repacts/repacts.html",

    DocumentType.ADMINISTRATIVE_ORDER: "/executive/ao/ao.html",
    DocumentType.EXECUTIVE_ORDER: "/executive/execord/execord.html",
    DocumentType.MEMORANDUM_CIRCULAR: "/executive/mc/mc.html",
    DocumentType.MEMORANDUM_ORDER: "/executive/mo/mo.html",
}

STATUTE_PATTERNS: dict[DocumentType, StatutePattern] = {
    DocumentType.REPUBLIC_ACT: StatutePattern(
        document_type=DocumentType.REPUBLIC_ACT,
        display_name=DocumentType.REPUBLIC_ACT.value,
        abbreviation="R.A.",
        patterns=[
            r'\[?\s*(REPUBLIC\s+ACT\s+NO\.?\s*(\d+))\s*\]?',
            r'(Republic\s+Act\s+No\.?\s*(\d+))',
            r'(R\.?\s*A\.?\s*(?:No\.?)?\s*(\d+))',
        ],
        url_indicators=["repact", "ra_", "republic_act", "/ra/"],
        title_prefixes=["AN ACT"],
        date_fields=["approved", "effectivity"]
    ),

    DocumentType.PRESIDENTIAL_DECREE: StatutePattern(
        document_type=DocumentType.PRESIDENTIAL_DECREE,
        display_name=DocumentType.PRESIDENTIAL_DECREE.value,
        abbreviation="P.D.",
        patterns=[
            r'\[?\s*(PRESIDENTIAL\s+DECREE\s+NO\.?\s*(\d+))\s*\]?',
            r'(Presidential\s+Decree\s+No\.?\s*(\d+))',
            r'(P\.?\s*D\.?\s*(?:No\.?)?\s*(\d+))',
        ],
        url_indicators=['presdec', 'pd_', 'presidential_decree', '/pd/'],
        title_prefixes=['DECREEING', 'DECLARING', 'PROVIDING', 'ESTABLISHING', 'CREATING', 'ORDAINING'],
        date_fields=['promulgated', 'effectivity'],
    ),

    DocumentType.EXECUTIVE_ORDER: StatutePattern(
        statute_type=DocumentType.EXECUTIVE_ORDER,
        display_name="Executive Order",
        abbreviation="E.O.",
        patterns=[
            r'\[?\s*(EXECUTIVE\s+ORDER\s+NO\.?\s*(\d+))\s*\]?',
            r'(Executive\s+Order\s+No\.?\s*(\d+))',
            r'(E\.?\s*O\.?\s*(?:No\.?)?\s*(\d+))',
        ],
        url_indicators=['execord', 'eo_', 'executive_order', '/eo/'],
        title_prefixes=['DIRECTING', 'PROVIDING', 'CREATING', 'ESTABLISHING', 'REORGANIZING', 'ORDERING'],
        date_fields=['signed', 'effectivity'],
    ),

    DocumentType.BATAS_PAMBANSA: StatutePattern(
        statute_type=DocumentType.BATAS_PAMBANSA,
        display_name="Batas Pambansa",
        abbreviation="B.P.",
        patterns=[
            r'\[?\s*(BATAS\s+PAMBANSA\s+(?:BLG\.?|BILANG)?\s*(\d+))\s*\]?',
            r'(Batas\s+Pambansa\s+(?:Blg\.?|Bilang)?\s*(\d+))',
            r'(B\.?\s*P\.?\s*(?:Blg\.?|Bilang|No\.?)?\s*(\d+))',
        ],
        url_indicators=['batas', 'bp_', 'batas_pambansa', '/bp/'],
        title_prefixes=['AN ACT'],
        date_fields=['approved', 'effectivity'],
    ),

    DocumentType.COMMONWEALTH_ACT: StatutePattern(
        statute_type=DocumentType.COMMONWEALTH_ACT,
        display_name="Commonwealth Act",
        abbreviation="C.A.",
        patterns=[
            r'\[?\s*(COMMONWEALTH\s+ACT\s+NO\.?\s*(\d+))\s*\]?',
            r'(Commonwealth\s+Act\s+No\.?\s*(\d+))',
            r'(C\.?\s*A\.?\s*(?:No\.?)?\s*(\d+))',
        ],
        url_indicators=['comact', 'ca_', 'commonwealth_act', '/ca/'],
        title_prefixes=['AN ACT'],
        date_fields=['approved', 'effectivity'],
    ),

    DocumentType.ACT: StatutePattern(
        statute_type=DocumentType.ACT,
        display_name="Act",
        abbreviation="Act",
        patterns=[
            r'\[?\s*(ACT\s+NO\.?\s*(\d+))\s*\]?',
            r'(Act\s+No\.?\s*(\d+))',
            r'(Act\s+(\d+))',
        ],
        url_indicators=['/act/', 'act_', 'actno'],
        title_prefixes=['AN ACT'],
        date_fields=['enacted', 'effectivity'],
    ),

    DocumentType.PRESIDENTIAL_PROCLAMATION: StatutePattern(
        statute_type=DocumentType.PRESIDENTIAL_PROCLAMATION,
        display_name="Presidential Proclamation",
        abbreviation="Proc.",
        patterns=[
            r'\[?\s*((?:PRESIDENTIAL\s+)?PROCLAMATION\s+NO\.?\s*(\d+))\s*\]?',
            r'(Proclamation\s+No\.?\s*(\d+))',
            r'(Proc\.?\s*(?:No\.?)?\s*(\d+))',
        ],
        url_indicators=['proc', 'proclamation', '/proc/'],
        title_prefixes=['DECLARING', 'PROCLAIMING'],
        date_fields=['issued', 'effectivity'],
    ),

    DocumentType.ADMINISTRATIVE_ORDER: StatutePattern(
        statute_type=DocumentType.ADMINISTRATIVE_ORDER,
        display_name="Administrative Order",
        abbreviation="A.O.",
        patterns=[
            r'\[?\s*(ADMINISTRATIVE\s+ORDER\s+NO\.?\s*(\d+))\s*\]?',
            r'(Administrative\s+Order\s+No\.?\s*(\d+))',
            r'(A\.?\s*O\.?\s*(?:No\.?)?\s*(\d+))',
        ],
        url_indicators=['adminord', 'ao_', 'administrative_order', '/ao/'],
        title_prefixes=['DIRECTING', 'PRESCRIBING', 'PROVIDING'],
        date_fields=['issued', 'effectivity'],
    ),

    DocumentType.MEMORANDUM_ORDER: StatutePattern(
        statute_type=DocumentType.MEMORANDUM_ORDER,
        display_name="Memorandum Order",
        abbreviation="M.O.",
        patterns=[
            r'\[?\s*(MEMORANDUM\s+ORDER\s+NO\.?\s*(\d+))\s*\]?',
            r'(Memorandum\s+Order\s+No\.?\s*(\d+))',
            r'(M\.?\s*O\.?\s*(?:No\.?)?\s*(\d+))',
        ],
        url_indicators=['memord', 'mo_', 'memorandum_order', '/mo/'],
        title_prefixes=['DIRECTING', 'PROVIDING'],
        date_fields=['issued', 'effectivity'],
    ),

    DocumentType.LETTER_OF_INSTRUCTION: StatutePattern(
        statute_type=DocumentType.LETTER_OF_INSTRUCTION,
        display_name="Letter of Instruction",
        abbreviation="LOI",
        patterns=[
            r'\[?\s*(LETTER\s+OF\s+INSTRUCTION\s+NO\.?\s*(\d+))\s*\]?',
            r'(Letter\s+of\s+Instruction\s+No\.?\s*(\d+))',
            r'(LOI\s*(?:No\.?)?\s*(\d+))',
        ],
        url_indicators=['loi', 'letter_of_instruction'],
        title_prefixes=['DIRECTING', 'INSTRUCTING'],
        date_fields=['issued', 'effectivity'],
    ),
}