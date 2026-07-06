import json
import random
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=GROQ_API_KEY)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    user_text: str
    weights: list = [0.25, 0.25, 0.25, 0.25]

def extract_user_intent(user_text: str) -> dict:
    system_prompt = """
    Anda adalah asisten AI yang ahli dalam memahami kebutuhan desain arsitektur.
    Tugas Anda adalah membaca teks dari pengguna dan mengekstrak informasi spesifik tentang rumah yang mereka inginkan.

    Output harus berupa JSON dengan struktur ABSOLUT berikut:
    {
        "rooms": {
            "bedroom": 0,
            "bathroom": 0,
            "living_room": 0,
            "kitchen": 0,
            "dining_room": 0,
            "study_room": 0
        },
        "total_area": null,
        "style": "unknown",
        "special_needs": [],
        "user_profile": "unknown"
    }

    ATURAN PENGISIAN:
    1. rooms: Isi angka berdasarkan teks user. Jika tidak disebut, isi 0.
    2. total_area: Cari angka yang menyebut luas dalam m2. Jika tidak ada, isi null.
    3. style: Deteksi gaya (minimalis, klasik, modern, skandinavia, jepang).
    4. special_needs: Array string. Contoh: ["hemat energi", "akses mudah"].
    5. user_profile: Deteksi siapa pengguna (lansia, keluarga muda, single).

    PENTING: Hanya balas dengan JSON, tidak ada teks lain di luar JSON.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        raw_content = response.choices[0].message.content
        return json.loads(raw_content)
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return {
            "rooms": {"bedroom": 0, "bathroom": 0, "living_room": 0, "kitchen": 0, "dining_room": 0, "study_room": 0},
            "total_area": None,
            "style": "unknown",
            "special_needs": [],
            "user_profile": "unknown"
        }

def generate_mock_floorplans(requirements: dict, weights: list) -> list:
    styles = ["Modern", "Minimalis", "Klasik", "Skandinavia", "Jepang"]
    colors = ["#E8F5E9", "#FFF3E0", "#E3F2FD", "#FCE4EC", "#F3E5F5"]
    results = []
    
    total_area = requirements.get("total_area")
    if total_area is None:
        total_area = 120
    
    for i in range(5):
        s1 = round(random.uniform(0.6, 0.95), 2)
        s2 = round(random.uniform(0.5, 0.90), 2)
        s3 = round(random.uniform(0.7, 0.98), 2)
        s4 = round(random.uniform(0.5, 0.88), 2)
        composite = round(weights[0]*s1 + weights[1]*s2 + weights[2]*s3 + weights[3]*s4, 3)
        results.append({
            "id": f"plan_{i+1:03d}",
            "image_url": f"https://placehold.co/400x300/{colors[i]}/333333?text=Denah+{i+1}",
            "scores": {
                "spatial_openness": s1,
                "circulation_efficiency": s2,
                "layout_rationality": s3,
                "adaptability": s4,
                "composite": composite
            },
            "energy": {
                "EUI": random.randint(90, 130),
                "fire_safety_status": "OK" if random.random() > 0.2 else "Needs Review",
                "total_area": total_area + random.randint(-5, 5)
            },
            "style": random.choice(styles),
            "rank": i+1
        })
    results.sort(key=lambda x: x["scores"]["composite"], reverse=True)
    return results

@app.post("/generate")
async def generate_floorplans(request: GenerateRequest):
    try:
        logger.info(f"Generate request received: {request.user_text[:50]}...")
        requirements = extract_user_intent(request.user_text)
        logger.info(f"Requirements extracted:\n{json.dumps(requirements, indent=2)}")
        mock_results = generate_mock_floorplans(requirements, request.weights)
        return {
            "status": "success",
            "data": mock_results,
            "parsed_data": requirements
        }
    except Exception as e:
        logger.error(f"Generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "FluX! Parser API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)