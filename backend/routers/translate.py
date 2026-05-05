import asyncio
import json
from functools import partial
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from models.request_models import TranslateRequest
from services.claude_service import translate_document, translate_document_sse
from services.stream_claude_service import stream_translation
from services.cache_service import generate_hash, get_cached_result, store_result
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
async def translate_stream_new(request: TranslateRequest, req: Request, background_tasks: BackgroundTasks):

    # Generate hash of submitted document
    document_hash = generate_hash(request.document_text)

    # Check cache for existing result
    cached_result = get_cached_result(document_hash)

    if cached_result is not None:
        # CACHE HIT — replay cached result through streaming interface
        async def cached_event_generator():
            # Send meta chunk
            meta_chunk = {
                "type": "meta",
                "data": {
                    "document_name": cached_result.get("document_name", ""),
                    "verdict": cached_result.get("verdict", ""),
                    "parties": cached_result.get("parties", []),
                    "summary": cached_result.get("summary", "")
                }
            }
            yield f"data: {json.dumps(meta_chunk)}\n\n"
            await asyncio.sleep(0.15)

            # Send each section with a short delay between them
            for section in cached_result.get("sections", []):
                section_chunk = {"type": "section", "data": section}
                yield f"data: {json.dumps(section_chunk)}\n\n"
                await asyncio.sleep(0.15)

            # Send final chunk
            final_chunk = {
                "type": "final",
                "data": {
                    "overall_risk_level": cached_result.get("overall_risk_level", ""),
                    "overall_risk_explanation": cached_result.get("overall_risk_explanation", ""),
                    "total_clauses_reviewed": cached_result.get("total_clauses_reviewed", 0),
                    "high_risk_count": cached_result.get("high_risk_count", 0),
                    "medium_risk_count": cached_result.get("medium_risk_count", 0),
                    "note_count": cached_result.get("note_count", 0)
                }
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            await asyncio.sleep(0.05)

            # Send cache indicator chunk — frontend uses this to show the badge
            cache_chunk = {"type": "cached", "data": {"is_cached": True}}
            yield f"data: {json.dumps(cache_chunk)}\n\n"

            # Send complete chunk
            yield f"data: {json.dumps({'type': 'complete', 'data': {}})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            cached_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            }
        )

    # CACHE MISS — call Claude API and store result
    assembled_result = {
        "document_name": request.document_name,
        "sections": []
    }

    async def live_event_generator():
        # Track client connection separately so we keep assembling even if
        # the client drops mid-stream — we still want to cache the result.
        client_connected = True

        try:
            async for chunk in stream_translation(
                document_text=request.document_text,
                document_name=request.document_name
            ):
                # Always assemble regardless of client state
                if chunk["type"] == "meta":
                    assembled_result.update(chunk["data"])
                elif chunk["type"] == "section":
                    assembled_result["sections"].append(chunk["data"])
                elif chunk["type"] == "final":
                    assembled_result.update(chunk["data"])
                    # Fallback store at final chunk — earlier than complete,
                    # guards against client disconnect or Nginx timeout cutting
                    # the connection before complete chunk is processed.
                    try:
                        store_result(
                            document_hash=document_hash,
                            document_name=request.document_name,
                            result=assembled_result
                        )
                    except Exception:
                        pass
                elif chunk["type"] == "complete":
                    # Primary store via background task — runs after the response
                    # is fully sent, independent of client connection state.
                    background_tasks.add_task(
                        store_result,
                        document_hash=document_hash,
                        document_name=request.document_name,
                        result=dict(assembled_result)
                    )

                # Only yield to client while still connected
                if client_connected:
                    if await req.is_disconnected():
                        client_connected = False
                    else:
                        yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as exc:
            if client_connected:
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(exc)}})}\n\n"
        finally:
            if client_connected:
                yield "data: [DONE]\n\n"

    return StreamingResponse(
        live_event_generator(),
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
    background_tasks: BackgroundTasks = None,
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

    # Generate hash of the extracted document text
    document_hash = generate_hash(text)

    # Check cache for existing result
    cached_result = get_cached_result(document_hash)

    if cached_result is not None:
        # CACHE HIT — replay cached result through streaming interface
        async def cached_event_generator():
            meta_chunk = {
                "type": "meta",
                "data": {
                    "document_name": cached_result.get("document_name", ""),
                    "verdict": cached_result.get("verdict", ""),
                    "parties": cached_result.get("parties", []),
                    "summary": cached_result.get("summary", "")
                }
            }
            yield f"data: {json.dumps(meta_chunk)}\n\n"
            await asyncio.sleep(0.15)

            for section in cached_result.get("sections", []):
                section_chunk = {"type": "section", "data": section}
                yield f"data: {json.dumps(section_chunk)}\n\n"
                await asyncio.sleep(0.15)

            final_chunk = {
                "type": "final",
                "data": {
                    "overall_risk_level": cached_result.get("overall_risk_level", ""),
                    "overall_risk_explanation": cached_result.get("overall_risk_explanation", ""),
                    "total_clauses_reviewed": cached_result.get("total_clauses_reviewed", 0),
                    "high_risk_count": cached_result.get("high_risk_count", 0),
                    "medium_risk_count": cached_result.get("medium_risk_count", 0),
                    "note_count": cached_result.get("note_count", 0)
                }
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            await asyncio.sleep(0.05)

            cache_chunk = {"type": "cached", "data": {"is_cached": True}}
            yield f"data: {json.dumps(cache_chunk)}\n\n"

            yield f"data: {json.dumps({'type': 'complete', 'data': {}})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            cached_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            }
        )

    # CACHE MISS — call Claude API and store result
    assembled_result = {
        "document_name": document_name,
        "sections": []
    }

    async def live_event_generator():
        client_connected = True

        try:
            async for chunk in stream_translation(
                document_text=text,
                document_name=document_name
            ):
                # Always assemble regardless of client state
                if chunk["type"] == "meta":
                    assembled_result.update(chunk["data"])
                elif chunk["type"] == "section":
                    assembled_result["sections"].append(chunk["data"])
                elif chunk["type"] == "final":
                    assembled_result.update(chunk["data"])
                    # Fallback store at final chunk — guards against disconnect
                    # or Nginx timeout before complete chunk is processed.
                    try:
                        store_result(
                            document_hash=document_hash,
                            document_name=document_name,
                            result=assembled_result
                        )
                    except Exception:
                        pass
                elif chunk["type"] == "complete":
                    # Primary store via background task — independent of connection.
                    if background_tasks is not None:
                        background_tasks.add_task(
                            store_result,
                            document_hash=document_hash,
                            document_name=document_name,
                            result=dict(assembled_result)
                        )

                # Only yield to client while still connected
                if client_connected:
                    if await req.is_disconnected():
                        client_connected = False
                    else:
                        yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as exc:
            if client_connected:
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(exc)}})}\n\n"
        finally:
            if client_connected:
                yield "data: [DONE]\n\n"

    return StreamingResponse(
        live_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )