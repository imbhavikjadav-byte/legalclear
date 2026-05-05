import io
from fastapi import UploadFile, HTTPException

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


async def extract_text_from_file(file: UploadFile) -> str:
    filename = file.filename or ""

    # 1. File extension validation (case-insensitive)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("txt", "pdf", "docx"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": "This file type is not supported. Please upload a .txt, .pdf, or .docx file only.",
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

    # 2. File signature validation
    if ext == "pdf" and not raw_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "INVALID_FILE_SIGNATURE",
                "message": "The file you uploaded doesn't appear to be a valid PDF. Please upload a genuine .pdf file or paste the text directly.",
            },
        )
    if ext == "docx" and not raw_bytes.startswith(b"PK"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "INVALID_FILE_SIGNATURE",
                "message": "The file you uploaded doesn't appear to be a valid Word document. Please upload a genuine .docx file or paste the text directly.",
            },
        )
    if ext == "txt" and b"\x00" in raw_bytes[:512]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "INVALID_FILE_SIGNATURE",
                "message": "The file you uploaded doesn't appear to be a valid text document. Please upload a genuine .txt file or paste the text directly.",
            },
        )

    # 3. Extract text — per-type error messages on failure
    try:
        if ext == "txt":
            extracted = raw_bytes.decode("utf-8", errors="replace")

        elif ext == "pdf":
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            extracted = "\n".join(text_parts).strip()

        elif ext == "docx":
            import docx
            doc = docx.Document(io.BytesIO(raw_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            extracted = "\n".join(paragraphs).strip()

    except HTTPException:
        raise
    except Exception:
        if ext == "txt":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "code": "FILE_EXTRACTION_ERROR",
                    "message": "We couldn't read this text file. It may be corrupted or in an unsupported encoding. Please try pasting the text directly.",
                },
            )
        elif ext == "pdf":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "code": "FILE_EXTRACTION_ERROR",
                    "message": "We couldn't extract text from this PDF. It may be a scanned document where pages are saved as images rather than text. Please try: (1) copying and pasting the text directly, or (2) using a PDF with a text layer.",
                },
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "code": "FILE_EXTRACTION_ERROR",
                    "message": "We couldn't extract text from this Word document. The file may be corrupted or password protected. Please try pasting the text directly.",
                },
            )

    # 4. Empty content check
    if ext == "txt" and len(extracted.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "FILE_EXTRACTION_ERROR",
                "message": "This text file appears to be empty or contains too little text to analyse. Please check the file and try again.",
            },
        )
    if ext == "pdf" and len(extracted) < 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "FILE_EXTRACTION_ERROR",
                "message": "We couldn't extract text from this PDF. It may be a scanned document where pages are saved as images rather than text. Please try copying and pasting the text directly.",
            },
        )
    if ext == "docx" and len(extracted.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "FILE_EXTRACTION_ERROR",
                "message": "This Word document appears to be empty or contains too little text to analyse. Please check the file and try again.",
            },
        )

    return extracted
