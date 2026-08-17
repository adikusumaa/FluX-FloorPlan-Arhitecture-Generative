# ===================================================================
# PROJECT: FluX! - Intelligent Generative Floor Plan System
# VERSION: 2.2
# STATUS: IN DEVELOPMENT
# LAST UPDATED: 2026-07-16
# VIBE CODING ORIENTED ARCHITECTURE
# ===================================================================

# TABLE OF CONTENTS
# ===================================================================
# 1. PROJECT OVERVIEW
# 2. SYSTEM ARCHITECTURE & DATA FLOW
# 3. PHASE 0: FOUNDATION & SETUP
# 4. PHASE 1: PARSER & RAG MODULE
# 5. PHASE 2: GENERATOR MODULE
# 6. PHASE 3: RFP-A EVALUATOR MODULE
# 7. PHASE 4: AI AGENT & ORCHESTRATION
# 8. PHASE 5: WEB APPLICATION
# 9. PHASE 6: TESTING & DEPLOYMENT
# 10. REFERENCE & CITATIONS
# 11. PROGRESS SUMMARY
# 12. RECENT UPDATES
# ===================================================================


# ===================================================================
# 1. PROJECT OVERVIEW
# ===================================================================

PROJECT NAME: FluX!
DESCRIPTION: Sistem AI yang menghasilkan denah rumah dari input teks natural language
             dengan validasi energi (GreenPlanner/PDE) dan spasial (RFP-A)

CORE FEATURES:
- Input user dalam bahasa natural
- Ekstraksi kebutuhan menggunakan LLM (Groq) - [x] SELESAI
- Retrieval regulasi dari Pinecone (RAG) - [x] INFRASTRUKTUR / INDEKS READY
- Generasi 100 denah kandidat (GreenPlanner / alternatif) - [ ] BELUM
- Validasi energi & fungsional (PDE) - [ ] BELUM
- Evaluasi spasial 4 dimensi (RFP-A) - [ ] BELUM
- Output 5 denah terbaik dengan skor & rekomendasi - [x] MOCK DATA

CURRENT STATUS: Backend + Frontend terhubung. Parser Groq & Vektor Database 
                Pinecone (2.843 records, llama-text-embed-v2) siap digunakan.
                Tahap penghubungan integrasi kode RAG di FastAPI.

TARGET: Production Ready

# ===================================================================


# ===================================================================
# 2. SYSTEM ARCHITECTURE & DATA FLOW
# ===================================================================

┌─────────────────────────────────────────────────────────────────┐
│                      USER INPUT (Teks Natural)                  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI - Local)                     │
│ 1. extract_user_intent() -> Menggunakan Groq API (JSON)        │
│ 2. retrieve_knowledge()  -> Query ke Pinecone Vector DB        │
│ 3. extract_constraints() -> Sinkronisasi Konteks Hukum + Groq  │
│ 4. generate_bubble_diagram() -> Membangun graph relasi antarruang│
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GENERATOR & VALIDATOR                       │
│ 1. Generator Wrapper -> Eksekusi model difusi/GAN open-source  │
│ 2. Evaluator RFP-A   -> Pengujian 4 metrik spasial (VGA, A*)    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              FRONTEND (React Pure CSS - Apple Style)            │
│ Menerima manifestasi data real: JSON hasil parser & 5 denah top │
└─────────────────────────────────────────────────────────────────┘

# ===================================================================


# ===================================================================
# 3. PHASE 0: FOUNDATION & SETUP
# ===================================================================

STATUS: [x] COMPLETED

## 3.1 Environment Setup
# [x] Python 3.10+ terinstall
# [x] Virtual environment dibuat (backend/venv)
# [x] Dependencies terinstall (FastAPI, uvicorn, pydantic, pinecone-client, sentence-transformers)
# [x] Node.js & npm terinstall
# [x] React project dibuat (frontend/)
# [x] File .env dengan PINECONE_API_KEY & GROQ_API_KEY (UTF-8 tanpa BOM)

## 3.2 Dataset Collection & Vector Ingestion
# [x] Dataset Regulasi (SNI 03-1733-2004, PERMEN PUPR No. 29/2020, SNI 03-6572-2001)
# [x] Pemotongan teks (Chunking) & Ekstraksi fitur embedding menggunakan llama-text-embed-v2
# [x] Ingesti data ke Pinecone Index: "rag-floorplan-knowledge" (2.843 records terunggah)
# [ ] RPLAN Dataset (80k+ denah) -> Status: Belum diunduh (untuk keperluan generator)

# ===================================================================


# ===================================================================
# 4. PHASE 1: PARSER & RAG MODULE
# ===================================================================

STATUS: [ ] 60% COMPLETED (Refactored for Pinecone Code Integration)

## 4.1 Groq API & Pinecone Setup
# [x] Koneksi API Key dan model llama-3.1-8b-instant berhasil diuji
# [x] Index Pinecone "rag-floorplan-knowledge" aktif pada region us-east-1

## 4.2 Fungsi Parser (LLM Ekstraksi Kebutuhan)
# [x] Fungsi: extract_user_intent(user_text: str) -> Dict
#     Output: { rooms, total_area, style, special_needs, user_profile }
# [x] Penanganan eror untuk structural None type pada total_area selesai

## 4.3 KODE INTEGRASI RAG (Fokus Utama Vibe Coding 1)
# [ ] Fungsi: retrieve_knowledge(query: str, top_k=5) -> List[Dict]
#     - Input: Query string dari intent arsitektural user
#     - Proses: Hit kueri ke host Pinecone index "rag-floorplan-knowledge" menggunakan embedding model llama-text-embed-v2
#     - Output: [{"text": str, "score": float}, ...]
# 
# [ ] Fungsi: extract_constraints(retrieved_contexts: List, original_query: str) -> List[Dict]
#     - Input: Dokumen teks dari Pinecone + query user
#     - Proses: Prompting ke Groq untuk ekstraksi batasan parameter numerik hukum bangunan
#     - Output: [{komponen, parameter, operator, nilai_numerik, satuan}]

## 4.4 Fungsi Topologi Spasial
# [ ] Fungsi: generate_bubble_diagram(requirements: Dict) -> Dict
#     - Logika formal: Representasi adjacency matrix/graph data struktur
#     - Output: { nodes: [id, label, type], edges: [source, target, weight] }

# ===================================================================


# ===================================================================
# 5. PHASE 2: GENERATOR MODULE
# ===================================================================

STATUS: [ ] NOT STARTED

## 5.1 Seleksi Model Open-Source (Substitusi GreenPlanner)
# [ ] Pengujian framework alternatif: ChatHouseDiffusion atau FloorplanDiffusion

## 5.2 Implementasi Wrapper Generator
# [ ] Fungsi: generate_floorplans(constraints: List, bubble_diagram: Dict, num_samples=100) -> List[Dict]

## 5.3 Integrasi Practical Design Evaluator (PDE)
# [ ] Fungsi: validate_energy(floorplan_layout) -> Dict (Validasi simulasi konsumsi energi termal)

# ===================================================================


# ===================================================================
# 6. PHASE 3: RFP-A EVALUATOR MODULE
# ===================================================================

STATUS: [ ] 40% COMPLETED

## 6.1 Algoritma Evaluasi Spasial 4-Dimensi
# [ ] S1 (Keterbukaan Spasial): calculate_spatial_openness(floorplan_image) -> Menggunakan Visibility Graph Analysis (VGA)
# [ ] S2 (Efisiensi Sirkulasi): calculate_circulation_efficiency(floorplan_graph) -> Perhitungan rute optimal menggunakan algoritma A*
# [ ] S3 (Rasionalitas Tata Letak): calculate_layout_rationality(floorplan) -> Metode Weighted Distance antar komponen fungsional
# [ ] S4 (Adaptabilitas Hubungan): calculate_spatial_adaptability(floorplan) -> Spatial Relation Metric (SDR)

# ===================================================================


# ===================================================================
# 7. PHASE 4: AI AGENT & ORCHESTRATION
# ===================================================================

STATUS: [ ] 30% COMPLETED

## 7.1 Pipeline Agen & Penentuan Bobot (Decision Matrix)
# [ ] Fungsi: agent_pipeline(user_text: str) -> List[Dict]
# [ ] Fungsi: determine_weights(user_profile: str) -> List[float] (Analisis preferensi user untuk pemeringkatan denah)

# ===================================================================


# ===================================================================
# 8. PHASE 5: WEB APPLICATION
# ===================================================================

STATUS: [x] 95% COMPLETED (Pending Real Data Sync)

## 8.1 Backend API (FastAPI)
# [x] Setup CORS, Swagger UI (/docs), routing HTTP POST ke /generate
# [x] Logger terstruktur format JSON standar industri

## 8.2 Frontend UI (React)
# [x] Desain Apple-style UI murni CSS tanpa emotikon
# [x] Penyetelan state manager (parsedData) untuk merender keluaran komponen JSON parser
# [ ] Mengubah endpoint konsumsi data dari mock data ke real pipeline data

## 8.3 Data Persistence
# [ ] Implementasi skema PostgreSQL (Tabel: users, generations, floorplans)

# ===================================================================


# ===================================================================
# 9. PHASE 6: TESTING & DEPLOYMENT
# ===================================================================

STATUS: [ ] NOT STARTED

# [ ] Unit Testing: pytest untuk main.py (`extract_user_intent`)
# [ ] Integration Testing: Pengujian end-to-end dari frontend ke response API
# [ ] Containerization: Setup Dockerfile dan docker-compose untuk backend dan frontend

# ===================================================================


# ===================================================================
# 10. REFERENCE & CITATIONS
# ===================================================================

# PAPER 1: GreenPlanner (ACM Multimedia / CVF 2026) - Energy-Aware Generative Framework
# PAPER 2: RFP-A Metrics (Buildings MDPI 2025) - Room Count, RFP-GED, Room Locations, RFP-IoU
# PAPER 3: Deep Learning & CV for Small Residential Space Layout (Jobe 2026) - VGA, A*, Weighted Distance, SDR
# PAPER 4: Space Syntax-guided Post-training (Automation in Construction 2026) - SSIO, D_pub, A_liv

# ===================================================================


# ===================================================================
# 11. PROGRESS SUMMARY
# ===================================================================

PHASE 0: FOUNDATION & SETUP          [x] 100%   ✅ SELESAI
PHASE 1: PARSER & RAG MODULE         [ ] 60%    ⏳ Integrasi Kode Konektor Pinecone & Bubble Diagram
PHASE 2: GENERATOR MODULE            [ ] 0%     ⏳ Menunggu model open-source
PHASE 3: RFP-A EVALUATOR MODULE      [ ] 40%    ⏳ Analisis matematis metrik selesai
PHASE 4: AI AGENT & ORCHESTRATION    [ ] 30%    ⏳ Arsitektur interkoneksi selesai
PHASE 5: WEB APPLICATION             [x] 95%    ✅ UI & Endpoint Mock Ready
PHASE 6: TESTING & DEPLOYMENT        [ ] 0%     ⏳ Belum dimulai

TOTAL ESTIMATED PROGRESS: ~54%

# ===================================================================


# ===================================================================
# 12. RECENT UPDATES (2026-07-16)
# ===================================================================

## ✅ Selesai
- Database Vektor Pinecone (`rag-floorplan-knowledge`) berhasil dikonfigurasi pada infrastruktur cloud.
- Berhasil melakukan embedding data regulasi bangunan (2.843 records terunggah) menggunakan model `llama-text-embed-v2`.
- Backend FastAPI dan Frontend React terhubung via Axios.

## 📋 Vibe Coding Next Steps (Urutan Instruksi Kode Selanjutnya)
1. **Langkah 1**: Buat fungsi `retrieve_knowledge` di `backend/main.py` menggunakan pustaka `pinecone-client` untuk menghubungkan backend ke indeks basis data vektor yang sudah ada.
2. **Langkah 2**: Buat fungsi `extract_constraints` menggunakan model Groq untuk memetakan dokumen hukum bangunan hasil pencarian menjadi representasi JSON terstruktur.
3. **Langkah 3**: Buat fungsi algoritma topologi `generate_bubble_diagram` untuk memetakan spasial ruangan berdasarkan JSON keluaran parser.

# ===================================================================
# END OF PROJECT MASTER FILE
# ===================================================================