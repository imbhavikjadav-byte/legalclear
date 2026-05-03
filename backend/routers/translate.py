from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from models.request_models import TranslateRequest
from services.claude_service import translate_document
from utils.file_extractor import extract_text_from_file

router = APIRouter()


@router.post("/translate")
async def translate(request: TranslateRequest):
    try:
        result = translate_document(request.document_text, request.document_name)
        return result
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": True, "code": "CLAUDE_ERROR", "message": str(exc)},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": True, "code": "PARSE_ERROR", "message": str(exc)},
        )


@router.post("/translate-file")
async def translate_file(
    file: UploadFile = File(...),
    document_name: str = Form(...),
):
    text = await extract_text_from_file(file)

    if len(text) < 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "VALIDATION_ERROR",
                "message": "Your document is too short. Please provide at least 100 characters.",
            },
        )
    if len(text) > 50000:
        text = text[:50000]

    try:
        result = translate_document(text, document_name)
        return result
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": True, "code": "CLAUDE_ERROR", "message": str(exc)},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": True, "code": "PARSE_ERROR", "message": str(exc)},
        )
