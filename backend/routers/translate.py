import asyncio
import json
from functools import partial
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from models.request_models import TranslateRequest
from services.claude_service import translate_document, translate_document_sse
from services.stream_claude_service import stream_translation
from utils.file_extractor import extract_text_from_file

# These headers are essential for SSE through Nginx / AWS proxies:
#   X-Accel-Buffering: no  → tells Nginx NOT to buffer — without this, pings
#                            are held in Nginx's buffer and never reach the
#                            client, making the whole SSE approach pointless.
#   Cache-Control: no-cache → prevents any intermediate cache from holding chunks.
_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}

router = APIRouter()


async def _run_translate(text: str, name: str) -> dict:
    """Run the blocking Claude call in a thread pool so it never blocks the event loop.
    Without this, uvicorn kills the request as a hung async handler."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(translate_document, text, name))


@router.post("/translate")
async def translate(request: TranslateRequest):
    try:
        result = await _run_translate(request.document_text, request.document_name)
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

    try:
        result = await _run_translate(text, document_name)
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

# ── SSE endpoints — proxy-timeout-proof ──────────────────────────────────────
# These replace the plain POST endpoints for the frontend. The backend streams
# 'ping' events every 5 s so Nginx / AWS ALB never hit proxy_read_timeout.

@router.post("/translate-stream")
async def translate_stream(request: TranslateRequest):
    return StreamingResponse(
        translate_document_sse(request.document_text, request.document_name),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.post("/translate-file-stream")
async def translate_file_stream(
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

    return StreamingResponse(
        translate_document_sse(text, document_name),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )

# ── NEW STREAMING ENDPOINTS — Progressive Rendering ──────────────────────────
# These use the new streaming Claude service for real-time section delivery

@router.post("/translate-stream-new")
async def translate_stream_new(request: TranslateRequest, req: Request):
    async def event_generator():
        try:
            async for chunk in stream_translation(
                document_text=request.document_text,
                document_name=request.document_name
            ):
                if await req.is_disconnected():
                    break
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(exc)}})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.post("/translate-file-stream-new")
async def translate_file_stream_new(
    req: Request,
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

    async def event_generator():
        try:
            async for chunk in stream_translation(
                document_text=text,
                document_name=document_name
            ):
                if await req.is_disconnected():
                    break
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(exc)}})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )