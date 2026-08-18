# interface/backend/core/config.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import os

def setup_cors(app: FastAPI):
    """Konfigurasi CORS agar frontend (Vite) dapat mengakses backend."""
    origins = [
        "http://localhost:5173",   # Vite default
        "http://localhost:3000",   # CRA (jika digunakan)
        "http://127.0.0.1:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Environment variables (bisa ditambah)
KAGGLE_MCP_URL = os.getenv("KAGGLE_MCP_URL", "http://localhost:8001")  # nanti diisi URL ngrok