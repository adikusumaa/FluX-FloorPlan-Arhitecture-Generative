# mcp/client/encoder_client.py
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

ENCODER_URL = os.getenv("ENCODER_URL")

def encode_text(user_text: str) -> dict:
    """
    Kirim teks natural ke encoder server (Kaggle) dan dapatkan JSON terstruktur.
    """
    if not ENCODER_URL:
        raise Exception("ENCODER_URL tidak ditemukan di .env")
    
    try:
        response = requests.post(
            f"{ENCODER_URL}/encode",
            json={"user_text": user_text},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "success":
            # Parse JSON string menjadi dict
            return json.loads(data["json_output"])
        else:
            raise Exception(f"Encoder error: {data}")
    except requests.exceptions.ConnectionError:
        raise Exception(f"Gagal terhubung ke encoder server di {ENCODER_URL}")
    except Exception as e:
        raise Exception(f"Error encoding: {e}")