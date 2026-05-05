import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import translate, pdf, email_router

app = FastAPI(title="LegalClear API", version="1.0.0")

_startup_time = datetime.now()
logging.basicConfig(level=logging.INFO)
logging.getLogger("legalclear").info(
    "LegalClear backend starting — %s",
    _startup_time.strftime("%Y-%m-%d %H:%M:%S"),
)


_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

origins = list({
    _frontend_url,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(translate.router, prefix="/api")
app.include_router(pdf.router, prefix="/api")
app.include_router(email_router.router, prefix="/api")


@app.get("/api/health")
async def health():
    from utils.test_mode import is_test_mode
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={
            "status": "ok",
            "service": "LegalClear API",
            "test_mode": is_test_mode(),
            "started_at": _startup_time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/api/test-mode")
async def test_mode_status():
    from utils.test_mode import is_test_mode
    return {"test_mode": is_test_mode()}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again.",
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8001)),
        timeout_keep_alive=1800,
        timeout_graceful_shutdown=1800,
    )