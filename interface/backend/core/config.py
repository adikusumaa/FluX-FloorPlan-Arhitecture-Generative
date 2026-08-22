import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

load_dotenv()

class Settings:
    def __init__(self):
        self.KAGGLE_EMBEDDING_URL = os.getenv("KAGGLE_EMBEDDING_URL", "http://localhost:8001")
        self.ENCODER_URL = os.getenv("ENCODER_URL", "http://localhost:8002")
        self.CHATHOUSE_URL = os.getenv("CHATHOUSE_URL", "http://localhost:8003")
        self.CHATHOUSE_ENDPOINT = os.getenv("CHATHOUSE_ENDPOINT", "/mcp/tools/generate_floorplans")
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
        self.PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
        self.PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "flux-rag-index")
        self.CHATHOUSE_FULL_URL = f"{self.CHATHOUSE_URL}{self.CHATHOUSE_ENDPOINT}"

        # CORS origins
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")

settings = Settings()

def setup_cors(app: FastAPI):
    """Konfigurasi CORS agar frontend (Vite) dapat mengakses backend."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )