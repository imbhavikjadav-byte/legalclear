import io
from fastapi import UploadFile, HTTPException


ALLOWED_TYPES = {
    "text/plain": "txt",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def extract_text_from_file(file: UploadFile) -> str:
    content_type = file.content_type or ""
    filename = file.filename or ""

    # Determine extension
    ext = ""
    if filename.endswith(".txt"):
        ext = "txt"
    elif filename.endswith(".pdf"):
        ext = "pdf"
    elif filename.endswith(".docx"):
        ext = "docx"
    elif content_type in ALLOWED_TYPES:
        ext = ALLOWED_TYPES[content_type]

    if not ext or ext not in ("txt", "pdf", "docx"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": "Only .txt, .pdf, and .docx files are supported.",
            },
        )

    raw_bytes = await file.read()

    if not raw_bytes:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "FILE_EXTRACTION_ERROR",
                "message": "Uploaded file is empty.",
            },
        )

    if len(raw_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "FILE_EXTRACTION_ERROR",
                "message": "File exceeds the 5 MB size limit.",
            },
        )

    try:
        if ext == "txt":
            return raw_bytes.decode("utf-8", errors="replace")

        elif ext == "pdf":
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            extracted = "\n".join(text_parts).strip()
            if len(extracted) < 100:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": True,
                        "code": "FILE_EXTRACTION_ERROR",
                        "message": "We couldn't extract text from this PDF. It may be a scanned document where pages are saved as images rather than text. Please try: (1) copying and pasting the text directly into the text box, or (2) using a PDF with a text layer.",
                    },
                )
            return extracted

        elif ext == "docx":
            import docx
            doc = docx.Document(io.BytesIO(raw_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            extracted = "\n".join(paragraphs).strip()
            if len(extracted) < 100:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": True,
                        "code": "FILE_EXTRACTION_ERROR",
                        "message": "We couldn't extract any text from this Word document. The file may be empty or corrupted. Please try copying and pasting the text directly into the text box.",
                    },
                )
            return extracted

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "FILE_EXTRACTION_ERROR",
                "message": "We could not extract text from this file. Please paste the document text manually.",
            },
        )
