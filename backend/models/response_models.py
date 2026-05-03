from pydantic import BaseModel
from typing import List, Optional


class RiskFlag(BaseModel):
    severity: str  # HIGH | MEDIUM | NOTE
    title: str
    explanation: str


class Section(BaseModel):
    section_id: int
    title: str
    category: str
    original_excerpt: str
    plain_english: str
    risk_flags: List[RiskFlag] = []


class Party(BaseModel):
    name: str
    role: str
    description: str


class TranslationResponse(BaseModel):
    document_name: str
    parties: List[Party] = []
    summary: str
    sections: List[Section] = []
    overall_risk_level: str  # LOW | MEDIUM | HIGH
    overall_risk_explanation: str
    total_clauses_reviewed: int
    high_risk_count: int
    medium_risk_count: int
    note_count: int


class ErrorResponse(BaseModel):
    error: bool = True
    code: str
    message: str
