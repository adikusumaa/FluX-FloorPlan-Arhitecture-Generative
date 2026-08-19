# rag/vector_store.py
import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from src.mcp.client.embedding_client import embed_texts

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "flux-rag-index")
CHUNK_STORE_PATH = os.path.join(os.path.dirname(__file__), "chunk_store.json")

# Global store untuk teks chunk
CHUNK_STORE: Dict[str, str] = {}

def load_chunk_store():
    global CHUNK_STORE
    if os.path.exists(CHUNK_STORE_PATH):
        with open(CHUNK_STORE_PATH, 'r', encoding='utf-8') as f:
            CHUNK_STORE = json.load(f)
        print(f"✅ Memuat {len(CHUNK_STORE)} chunk dari {CHUNK_STORE_PATH}")

def save_chunk_store():
    with open(CHUNK_STORE_PATH, 'w', encoding='utf-8') as f:
        json.dump(CHUNK_STORE, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(CHUNK_STORE)} chunk teks disimpan ke {CHUNK_STORE_PATH}")

def init_pinecone():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"📦 Index '{INDEX_NAME}' belum ada, membuat baru...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=1024,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
        print(f"✅ Index '{INDEX_NAME}' berhasil dibuat.")
    else:
        print(f"✅ Index '{INDEX_NAME}' sudah ada.")
    return pc.Index(INDEX_NAME)

def upsert_documents(chunks: List[str]):
    global CHUNK_STORE
    index = init_pinecone()
    
    print(f"📤 Menggenerate embedding untuk {len(chunks)} chunks...")
    embeddings = embed_texts(chunks, batch_size=4)
    
    vectors = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        vector_id = f"chunk_{i}"
        CHUNK_STORE[vector_id] = chunk
        vectors.append({
            "id": vector_id,
            "values": emb,
            "metadata": {"chunk_id": vector_id}
        })
    
    # Simpan chunk store ke file
    save_chunk_store()
    
    for i in range(0, len(vectors), 100):
        batch = vectors[i:i+100]
        index.upsert(vectors=batch)
        print(f"   ✅ Upload {len(batch)} vektor (total {i+len(batch)})")
    
    print(f"✅ Selesai! Total {len(vectors)} chunks berhasil diupload ke Pinecone.")

def retrieve(query: str, top_k: int = 5) -> List[str]:
    global CHUNK_STORE
    # Pastikan chunk store termuat
    if not CHUNK_STORE:
        load_chunk_store()
    
    index = init_pinecone()
    
    print(f"🔍 Meng-embed query: '{query[:50]}...'")
    query_embedding = embed_texts([query])[0]
    
    result = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    texts = []
    for match in result['matches']:
        chunk_id = match['metadata'].get('chunk_id')
        if chunk_id and chunk_id in CHUNK_STORE:
            texts.append(CHUNK_STORE[chunk_id])
        else:
            texts.append(f"[Teks tidak ditemukan untuk {chunk_id}]")
    
    return texts