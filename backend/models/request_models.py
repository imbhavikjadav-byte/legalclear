from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class TranslateRequest(BaseModel):
    document_text: str
    document_name: str

    @field_validator("document_text")
    @classmethod
    def validate_document_text(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 100:
            raise ValueError("Document text must be at least 100 characters.")
        if len(v) > 50000:
            raise ValueError("Document text must not exceed 50,000 characters.")
        return v

    @field_validator("document_name")
    @classmethod
    def validate_document_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Document name is required.")
        if len(v) > 100:
            raise ValueError("Document name must be 100 characters or fewer.")
        return v


class GeneratePdfRequest(BaseModel):
    translation_data: dict
    document_name: str
    original_filename: Optional[str] = None


class SendEmailRequest(BaseModel):
    email: EmailStr
    translation_data: dict
    document_name: str
    original_filename: Optional[str] = None
