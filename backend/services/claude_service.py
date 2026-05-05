import asyncio
import json
import logging
import os
import re
import threading
import anthropic
from anthropic import APIStatusError, APITimeoutError, APIConnectionError
from utils.test_mode import get_test_pdf_text, generate_test_mock_response, is_test_mode

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are LegalClear, an expert legal document analyser.

Your role is to translate legal documents into plain English and identify risks
for the person being asked to agree to the document (referred to as "the user").

CRITICAL STREAMING INSTRUCTION:
You must output your analysis section by section.
For each section you find, output a complete JSON object on its own line,
wrapped in <section> tags like this:

<section>{"section_id": 1, "title": "...", "category": "...", "original_excerpt": "...", "plain_english": "...", "risk_flags": [{"severity": "HIGH", "title": "short flag title", "explanation": "what this risk means for the user"}]}</section>

Each risk_flag MUST have exactly these three fields: severity (HIGH|MEDIUM|NOTE), title (short label), explanation (1-2 sentences).

Before the first section, output document metadata wrapped in <meta> tags:
<meta>{"document_name": "...", "parties": [...], "summary": "..."}</meta>

After ALL sections, output a final summary wrapped in <final> tags:
<final>{"overall_risk_level": "LOW|MEDIUM|HIGH", "overall_risk_explanation": "...", "total_clauses_reviewed": 0, "high_risk_count": 0, "medium_risk_count": 0, "note_count": 0}</final>

RULES:
1. Read the ENTIRE document before outputting anything
2. Output <meta> first, then each <section>, then <final>
3. Every section JSON must be complete and valid — never break a section across lines
4. Identify all parties and define them clearly in the meta block
5. Categorise every clause: Your Rights | Company Rights | Your Obligations |
   Company Obligations | Termination | Liability & Disputes | Data & Privacy |
   Payment & Fees | Intellectual Property | Other
6. Risk flag severity: HIGH | MEDIUM | NOTE
7. Never soften language around genuinely harmful clauses
8. Always flag: arbitration, data selling, auto-renewal, unilateral modification,
   data selling, liability waivers, jurisdiction clauses
9. Cross-reference dependent clauses — never translate a clause in isolation if it depends
   on or is modified by another clause
10. Do not provide legal advice
11. Approach every document with the assumption it may contain unfair terms

OUTPUT BREVITY RULES — these are strict and must be followed exactly:
- verdict: EXACTLY 1 sentence, maximum 20 words. This is the single most important
  thing a user needs to know about this document. Make it direct and honest.
  Example: "This document gives the company broad rights over your data and heavily
  limits your ability to dispute charges."
- summary: EXACTLY 1 sentence, maximum 25 words. State what the document is and
  what it governs. No risk language here — just what the document covers.
- overall_risk_explanation: EXACTLY 1 sentence, maximum 20 words. State why the
  document received this risk level.
- plain_english (per section): Maximum 3 sentences. State what the clause does,
  who it affects, and what the practical implication is for the user. No padding.
- risk flag explanation: Maximum 15 words. Be direct. No padding or softening.
  Example: "Company can change prices at any time without your consent."

You must return your response ONLY as a valid JSON object — no preamble,
no explanation outside the JSON, no markdown code fences."""

USER_MESSAGE_TEMPLATE = """Analyse the following legal document and return a JSON object conforming to this exact schema:

{{
  "document_name": "string — name of the document as provided by the user",
  "verdict": "string — EXACTLY 1 sentence, max 20 words. The single most important thing the user needs to know about this document. Direct and honest.",
  "parties": [
    {{ "name": "string", "role": "string — e.g. user/customer/tenant/employee", "description": "string" }}
  ],
  "summary": "string — EXACTLY 1 sentence, maximum 25 words. State what the document is and what it governs. No risk language here — just what the document covers.",
  "sections": [
    {{
      "section_id": "integer",
      "title": "string — clear descriptive title for this clause or section",
      "category": "one of: Your Rights | Company Rights | Your Obligations | Company Obligations | Termination | Liability & Disputes | Data & Privacy | Payment & Fees | Intellectual Property | Other",
      "original_excerpt": "string — the key original legal text this section is based on (max 300 chars, truncate with ellipsis if longer)",
      "plain_english": "string — Maximum 3 sentences. State what the clause does, who it affects, and what the practical implication is for the user. No padding.",
      "risk_flags": [
        {{
          "severity": "HIGH | MEDIUM | NOTE",
          "title": "string — short flag title",
          "explanation": "string — Maximum 15 words. Be direct. No padding or softening."
        }}
      ]
    }}
  ],
  "overall_risk_level": "LOW | MEDIUM | HIGH — overall risk assessment of the entire document",
  "overall_risk_explanation": "string — EXACTLY 1 sentence, maximum 20 words. State why the document received this risk level.",
  "total_clauses_reviewed": "integer",
  "high_risk_count": "integer",
  "medium_risk_count": "integer",
  "note_count": "integer"
}}

Document Name: {document_name}

Legal Document Text:
{document_text}"""


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from Claude response, stripping any surrounding text."""
    text = text.strip()
    # Remove all markdown code fences (anywhere in the text)
    text = re.sub(r"```(?:json)?", "", text)
    text = text.strip()
    # Find the outermost JSON object — handles preamble/postamble text robustly
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


# Document/chunking helpers for large inputs
_MAX_OUTPUT_TOKENS = 8192   # model's actual output token ceiling
_SDK_TIMEOUT      = 1800.0  # 30 minutes — httpx connect/read timeout passed to SDK
_MAX_CHUNK_CHARS = 28000    # chunk size for splitting large documents
_CHUNK_OVERLAP_CHARS = 2000  # keep overlap to avoid clause cuts
_MAX_DOCUMENT_CHARS = 800000  # safeguard for extremely large uploads

_CLAUDE_API_ERROR_MESSAGE = (
    "Claude AI is unavailable right now. Please try again in a few moments."
)
_CLAUDE_PARSE_ERROR_MESSAGE = (
    "Claude AI returned an invalid response. Please try again or split the document into smaller sections."
)


def _choose_overall_risk_level(levels):
    if any(level == "HIGH" for level in levels):
        return "HIGH"
    if any(level == "MEDIUM" for level in levels):
        return "MEDIUM"
    return "LOW"


def _create_claude_client(api_key: str):
    sdk_timeout = anthropic.Timeout(
        timeout=_SDK_TIMEOUT,
        connect=30.0,
        read=_SDK_TIMEOUT,
        write=60.0,
        pool=10.0,
    )
    return anthropic.Anthropic(api_key=api_key, timeout=sdk_timeout)


def _chunk_document_text(text: str) -> list[str]:
    text = text.strip()
    if len(text) <= _MAX_CHUNK_CHARS:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + _MAX_CHUNK_CHARS)

        if end < len(text):
            boundary = text.rfind("\n", start, end)
            if boundary <= start:
                boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        if end == start:
            end = min(len(text), start + _MAX_CHUNK_CHARS)

        chunk = text[start:end].strip()
        if start > 0:
            overlap_start = max(0, start - _CHUNK_OVERLAP_CHARS)
            chunk = text[overlap_start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end

    return chunks


def _extract_parties_from_text(client, document_text: str) -> list[dict]:
    prompt = (
        "Extract all distinct parties named in this legal document text. "
        "Return only a valid JSON array with objects containing name, role, and description. "
        "If you cannot identify parties, return an empty array.\n\n"
        "Document text:\n"
        + document_text[:120000]
    )
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        result = _extract_json(response.content[0].text)
        if isinstance(result, list):
            return result
    except Exception:
        logger.warning("Unable to extract parties from document text", exc_info=True)
    return []


_CHUNK_MESSAGE_TEMPLATE = """\
This is part {chunk_id} of {total_chunks} from a larger legal document.
Analyse this text and return ONLY a valid JSON object — no preamble, no explanation, no markdown fences.

The JSON must have exactly this structure:
{{
  "summary": "string — 1-2 sentence overview of what this part covers",
  "sections": [
    {{
      "section_id": integer,
      "title": "string",
      "category": "one of: Your Rights | Company Rights | Your Obligations | Company Obligations | Termination | Liability & Disputes | Data & Privacy | Payment & Fees | Intellectual Property | Other",
      "original_excerpt": "string — key legal text this section is based on (max 300 chars)",
      "plain_english": "string — plain-English explanation of what this clause means for the user",
      "risk_flags": [
        {{
          "severity": "HIGH | MEDIUM | NOTE",
          "title": "string — short flag title",
          "explanation": "string — what this risk means for the user"
        }}
      ]
    }}
  ],
  "overall_risk_level": "LOW | MEDIUM | HIGH",
  "overall_risk_explanation": "string — 1-2 sentence explanation",
  "total_clauses_reviewed": integer,
  "high_risk_count": integer,
  "medium_risk_count": integer,
  "note_count": integer
}}

Document chunk:
{chunk_text}"""


def _analyze_chunk(client, chunk_text: str, chunk_id: int, total_chunks: int) -> dict:
    prompt = _CHUNK_MESSAGE_TEMPLATE.format(
        chunk_id=chunk_id,
        total_chunks=total_chunks,
        chunk_text=chunk_text,
    )
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=_MAX_OUTPUT_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    logger.info("Received chunk %s/%s analysis from Claude", chunk_id, total_chunks)
    return _extract_json(raw)


def _merge_chunk_results(chunk_results: list[dict], document_name: str) -> dict:
    all_sections = []
    summaries = []
    explanations = []

    for result in chunk_results:
        if not result:
            continue
        all_sections.extend(result.get("sections", []))
        summary = result.get("summary")
        if summary:
            summaries.append(summary.strip())
        explanation = result.get("overall_risk_explanation", "").strip()
        if explanation:
            explanations.append(explanation)

    # Renumber sections sequentially after merging
    for idx, sec in enumerate(all_sections, start=1):
        sec["section_id"] = idx

    # Derive risk counts and overall level from actual merged risk_flags — the
    # single authoritative source. Chunk-level counts from Claude are unreliable
    # (they may be approximate or inconsistent across chunks).
    high_risk = 0
    medium_risk = 0
    note_count = 0
    for sec in all_sections:
        for flag in sec.get("risk_flags", []):
            severity = (flag.get("severity") or "").upper()
            if severity == "HIGH":
                high_risk += 1
            elif severity == "MEDIUM":
                medium_risk += 1
            elif severity == "NOTE":
                note_count += 1

    if high_risk > 0:
        overall_risk_level = "HIGH"
    elif medium_risk > 0:
        overall_risk_level = "MEDIUM"
    else:
        overall_risk_level = "LOW"

    return {
        "document_name": document_name,
        "parties": [],
        "summary": (" ".join(summaries).strip()[:800] or "Document analysed in chunks."),
        "sections": all_sections,
        "overall_risk_level": overall_risk_level,
        "overall_risk_explanation": (
            explanations[0]
            if explanations
            else "This document contains multiple risk areas and was analysed in chunks."
        ),
        "total_clauses_reviewed": len(all_sections),
        "high_risk_count": high_risk,
        "medium_risk_count": medium_risk,
        "note_count": note_count,
    }


def translate_document(document_text: str, document_name: str) -> dict:
    # Check if test mode is enabled
    if is_test_mode():
        pdf_text = get_test_pdf_text()
        return generate_test_mock_response(document_name, pdf_text)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(_CLAUDE_API_ERROR_MESSAGE)

    if len(document_text) > _MAX_DOCUMENT_CHARS:
        logger.warning(
            "Input document exceeded max allowed length (%s chars), truncating to %s chars",
            len(document_text),
            _MAX_DOCUMENT_CHARS,
        )
        document_text = document_text[:_MAX_DOCUMENT_CHARS]

    client = _create_claude_client(api_key)

    if len(document_text) > _MAX_CHUNK_CHARS:
        logger.info(
            "Large document detected (%s chars); using chunked Claude pipeline",
            len(document_text),
        )
        chunks = _chunk_document_text(document_text)
        partial_results = []

        for idx, chunk in enumerate(chunks):
            try:
                partial_results.append(_analyze_chunk(client, chunk, idx + 1, len(chunks)))
            except (APITimeoutError, APIConnectionError, APIStatusError):
                raise RuntimeError(_CLAUDE_API_ERROR_MESSAGE)
            except Exception:
                logger.exception("Chunk analysis failed")
                raise RuntimeError(_CLAUDE_PARSE_ERROR_MESSAGE)

        parties = _extract_parties_from_text(client, document_text)
        merged = _merge_chunk_results(partial_results, document_name)
        merged["parties"] = parties
        return merged

    user_message = USER_MESSAGE_TEMPLATE.format(
        document_name=document_name,
        document_text=document_text,
    )

    def _call(extra_messages=None) -> str:
        """Single Claude call; extra_messages appended after the user turn."""
        messages = [{"role": "user", "content": user_message}]
        if extra_messages:
            messages.extend(extra_messages)
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=_MAX_OUTPUT_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text

    # --- Attempt 1: straightforward call ---
    raw = None
    try:
        raw = _call()
        return _extract_json(raw)
    except (json.JSONDecodeError, ValueError):
        pass
    except (APITimeoutError, APIConnectionError, APIStatusError):
        raise RuntimeError(_CLAUDE_API_ERROR_MESSAGE)
    except Exception:
        pass

    # --- Attempt 2: retry only for JSON parse failures or unexpected errors ---
    try:
        extra = [{
            "role": "assistant",
            "content": "I will now return only the valid JSON object with no additional text:",
        }]
        raw = _call(extra_messages=extra)
        return _extract_json(raw)
    except (APITimeoutError, APIConnectionError, APIStatusError):
        raise RuntimeError(_CLAUDE_API_ERROR_MESSAGE)
    except Exception:
        raise RuntimeError(_CLAUDE_PARSE_ERROR_MESSAGE)

async def translate_document_sse(document_text: str, document_name: str):
    """
    Async generator that yields Server-Sent Events (SSE).

    WHY SSE instead of a plain long-running HTTP request:
      Nginx (and AWS ALB) have a proxy_read_timeout of 60s by default.
      They kill ANY connection that produces no bytes for that long, regardless
      of what the backend is configured for.  SSE keeps the connection alive by
      sending a 'ping' event every 5 seconds while Claude is still thinking.
      The X-Accel-Buffering: no response header (set in the router) tells Nginx
      not to buffer the stream — without it, pings would be held in Nginx's
      buffer and never reach the client until the whole response is ready,
      defeating the purpose entirely.
    """
    if is_test_mode():
        pdf_text = get_test_pdf_text()
        result = generate_test_mock_response(document_name, pdf_text)
        yield f"data: {json.dumps({'type': 'status', 'message': 'Analysing your document...'})}\n\n"
        yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
        return

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield f"data: {json.dumps({'type': 'error', 'message': _CLAUDE_API_ERROR_MESSAGE})}\n\n"
        return

    sdk_timeout = anthropic.Timeout(
        timeout=_SDK_TIMEOUT,
        connect=30.0,
        read=_SDK_TIMEOUT,
        write=60.0,
        pool=10.0,
    )
    client = _create_claude_client(api_key)
    user_message = USER_MESSAGE_TEMPLATE.format(
        document_name=document_name,
        document_text=document_text,
    )

    # get_running_loop() is safe here because this is called from an async route
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _stream_in_thread():
        """Runs in a daemon thread to keep the async route responsive."""
        try:
            if len(document_text) > _MAX_CHUNK_CHARS:
                logger.info(
                    "Large-stream document detected (%s chars); using chunked pipeline",
                    len(document_text),
                )
                result = translate_document(document_text, document_name)
                loop.call_soon_threadsafe(queue.put_nowait, ("done", json.dumps(result)))
                return

            collected = ""
            with client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=_MAX_OUTPUT_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                for chunk in stream.text_stream:
                    collected += chunk
            loop.call_soon_threadsafe(queue.put_nowait, ("done", collected))
        except Exception:
            logger.exception("Claude streaming thread failed")
            loop.call_soon_threadsafe(queue.put_nowait, ("error", _CLAUDE_API_ERROR_MESSAGE))

    thread = threading.Thread(target=_stream_in_thread, daemon=True)
    thread.start()

    yield f"data: {json.dumps({'type': 'status', 'message': 'Analysing your document...'})}\n\n"

    # Drain queue; every 5 s of silence we send a ping to keep proxies alive
    while True:
        try:
            event_type, payload = await asyncio.wait_for(queue.get(), timeout=5.0)
        except asyncio.TimeoutError:
            # Heartbeat — keeps Nginx / AWS ALB from killing the connection
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            continue

        if event_type == "done":
            # Try to parse; if malformed, retry once with explicit instruction
            try:
                result = _extract_json(payload)
                yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
            except (json.JSONDecodeError, ValueError):
                try:
                    retry_msg = client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=_MAX_OUTPUT_TOKENS,
                        system=SYSTEM_PROMPT,
                        messages=[
                            {"role": "user", "content": user_message},
                            {
                                "role": "assistant",
                                "content": "I will now return only the valid JSON object with no additional text:",
                            },
                        ],
                    )
                    result = _extract_json(retry_msg.content[0].text)
                    yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
                except Exception:
                    yield f"data: {json.dumps({'type': 'error', 'message': _CLAUDE_PARSE_ERROR_MESSAGE})}\n\n"
            break

        elif event_type == "error":
            yield f"data: {json.dumps({'type': 'error', 'message': payload})}\n\n"
            break