# rag/test_embedding.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

KAGGLE_URL = "https://reshoot-levers-fraction.ngrok-free.dev"

def embed_texts(texts):
    response = requests.post(
        f"{KAGGLE_URL}/embed",
        json={"texts": texts, "batch_size": 4},
        timeout=60
    )
    return response.json()["embeddings"]

if __name__ == "__main__":
    result = embed_texts(["Rumah dengan 3 kamar tidur", "Ruang tamu yang luas"])
    print(f"✅ Jumlah embedding: {len(result)}")
    print(f"✅ Dimensi: {len(result[0])}")