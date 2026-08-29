import os
import sys
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from src.agents.crew.crew_runner import generate_crew_summary

# Data dummy
dummy_candidates = [
    {
        "rank": 1,
        "id": "abc123",
        "scores": {"composite": 71.70, "env_score": 0.873},
        "orientation": 124.0,
        "location": {"lat": -6.2, "lng": 106.8},
        "suggestions": {"environment": "Assessment: denah ini baik, tapi perlu perbaikan ventilasi."}
    },
    {
        "rank": 2,
        "id": "def456",
        "scores": {"composite": 70.30, "env_score": 0.827},
        "orientation": 90.0,
        "location": {"lat": -6.2, "lng": 106.8},
        "suggestions": {"environment": "Assessment: perlu optimalisasi pencahayaan."}
    }
]

summary = generate_crew_summary(
    top_candidates=dummy_candidates,
    user_text="Saya ingin rumah dengan 3 kamar tidur dan taman.",
    location={"lat": -6.2, "lng": 106.8}
)

print("=== HASIL RINGKASAN CREWAI ===")
print(summary)