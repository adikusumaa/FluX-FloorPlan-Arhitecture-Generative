"""
environment_client.py
Klien untuk memanggil Environment Evaluation API (Qwen di Kaggle via ngrok).
"""
import os
import json
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

# Muat .env
load_dotenv()
EVALUATION_URL = os.getenv("EVALUATION_URL", "")
if not EVALUATION_URL:
    raise ValueError("[ENV CLIENT] EVALUATION_URL tidak ditemukan di .env")


def evaluate_plans(lat: float, lon: float, plans: List[Dict[str, Any]],
                   initial_scores: List[float] = None) -> Dict[str, Any]:
    """
    Kirim data denah dan lokasi ke API evaluasi lingkungan.

    Args:
        lat, lon: koordinat lokasi
        plans: list of plan dicts (format sama dengan contoh)
        initial_scores: list skor awal opsional

    Returns:
        Dict dengan key 'results' (list hasil evaluasi) dan 'environment_report' (dict info lingkungan)
    """
    if initial_scores is None:
        initial_scores = [0.5] * len(plans)

    payload = {
        "lat": lat,
        "lon": lon,
        "plans": plans,
        "initial_scores": initial_scores
    }

    endpoint = f"{EVALUATION_URL.rstrip('/')}/evaluate"
    try:
        print("[ENV CLIENT] Mengirim permintaan ke API...")
        resp = requests.post(endpoint, json=payload, timeout=600)  # timeout panjang untuk LLM
        resp.raise_for_status()
        print("[ENV CLIENT] Respons diterima dengan status 200")

        data = resp.json()

        # Tampilkan environment report di log jika ada
        env_report = data.get("environment_report")
        if env_report:
            city = env_report.get("city", "Unknown")
            country = env_report.get("country", "Unknown")
            temperature = env_report.get("temperature", "N/A")
            print(f"[ENV CLIENT] Environment report: {city}, {country} | Temp: {temperature}°C")
        else:
            print("[ENV CLIENT] Environment report tidak ditemukan dalam respons.")

        return data

    except requests.exceptions.RequestException as e:
        print(f"[ENV CLIENT] Gagal memanggil API: {e}")
        if 'resp' in locals() and resp is not None:
            print(f"[ENV CLIENT] Response text: {resp.text}")
        raise


if __name__ == "__main__":
    # Contoh penggunaan
    lat, lon = -6.2088, 106.8456  # Jakarta
    sample_plans = [
        {
            "name": "Plan A - North",
            "orientation": 0,
            "rooms": [
                {"name": "Bedroom", "center": [5, 5], "windows": [{"direction": 0}]},
                {"name": "Living Room", "center": [15, 15], "windows": [{"direction": 180}]}
            ]
        },
        {
            "name": "Plan B - East",
            "orientation": 90,
            "rooms": [
                {"name": "Bedroom", "center": [5, 5], "windows": [{"direction": 90}]},
                {"name": "Living Room", "center": [15, 15], "windows": [{"direction": 270}]}
            ]
        }
    ]

    print("[ENV CLIENT] Memulai evaluasi contoh...")
    result = evaluate_plans(lat, lon, sample_plans, initial_scores=[0.8, 0.7])
    print("[ENV CLIENT] Hasil evaluasi:")
    print(json.dumps(result, indent=2, ensure_ascii=False))