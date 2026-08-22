from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from api.routes import router
from core.config import setup_cors, settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FluX! AI Backend",
    description="API untuk generate floor plan dengan kecerdasan buatan",
    version="1.0.0",
)

# Setup CORS
setup_cors(app)

# Include router
app.include_router(router)

# ---------- Exception handler untuk validasi ----------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Menangani error validasi Pydantic dan mengembalikan detail yang jelas ke frontend.
    """
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body,
            "message": "Invalid request parameters",
        },
    )

# ---------- Root & Health ----------
@app.get("/")
async def root():
    return {"message": "FluX! AI Backend is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}