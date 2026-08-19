# mcp/client/embedding_client.py
import requests
import os
from typing import List

KAGGLE_EMBEDDING_URL = os.getenv("KAGGLE_EMBEDDING_URL", "http://localhost:8001")

def embed_texts(texts: List[str], batch_size: int = 4) -> List[List[float]]:
    """
    Kirim request ke Kaggle untuk generate embeddings.
    """
    response = requests.post(
        f"{KAGGLE_EMBEDDING_URL}/embed",
        json={"texts": texts, "batch_size": batch_size},
        timeout=60  # timeout 60 detik
    )
    
    if response.status_code != 200:
        raise Exception(f"Embedding server error: {response.text}")
    
    data = response.json()
    return data["embeddings"]