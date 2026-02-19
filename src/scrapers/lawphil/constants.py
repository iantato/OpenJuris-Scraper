from enums.document_type import DocumentType

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