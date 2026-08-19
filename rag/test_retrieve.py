# rag/test_retrieve.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.vector_store import retrieve

if __name__ == "__main__":
    queries = [
        "Tabel 2 rata-rata jumlah edge untuk ruang tamu di dataset RPLAN",
        "Rumus perhitungan RFP-IoU",
        "Perbedaan antara RFP-GED dan GED biasa",
        "Empat tahap evaluasi RFP-A: jumlah ruang, graf, lokasi, geometri",
    ]
    
    for q in queries:
        print("\n" + "="*60)
        print(f"🔍 Query: {q}")
        print("="*60)
        try:
            results = retrieve(q, top_k=2)
            if not results:
                print("   ❌ Tidak ada hasil ditemukan.")
            else:
                for i, res in enumerate(results):
                    print(f"\n📄 Hasil {i+1} (300 karakter pertama):")
                    print(f"   {res[:300]}...")
        except Exception as e:
            print(f"   ❌ Error saat retrieve: {e}")