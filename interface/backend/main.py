# interface/backend/main.py
from fastapi import FastAPI
import logging
from api.routes import router
from core.config import setup_cors

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FluX! AI Backend",
    description="API untuk generate floor plan dengan AI",
    version="1.0.0"
)

# Setup CORS
setup_cors(app)

# Include router
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "FluX! AI Backend is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}