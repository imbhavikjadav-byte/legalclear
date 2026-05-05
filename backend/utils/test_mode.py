import os
from pathlib import Path

import PyPDF2


def is_test_mode() -> bool:
    test_mode = os.getenv("TEST_MODE", "false").lower()
    return test_mode in ("true", "1", "yes")


def resolve_test_pdf_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    env_path = os.getenv("TEST_PDF_PATH", "test_assets/test-document.pdf")
    path = Path(env_path)
    if not path.is_absolute():
        path = root / path
    return path


def get_test_pdf_text() -> str | None:
    path = resolve_test_pdf_path()
    if not path.exists():
        return None

    try:
        with path.open("rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            pages = [page.extract_text() for page in reader.pages]
        text = "\n".join([page for page in pages if page]).strip()
        return text if text else None
    except Exception:
        return None


def _static_mock_response(document_name: str) -> dict:
    return {
        "document_name": document_name,
        "verdict": "This agreement heavily favors the company with broad termination rights and limited user protections.",
        "parties": [
            {
                "name": "User",
                "role": "customer",
                "description": "The individual subscribing to the service"
            },
            {
                "name": "LegalClear Inc.",
                "role": "service provider",
                "description": "The company providing the legal analysis platform"
            }
        ],
        "summary": "This is a software service agreement governing user access to an online legal analysis platform with subscription terms.",
        "sections": [
            {
                "section_id": 1,
                "title": "Payment Terms and Auto-Renewal",
                "category": "Payment & Fees",
                "original_excerpt": "The subscription fee shall automatically renew each month unless cancelled 30 days prior...",
                "plain_english": "Your subscription renews automatically every month. You must cancel at least 30 days before renewal to avoid being charged again.",
                "risk_flags": [
                    {
                        "severity": "MEDIUM",
                        "title": "Auto-renewal",
                        "explanation": "Subscription renews automatically without explicit consent."
                    }
                ]
            },
            {
                "section_id": 2,
                "title": "Data Collection and Usage",
                "category": "Data & Privacy",
                "original_excerpt": "We may collect, use, and share your personal information for service provision and marketing...",
                "plain_english": "The company can collect your personal data and use it for their business purposes, including sharing with third parties for marketing.",
                "risk_flags": [
                    {
                        "severity": "HIGH",
                        "title": "Data sharing",
                        "explanation": "Company can share your data with third parties for marketing."
                    }
                ]
            },
            {
                "section_id": 3,
                "title": "Termination Rights",
                "category": "Termination",
                "original_excerpt": "The company may terminate this agreement at any time for any reason...",
                "plain_english": "The company can end this agreement whenever they want, for any reason, without giving you much notice or explanation.",
                "risk_flags": [
                    {
                        "severity": "HIGH",
                        "title": "Unilateral termination",
                        "explanation": "Company can terminate agreement at any time without cause."
                    }
                ]
            },
            {
                "section_id": 4,
                "title": "Liability Limitations",
                "category": "Liability & Disputes",
                "original_excerpt": "The company's liability shall not exceed the amount paid in the past 12 months...",
                "plain_english": "If something goes wrong, the company only has to pay you back what you've paid them in the last year, even if their mistake caused you bigger losses.",
                "risk_flags": [
                    {
                        "severity": "MEDIUM",
                        "title": "Limited liability",
                        "explanation": "Company liability is capped at subscription payments."
                    }
                ]
            },
            {
                "section_id": 5,
                "title": "Arbitration Clause",
                "category": "Liability & Disputes",
                "original_excerpt": "Any disputes shall be resolved through binding arbitration in [company's location]...",
                "plain_english": "If there's a disagreement, you can't sue in court. Instead, you have to use private arbitration, which is usually faster but less favorable to consumers.",
                "risk_flags": [
                    {
                        "severity": "HIGH",
                        "title": "Arbitration required",
                        "explanation": "Disputes must go to arbitration instead of court."
                    },
                    {
                        "severity": "NOTE",
                        "title": "Jurisdiction",
                        "explanation": "Arbitration occurs in company's preferred location."
                    }
                ]
            }
        ],
        "overall_risk_level": "HIGH",
        "overall_risk_explanation": "Multiple high-risk clauses including data sharing, unilateral termination, and arbitration requirements.",
        "total_clauses_reviewed": 5,
        "high_risk_count": 3,
        "medium_risk_count": 2,
        "note_count": 1
    }


def _keywords_present(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _add_section(sections: list[dict], title: str, category: str, excerpt: str, plain_english: str, risk_flags: list[dict]):
    sections.append({
        "section_id": len(sections) + 1,
        "title": title,
        "category": category,
        "original_excerpt": excerpt,
        "plain_english": plain_english,
        "risk_flags": risk_flags,
    })


def _generate_keyword_mock_response(document_name: str, text: str) -> dict:
    sections: list[dict] = []
    if _keywords_present(text, ["auto-renew", "auto renew", "renewal", "renew automatically"]):
        _add_section(
            sections,
            "Payment Terms and Auto-Renewal",
            "Payment & Fees",
            "The subscription fee renews automatically unless you cancel before the next billing cycle...",
            "Your subscription renews automatically and you must cancel early to avoid another charge.",
            [{
                "severity": "MEDIUM",
                "title": "Auto-renewal",
                "explanation": "Subscription renews automatically unless cancelled."
            }],
        )

    if _keywords_present(text, ["data sharing", "personal data", "collect your data", "third party", "privacy policy"]):
        _add_section(
            sections,
            "Data Collection and Sharing",
            "Data & Privacy",
            "We may collect, use, and share your personal information with partners and service providers...",
            "The company can collect and share your personal data with partners without asking each time.",
            [{
                "severity": "HIGH",
                "title": "Data sharing",
                "explanation": "Your personal data may be shared with third parties."
            }],
        )

    if _keywords_present(text, ["terminate this agreement", "terminate at any time", "terminate for any reason", "termination"]):
        _add_section(
            sections,
            "Termination Rights",
            "Termination",
            "The company may terminate this agreement at any time for any reason without prior notice...",
            "The company can end the contract whenever they want, with limited notice or explanation.",
            [{
                "severity": "HIGH",
                "title": "Unilateral termination",
                "explanation": "Company can terminate the agreement without cause."
            }],
        )

    if _keywords_present(text, ["arbitration", "binding arbitration", "court", "litigation"]):
        _add_section(
            sections,
            "Dispute Resolution",
            "Liability & Disputes",
            "Disputes must be resolved through binding arbitration in the company’s chosen location...",
            "You must resolve disputes in arbitration rather than court, likely in the company's home jurisdiction.",
            [
                {
                    "severity": "HIGH",
                    "title": "Arbitration required",
                    "explanation": "Disputes must go to arbitration instead of court."
                },
                {
                    "severity": "NOTE",
                    "title": "Jurisdiction",
                    "explanation": "Dispute location is chosen by the company."
                }
            ],
        )

    if _keywords_present(text, ["liability", "liability cap", "limit liability", "damages"]):
        _add_section(
            sections,
            "Liability Cap",
            "Liability & Disputes",
            "The company’s liability is limited to a small amount or to fees paid in the prior year...",
            "If the company is at fault, your recovery may be capped at a much smaller amount than your actual loss.",
            [{
                "severity": "MEDIUM",
                "title": "Limited liability",
                "explanation": "Company liability is capped at a low amount."
            }],
        )

    if _keywords_present(text, ["intellectual property", "license", "proprietary"]):
        _add_section(
            sections,
            "Intellectual Property Rights",
            "Intellectual Property",
            "The company retains ownership of all intellectual property and licenses your contributions for its use...",
            "The company keeps ownership of the intellectual property and only grants you a limited license.",
            [{
                "severity": "NOTE",
                "title": "Company IP ownership",
                "explanation": "The company retains ownership of intellectual property."
            }],
        )

    if not sections:
        _add_section(
            sections,
            "Service Access and Fees",
            "Payment & Fees",
            "You agree to pay fees for access and renewals according to the terms of this service agreement...",
            "The agreement includes paid access, fees, and renewal terms that affect how long you can use the service.",
            [{
                "severity": "MEDIUM",
                "title": "Paid access",
                "explanation": "Your use of the service requires ongoing payments."
            }],
        )
        _add_section(
            sections,
            "Data and Privacy",
            "Data & Privacy",
            "The document allows the company to collect and use personal data as part of delivering the service...",
            "The company may collect and use your personal data as part of service delivery."
            , [{
                "severity": "HIGH",
                "title": "Data collection",
                "explanation": "Your personal data may be collected and used broadly."
            }],
        )

    high_count = sum(1 for section in sections for flag in section["risk_flags"] if flag["severity"] == "HIGH")
    medium_count = sum(1 for section in sections for flag in section["risk_flags"] if flag["severity"] == "MEDIUM")
    note_count = sum(1 for section in sections for flag in section["risk_flags"] if flag["severity"] == "NOTE")

    if high_count > 0:
        overall_risk_level = "HIGH"
        overall_risk_explanation = "Several clauses pose high risk for the user, including data sharing and arbitration."
    elif medium_count > 0:
        overall_risk_level = "MEDIUM"
        overall_risk_explanation = "The document has multiple concerning clauses that should be reviewed carefully."
    else:
        overall_risk_level = "LOW"
        overall_risk_explanation = "No major high-risk clauses were detected in the sampled document text."

    summary = (
        "This agreement governs access to an online service and how your data and fees are managed."
        if "service" in text
        else "This document sets terms for a business relationship and how fees, data, and disputes are handled."
    )

    return {
        "document_name": document_name,
        "verdict": "This agreement gives the company broad control over fees, data, and dispute resolution.",
        "parties": [
            {
                "name": "User",
                "role": "customer",
                "description": "The individual using the service"
            },
            {
                "name": "LegalClear Inc.",
                "role": "service provider",
                "description": "The company offering the platform"
            }
        ],
        "summary": summary,
        "sections": sections,
        "overall_risk_level": overall_risk_level,
        "overall_risk_explanation": overall_risk_explanation,
        "total_clauses_reviewed": len(sections),
        "high_risk_count": high_count,
        "medium_risk_count": medium_count,
        "note_count": note_count,
    }


def generate_test_mock_response(document_name: str, source_text: str | None = None) -> dict:
    if not source_text:
        return _static_mock_response(document_name)
    return _generate_keyword_mock_response(document_name, source_text.lower())
