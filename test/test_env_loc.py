"""
test/test_env_loc.py
Uji koneksi Environment Evaluation API.
"""
import os
import sys
import json

# Tentukan root project (folder yang berisi src, test, .env)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tambahkan root project dan src ke sys.path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from mcp.client.environment_client import evaluate_plans
from dotenv import load_dotenv

# Muat .env dari root project
load_dotenv(os.path.join(ROOT_DIR, ".env"))

EVALUATION_URL = os.getenv("EVALUATION_URL", "")
if not EVALUATION_URL:
    print("[TEST] EVALUATION_URL tidak ditemukan di .env")
    sys.exit(1)

print("[TEST] Memulai pengujian Environment Evaluation API")
print(f"[TEST] URL API: {EVALUATION_URL}")

# Koordinat contoh: Jakarta
lat, lon = -6.2088, 106.8456

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
    },
    {
        "name": "Plan C - South",
        "orientation": 180,
        "rooms": [
            {"name": "Bedroom", "center": [5, 5], "windows": [{"direction": 180}]},
            {"name": "Living Room", "center": [15, 15], "windows": [{"direction": 0}]}
        ]
    }
]

initial_scores = [0.8, 0.7, 0.9]

def main():
    print("[TEST] Mengirim data ke API...")
    try:
        result = evaluate_plans(lat, lon, sample_plans, initial_scores)
    except Exception as e:
        print(f"[TEST] Gagal memanggil API: {e}")
        sys.exit(1)

    print("[TEST] Respons diterima. Menampilkan ringkasan...")
    if "results" not in result:
        print("[TEST] Format respons tidak sesuai, harap periksa API.")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    ranked = result["results"]
    print(f"[TEST] Jumlah denah yang dievaluasi: {len(ranked)}")
    print("=" * 60)
    for idx, item in enumerate(ranked, 1):
        plan_name = item["plan"].get("name", f"Plan {idx}")
        combined = item.get("combined_score", 0.0)
        env_score = item.get("env_score", 0.0)
        initial = item.get("initial_score", 0.0)
        mitigation = item.get("mitigation", "")

        print(f"{idx}. {plan_name}")
        print(f"   Skor Awal      : {initial:.3f}")
        print(f"   Skor Lingkungan: {env_score:.3f}")
        print(f"   Skor Gabungan  : {combined:.3f}")
        print("   Mitigasi/Assessment:")
        print("   " + mitigation.replace("\n", "\n   ") if mitigation else "   Tidak ada")
        print("-" * 60)

    print("[TEST] Pengujian selesai.")

if __name__ == "__main__":
    main()