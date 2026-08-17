import json
import random
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from pinecone import Pinecone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINE_API_KEY = os.getenv("PINE_API_KEY")
PINE_INDEX_NAME = os.getenv("PINE_INDEX_NAME")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")
if not PINE_API_KEY:
    raise ValueError("PINE_API_KEY not found in environment variables")
if not PINE_INDEX_NAME:
    raise ValueError("PINE_INDEX_NAME not found in environment variables")

groq_client = Groq(api_key=GROQ_API_KEY)
pc = Pinecone(api_key=PINE_API_KEY)
pinecone_index = pc.Index(PINE_INDEX_NAME)

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
        response = groq_client.chat.completions.create(
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
        logger.error(f"Groq intent extraction error: {e}")
        return {
            "rooms": {"bedroom": 0, "bathroom": 0, "living_room": 0, "kitchen": 0, "dining_room": 0, "study_room": 0},
            "total_area": None,
            "style": "unknown",
            "special_needs": [],
            "user_profile": "unknown"
        }

def retrieve_knowledge(query: str, top_k: int = 5) -> list:
    try:
        embedding_response = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[query],
            parameters={"input_type": "query"}
        )
        query_embedding = embedding_response[0].values
        
        search_response = pinecone_index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        retrieved_contexts = []
        for match in search_response.matches:
            metadata = match.metadata if match.metadata else {}
            source_doc = metadata.get("source", metadata.get("file_name", "Metadata_Kosong.pdf"))
            retrieved_contexts.append({
                "text": metadata.get("text", ""),
                "source": source_doc,
                "score": match.score
            })
        return retrieved_contexts
    except Exception as e:
        logger.error(f"Pinecone retrieval error: {e}")
        return []

def extract_constraints(retrieved_contexts: list, original_query: str) -> list:
    if not retrieved_contexts:
        return []
        
    context_sections = []
    for ctx in retrieved_contexts:
        context_sections.append(f"SUMBER_ASLI: {ctx['source']}\nISI_HUKUM:\n{ctx['text']}")
    context_text = "\n\n---\n\n".join(context_sections)
    
    system_prompt = f"""
    Anda adalah analis regulasi arsitektur spasial.
    Tugas Anda mengekstrak batasan NUMERIK SPASIAL HANYA dari teks di bawah label 'Konteks Hukum'.
    
    ATURAN FILTERING ABSOLUT:
    1. HANYA ekstrak aturan hukum spasial dari 'Konteks Hukum'.
    2. JANGAN PERNAH membuat aturan dari teks 'Kebutuhan Pengguna'. Kebutuhan Pengguna BUKAN dokumen hukum.
    3. Untuk field "sumber_pdf", Anda DIWAJIBKAN melakukan COPY-PASTE secara persis teks yang berada di sebelah kanan tulisan "SUMBER_ASLI:". Dilarang mengubah nama atau merangkum nama dokumen.
    
    Konteks Hukum:
    {context_text}
    
    Kebutuhan Pengguna:
    {original_query}
    
    Output harus berupa JSON dengan struktur:
    {{
        "constraints": [
            {{
                "komponen": "string",
                "parameter": "string",
                "operator": "string",
                "nilai_numerik": float,
                "satuan": "string",
                "sumber_pdf": "string"
            }}
        ]
    }}
    
    PENTING: Hanya balas dengan JSON.
    """
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        raw_content = response.choices[0].message.content
        parsed = json.loads(raw_content)
        return parsed.get("constraints", [])
    except Exception as e:
        logger.error(f"Groq constraints extraction error: {e}")
        return []

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
        logger.info("Generate request received.")
        
        requirements = extract_user_intent(request.user_text)
        logger.info("Requirements extracted successfully.")
        
        spatial_query = f"standar luas minimum dimensi sirkulasi pencahayaan untuk kamar tidur {requirements['rooms']['bedroom']} ruang tamu {requirements['rooms']['living_room']} dapur {requirements['rooms']['kitchen']} ruang belajar {requirements['rooms']['study_room']} {' '.join(requirements['special_needs'])}"
        logger.info(f"Refined Spatial Query for RAG: {spatial_query}")
        
        retrieved_contexts = retrieve_knowledge(spatial_query, top_k=5)
        logger.info(f"Retrieved {len(retrieved_contexts)} contexts from Pinecone.")
        
        for idx, ctx in enumerate(retrieved_contexts):
            logger.info(f"--- RAW PINECONE CONTEXT {idx+1} ---\n{ctx['text']}\n-----------------------------")
        
        constraints = extract_constraints(retrieved_contexts, request.user_text)
        logger.info(f"Constraints extracted successfully: {len(constraints)} rules found.")
        logger.info(f"Constraints Data:\n{json.dumps(constraints, indent=2)}")
        
        mock_results = generate_mock_floorplans(requirements, request.weights)
        
        return {
            "status": "success",
            "data": mock_results,
            "parsed_data": requirements,
            "constraints": constraints
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