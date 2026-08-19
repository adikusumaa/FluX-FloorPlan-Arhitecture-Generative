# rag/ingest_pdf.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.chunker import extract_sections_from_pdf, section_based_chunking
from src.rag.vector_store import upsert_documents

PDF_PATH = "D:/Academic-Project/Portofolio GEN-AI Architecture/knowledge/evaluation matrikx/Comprehensive and Dedicated Metrics for Evaluating.pdf"

if __name__ == "__main__":
    print("📄 Membaca PDF dan mengekstrak section...")
    sections = extract_sections_from_pdf(PDF_PATH)
    
    print(f"📄 Ditemukan {len(sections)} section:")
    for title in list(sections.keys())[:5]:
        print(f"   - {title[:60]}...")
    
    # Gabungkan semua konten untuk melihat panjang total
    total_text = "\n".join(sections.values())
    print(f"📄 Panjang total teks: {len(total_text)} karakter")
    
    if len(total_text) < 1000:
        print("⚠️  Teks hasil ekstraksi sangat pendek. Mungkin PDF tidak terbaca dengan benar.")
    
    print("✂️ Memotong menjadi chunks berbasis section...")
    chunks = section_based_chunking(sections, chunk_size=512, overlap=50)
    print(f"✅ {len(chunks)} chunks berhasil dibuat")
    
    if chunks:
        print(f"📄 Contoh chunk pertama (200 karakter): {chunks[0][:200]}...")
    else:
        print("❌ Tidak ada chunk yang dihasilkan. Periksa ekstraksi PDF.")
        sys.exit(1)
    
    print("📤 Mengupload ke Pinecone...")
    upsert_documents(chunks)
    print("✅ Selesai!")