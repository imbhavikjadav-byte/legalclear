import json
import os
import re
import anthropic
from anthropic import APIStatusError, APITimeoutError, APIConnectionError

SYSTEM_PROMPT = """You are LegalClear, an expert legal document analyser. Your role is to translate legal documents into plain English that any adult can understand, and to clearly identify risks and obligations for the person who is being asked to agree to the document (referred to as "the user").

You must follow these rules without exception:

1. Read the ENTIRE document before producing any output.
2. Identify all parties and define them clearly at the start.
3. Categorise every clause or section you find.
4. Translate every clause into plain English — what it means in practice for the user.
5. Flag risks accurately using the severity system: HIGH RISK (red), MEDIUM RISK (amber), NOTE (blue).
6. Never soften the language around genuinely harmful clauses.
7. Flag all ambiguous language as a risk — vagueness in a legal document always favours the drafter.
8. Always flag: arbitration clauses, data selling/sharing, automatic renewal, unilateral modification rights, liability waivers, and jurisdiction clauses.
9. Cross-reference dependent clauses — never translate a clause in isolation if it depends on or is modified by another clause.
10. Do not provide legal advice. Do not tell the user whether to sign. Do translate and flag accurately.
11. Approach every document with the assumption it may contain unfair terms.
12. Be concise in every field: plain_english should be 2-4 sentences max; risk flag explanations 1-2 sentences max. Prioritise clarity over exhaustiveness.
13. Group closely related sub-clauses into a single section rather than splitting into many tiny sections. Aim for 8-20 sections total regardless of document length.

You must return your response ONLY as a valid JSON object — no preamble, no explanation outside the JSON, no markdown code fences. The JSON must conform exactly to the schema provided in the user message."""

USER_MESSAGE_TEMPLATE = """Analyse the following legal document and return a JSON object conforming to this exact schema:

{{
  "document_name": "string — name of the document as provided by the user",
  "parties": [
    {{ "name": "string", "role": "string — e.g. user/customer/tenant/employee", "description": "string" }}
  ],
  "summary": "string — 2-3 sentence plain-English overview of what this document is and what it does",
  "sections": [
    {{
      "section_id": "integer",
      "title": "string — clear descriptive title for this clause or section",
      "category": "one of: Your Rights | Company Rights | Your Obligations | Company Obligations | Termination | Liability & Disputes | Data & Privacy | Payment & Fees | Intellectual Property | Other",
      "original_excerpt": "string — the key original legal text this section is based on (max 300 chars, truncate with ellipsis if longer)",
      "plain_english": "string — full plain-English explanation of what this clause means in practice for the user",
      "risk_flags": [
        {{
          "severity": "HIGH | MEDIUM | NOTE",
          "title": "string — short flag title",
          "explanation": "string — what this risk means for the user specifically"
        }}
      ]
    }}
  ],
  "overall_risk_level": "LOW | MEDIUM | HIGH — overall risk assessment of the entire document",
  "overall_risk_explanation": "string — 1-2 sentence explanation of the overall risk rating",
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


# Claude Sonnet 4.5 hard limits
_MAX_OUTPUT_TOKENS = 8192   # model's actual output token ceiling
_SDK_TIMEOUT      = 1800.0  # 30 minutes — httpx connect/read timeout passed to SDK


def translate_document(document_text: str, document_name: str) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured.")

    # httpx.Timeout(total, connect, read, write, pool) — all set to 30 min
    sdk_timeout = anthropic.Timeout(
        timeout=_SDK_TIMEOUT,
        connect=30.0,
        read=_SDK_TIMEOUT,
        write=60.0,
        pool=10.0,
    )
    client = anthropic.Anthropic(api_key=api_key, timeout=sdk_timeout)

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
    first_exc = None
    try:
        raw = _call()
        return _extract_json(raw)
    except (json.JSONDecodeError, ValueError):
        # Claude responded but JSON was malformed — retry with stricter prompt
        first_exc = None  # not a hard failure; fall through to retry
    except (APITimeoutError, APIConnectionError, APIStatusError) as exc:
        # Hard API failure — surface immediately, no point retrying
        raise RuntimeError(
            f"Claude API error ({type(exc).__name__}): {exc}"
        ) from exc
    except Exception as exc:
        first_exc = exc  # unexpected; try once more

    # --- Attempt 2: retry only for JSON parse failures or unexpected errors ---
    try:
        extra = [{
            "role": "assistant",
            "content": "I will now return only the valid JSON object with no additional text:",
        }]
        raw = _call(extra_messages=extra)
        return _extract_json(raw)
    except (APITimeoutError, APIConnectionError, APIStatusError) as exc:
        raise RuntimeError(
            f"Claude API error on retry ({type(exc).__name__}): {exc}"
        ) from exc
    except Exception as exc:
        cause = first_exc or exc
        raise RuntimeError(
            "We were unable to process this document. "
            "Please try again or split the document into smaller sections."
        ) from cause
