import json
import os
import logging
from pinecone import Pinecone
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Konfigurasi
PINE_API_KEY = os.getenv("PINE_API_KEY")
PINE_INDEX_NAME = os.getenv("PINE_INDEX_NAME")
KNOWLEDGE_PATH = r"D:\Academic-Project\Portofolio GENAI Architecture\RAG\International_Residential_Code.json"

if not PINE_API_KEY or not PINE_INDEX_NAME:
    raise ValueError("Pastikan PINE_API_KEY dan PINE_INDEX_NAME di-set di file .env")

# Inisialisasi Klien Pinecone
pc = Pinecone(api_key=PINE_API_KEY)
index = pc.Index(PINE_INDEX_NAME)

def ingest_data():
    try:
        # 1. Cek isi indeks sebelum menghapus untuk menghindari 404
        stats = index.describe_index_stats()
        if stats['total_vector_count'] > 0:
            logger.info(f"Ditemukan {stats['total_vector_count']} vektor lama, menghapus...")
            index.delete(delete_all=True)
        else:
            logger.info("Indeks masih kosong, melanjutkan proses.")
        
        # 2. Membaca file JSON
        if not os.path.exists(KNOWLEDGE_PATH):
            logger.error(f"File tidak ditemukan di: {KNOWLEDGE_PATH}")
            return

        with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Memulai proses embedding untuk {len(data)} entri...")

        # 3. Proses Embedding dan Upsert
        vectors_to_upsert = []
        for item in data:
            # String deskriptif untuk embedding (Knowledge Base)
            text_to_embed = (
                f"Komponen: {item.get('komponen', 'N/A')}. "
                f"Parameter: {item.get('parameter', 'N/A')}. "
                f"Nilai: {item.get('nilai_numerik', 'N/A')} {item.get('satuan', '')}. "
                f"Sumber: {item.get('sumber', 'IRC Standard')}"
            )
            
            # Generate Embedding menggunakan Pinecone Inference
            embedding_response = pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[text_to_embed],
                parameters={"input_type": "passage"}
            )
            vector = embedding_response[0].values
            
            # Persiapan data
            vectors_to_upsert.append({
                "id": str(item['id']),
                "values": vector,
                "metadata": {
                    "text": text_to_embed,
                    "source": item['sumber'],
                    "kategori": "residensial"
                }
            })
        
        # 4. Upsert batch ke Pinecone
        if vectors_to_upsert:
            index.upsert(vectors=vectors_to_upsert)
            logger.info(f"Sukses! {len(vectors_to_upsert)} data berhasil di-upload ke {PINE_INDEX_NAME}.")
        else:
            logger.warning("Data JSON kosong atau tidak ada entri untuk di-upload.")

    except Exception as e:
        logger.error(f"Terjadi kesalahan fatal saat ingest data: {e}")

if __name__ == "__main__":
    ingest_data()