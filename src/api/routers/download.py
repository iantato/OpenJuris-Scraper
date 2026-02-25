from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
import io
import markdown
from weasyprint import HTML

router = APIRouter(prefix="/download", tags=["Download"])

@router.post("/pdf/")
async def download_pdf(
    markdown_text: str = Body(..., embed=True, description="Markdown content to convert")
):
    """Convert Markdown to PDF and return as download."""
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_text)

    # Convert HTML to PDF using WeasyPrint
    pdf_bytes = HTML(string=html_content).write_pdf()

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=document.pdf"}
    )