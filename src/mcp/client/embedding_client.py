# mcp/client/embedding_client.py
import requests
import os
from typing import List
from dotenv import load_dotenv

# Load .env dari root proyek
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

KAGGLE_EMBEDDING_URL = os.getenv("KAGGLE_EMBEDDING_URL", "http://localhost:8001")

def embed_texts(texts: List[str], batch_size: int = 4) -> List[List[float]]:
    response = requests.post(
        f"{KAGGLE_EMBEDDING_URL}/embed",
        json={"texts": texts, "batch_size": batch_size},
        timeout=60
    )
    if response.status_code != 200:
        raise Exception(f"Embedding server error: {response.text}")
    data = response.json()
    return data["embeddings"]