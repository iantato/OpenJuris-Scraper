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
    )
}