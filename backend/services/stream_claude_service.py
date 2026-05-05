import asyncio
import json
import os
import re
from typing import AsyncGenerator
import anthropic
from anthropic import APIStatusError, APITimeoutError, APIConnectionError
from utils.test_mode import get_test_pdf_text, generate_test_mock_response, is_test_mode

_SDK_TIMEOUT = 1800.0
_CLAUDE_API_ERROR_MESSAGE = (
    "Claude AI is unavailable right now. Please try again in a few moments."
)


async def _mock_stream_response(document_name: str) -> AsyncGenerator[dict, None]:
    """Generate mock streaming response for testing."""
    mock_data = generate_test_mock_response(document_name, get_test_pdf_text())

    # Yield meta first
    yield {"type": "meta", "data": {
        "document_name": mock_data["document_name"],
        "verdict": mock_data["verdict"],
        "parties": mock_data["parties"],
        "summary": mock_data["summary"]
    }}

    # Yield heartbeat
    yield {"type": "heartbeat", "data": {}}

    # Yield sections with delays
    for section in mock_data["sections"]:
        await asyncio.sleep(1.5)  # Simulate processing time
        yield {"type": "section", "data": section}
        yield {"type": "heartbeat", "data": {}}

    # Yield final
    await asyncio.sleep(1.0)
    yield {"type": "final", "data": {
        "overall_risk_level": mock_data["overall_risk_level"],
        "overall_risk_explanation": mock_data["overall_risk_explanation"],
        "total_clauses_reviewed": mock_data["total_clauses_reviewed"],
        "high_risk_count": mock_data["high_risk_count"],
        "medium_risk_count": mock_data["medium_risk_count"],
        "note_count": mock_data["note_count"]
    }}


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
<meta>{"document_name": "...", "verdict": "...", "parties": [{"name": "Party Name", "role": "user|company|landlord|employee|etc", "description": "what this party is in the context of this document"}], "summary": "..."}</meta>

The parties array MUST be populated. Identify EVERY named party in the document (company, individual, organisation). Each party must have name, role and description.

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
   liability waivers, jurisdiction clauses
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

IMPORTANT: Do NOT output a plain JSON object. You MUST use the XML tag format:
<meta>...</meta> then <section>...</section> for each section then <final>...</final>.
No preamble, no explanation, no markdown code fences. Only XML-tagged JSON blocks."""


def _create_async_claude_client(api_key: str):
    return anthropic.AsyncAnthropic(
        api_key=api_key,
        timeout=anthropic.Timeout(
            timeout=_SDK_TIMEOUT,
            connect=30.0,
            read=_SDK_TIMEOUT,
            write=60.0,
            pool=10.0,
        ),
    )

async def stream_translation(
    document_text: str,
    document_name: str
) -> AsyncGenerator[dict, None]:

    # Check if test mode is enabled
    if is_test_mode():
        async for chunk in _mock_stream_response(document_name):
            yield chunk
        return

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield {"type": "error", "data": {"message": _CLAUDE_API_ERROR_MESSAGE}}
        return

    client = _create_async_claude_client(api_key)

    user_message = f"""Analyse the following legal document.

Document Name: {document_name}

Legal Document Text:
{document_text}

Remember: Output <meta> first, then each <section> as you complete it, then <final>.
Each tag must contain a single complete valid JSON object."""

    buffer = ""

    try:
        async with client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        ) as stream:
            async for text_chunk in stream.text_stream:
                buffer += text_chunk

                # Extract and yield complete <meta> blocks
                meta_match = re.search(r'<meta>(.*?)</meta>', buffer, re.DOTALL)
                if meta_match:
                    try:
                        meta_data = json.loads(meta_match.group(1).strip())
                        yield {"type": "meta", "data": meta_data}
                    except json.JSONDecodeError:
                        pass
                    finally:
                        buffer = buffer[meta_match.end():]

                # Extract and yield complete <section> blocks
                while True:
                    section_match = re.search(r'<section>(.*?)</section>', buffer, re.DOTALL)
                    if not section_match:
                        break
                    try:
                        section_data = json.loads(section_match.group(1).strip())
                        yield {"type": "section", "data": section_data}
                        buffer = buffer[section_match.end():]
                    except json.JSONDecodeError:
                        buffer = buffer[section_match.end():]

                # Send a heartbeat every chunk to keep connection alive
                yield {"type": "heartbeat", "data": {}}

        # After stream ends, extract <final> block
        final_match = re.search(r'<final>(.*?)</final>', buffer, re.DOTALL)
        if final_match:
            try:
                final_data = json.loads(final_match.group(1).strip())
                yield {"type": "final", "data": final_data}
            except json.JSONDecodeError:
                yield {
                    "type": "final",
                    "data": {
                        "overall_risk_level": "UNKNOWN",
                        "overall_risk_explanation": "Analysis complete.",
                        "total_clauses_reviewed": 0,
                        "high_risk_count": 0,
                        "medium_risk_count": 0,
                        "note_count": 0
                    }
                }

        yield {"type": "complete", "data": {}}

    except (APIStatusError, APITimeoutError, APIConnectionError) as e:
        yield {"type": "error", "data": {"message": _CLAUDE_API_ERROR_MESSAGE}}
    except Exception as e:
        yield {"type": "error", "data": {"message": str(e)}}