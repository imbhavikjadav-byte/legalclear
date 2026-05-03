from fastapi import APIRouter, HTTPException
from models.request_models import SendEmailRequest
from services.pdf_service import generate_pdf
from services.email_service import send_email_with_pdf

router = APIRouter()


@router.post("/send-email")
async def send_email_endpoint(request: SendEmailRequest):
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

    try:
        send_email_with_pdf(
            recipient_email=str(request.email),
            translation_data=request.translation_data,
            pdf_bytes=pdf_bytes,
            document_name=request.document_name,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "code": "EMAIL_ERROR",
                "message": f"Failed to send email: {str(exc)}",
            },
        )

    return {"success": True, "message": "Email sent successfully."}
