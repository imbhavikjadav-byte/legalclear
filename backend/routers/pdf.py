from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from models.request_models import GeneratePdfRequest
from services.pdf_service import generate_pdf
from utils.validators import sanitise_filename
from datetime import datetime, timezone

router = APIRouter()


@router.post("/generate-pdf")
async def generate_pdf_endpoint(request: GeneratePdfRequest):
    try:
        pdf_bytes = generate_pdf(
            request.translation_data,
            request.document_name,
            original_filename=request.original_filename,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": True, "code": "PDF_ERROR", "message": f"PDF generation failed: {str(exc)}"},
        )

    safe_name = sanitise_filename(request.document_name)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"LegalClear-{safe_name}-{date_str}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
