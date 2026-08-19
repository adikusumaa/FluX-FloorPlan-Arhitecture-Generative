# Flux! AI — Project Workplan

> **Nama File:** workplan_flux.md
> **Versi Dokumen:** 1.2.0 (Detailed Hybrid Cloud-Local)
> **Status:** Approved Draft
> **Project Codename:** Flux! AI
> **Output Utama:** 5 Floor Plan RPLAN Style terbaik berdasarkan metrik RFP-A
> **Sumber Model Generatif:** ChatHouseDiffusion

---

## 1. Ringkasan Eksekutif

Flux! AI adalah sistem otomatisasi pembuatan denah rumah (floor plan) bergaya RPLAN. Sistem menerima dua bentuk input dari pengguna: **Lokasi** (titik peta) dan **NLP Input** (deskripsi natural mengenai kebutuhan ruang).

Proyek ini menggunakan arsitektur Hibrida untuk efisiensi komputasi:
1. **Lokal (Docker):** Menangani UI, Orkestrasi CrewAI, RAG, Analisis Lingkungan, dan Evaluasi matematis RFP-A.
2. **Cloud (Kaggle):** Menangani komputasi berat (PyTorch & ChatHouseDiffusion) menggunakan GPU, terhubung dengan lokal melalui Model Context Protocol (MCP).

---

## 2. Arsitektur Solusi & Teknologi

| Lapisan / Modul | Teknologi yang Digunakan | Lokasi Eksekusi |
| :--- | :--- | :--- |
| **Frontend** | React.js / Vite, TailwindCSS, Leaflet | Local (Docker) |
| **Backend** | Python, FastAPI, Uvicorn | Local (Docker) |
| **Orchestration** | CrewAI | Local (Docker) |
| **Vector Database** | Pinecone | External Service |
| **LLM Engine** | Google AI Studio / Local (Ollama) | External / Local |
| **Generation Model**| PyTorch, ChatHouseDiffusion | Cloud (Kaggle GPU) |
| **Integration** | MCP Server/Client (HTTP/ngrok) | Cloud & Local |
| **Geospatial & Env**| Nominatim (OSM), Open-Meteo API | Local (Docker) |

---

## 3. Struktur Folder

Penempatan fitur memisahkan logika yang berjalan di cloud (Kaggle) dan lokal.

    flux-ai/
    ├── interface/
    │   ├── backend/
    │   │   ├── main.py
    │   │   ├── api/
    │   │   │   ├── routes.py
    │   │   │   └── schemas.py
    │   │   ├── core/
    │   │   └── services/D
    │   └── frontend/
    │       ├── src/
    │       │   ├── App.js
    │       │   ├── components/
    │       │   ├── services/
    │       │   └── state/
    │       └── package.json
    ├── knowledge/
    │   ├── evaluation_matrix/
    │   ├── model/
    │   └── rag_docs/
    ├── rag/
    │   ├── chunker.py
    │   └── vector_store.py
    ├── agents/
    │   ├── crew.py
    │   ├── tasks.py
    │   └── tools/
    │       ├── rag_tool.py
    │       ├── env_tool.py
    │       └── generation_tool.py  # Memanggil MCP Client
    ├── nlp/
    │   ├── encoder.py
    │   └── decoder.py
    ├── environment/
    │   ├── location_parser.py
    │   └── analyzer.py
    ├── evaluation/
    │   ├── rfpa_metrics.py
    │   └── ranking_engine.py
    ├── mcp/
    │   ├── client/
    │   │   └── mcp_client.py       # Koneksi HTTP ke ngrok
    │   └── server/
    │       ├── mcp_server.py       # Script untuk di-run di Kaggle
    │       └── requirements.txt
    ├── docker/
    │   ├── docker-compose.yml
    │   ├── backend.Dockerfile
    │   └── frontend.Dockerfile
    └── workplan_flux.md

---

## 4. Definisi Fitur & Workplan Detail

### A. Fitur Interface Website

**A.1. Frontend (React.js)**
*   **Dev:**
    *   [x] Inisialisasi `interface/frontend/src/App.js` dasar.
    *   [x] Inisialisasi Vite, TailwindCSS, dan konfigurasi environment variables (`.env`).
    *   [x] Pembuatan UI Map Picker menggunakan Leaflet: Menangkap event klik untuk mendapatkan koordinat (*latitude*, *longitude*).
    *   [x] Pembuatan UI NLP Input: *Text area* dengan validasi state minimum karakter.
    *   [x] Integrasi *State Management* (Zustand/Redux) untuk tracking status *loading* AI.
    *   [x] Pembuatan UI Output Gallery: Render Base64 *image string* menjadi elemen `<img>`.
    *   [x] Pembuatan Detail Modal: Menampilkan data metrik RFP-A dan hasil string saran lingkungan.
*   **Test:**
    *   [x] Unit test state Leaflet untuk memastikan koordinat valid.
    *   [x] Unit test render komponen gambar menggunakan *dummy* Base64.

**A.2. Backend (FastAPI)**
*   **Dev:**
    *   [x] Inisialisasi `interface/backend/main.py`.
    *   [x] Implementasi Pydantic *schemas* untuk validasi *payload* masuk (koordinat dan teks NLP).
    *   [x] Pembuatan endpoint POST `/api/v1/generate`.
    *   [x] Integrasi pemanggilan `crew.py` (CrewAI) sebagai proses *background task* atau fungsi asinkron (AsyncIO).
    *   [x] Implementasi CORS middleware untuk mengizinkan *request* dari port React (5173).
*   **Test:**
    *   [x] Contract test endpoint `/api/v1/generate` (mengembalikan HTTP 200 dengan struktur respons JSON yang benar).

### B. Fitur RAG & Vector Database (Pinecone)
*   **Dev:**
    *   [x] Pembuatan skrip ekstraksi teks PDF (`PyMuPDF`).
    *   [x] Implementasi algoritma *Layout-Aware Chunking* untuk memisahkan tabel dan teks paragraf. Recursive Character Splitting (512 token, overlap 50)
    *   [x] Konfigurasi inisialisasi Pinecone index.
    *   [x] Pembuatan proses *embedding* teks menggunakan model *open-source* (misal: BAAI/bge-m3) dan *upsert* ke Pinecone.
    *   [x] Pembuatan fungsi `retriever` yang mengembalikan top-k dokumen berdasarkan perhitungan *cosine similarity*.
*   **Test:**
    *   [x] Unit test *chunker* memastikan teks tidak terpotong di tengah kalimat.
    *   [x] Integration test pengambilan data relevan dari Pinecone menggunakan kueri pengujian.

### C. Fitur NLP Encoder-Decoder (Token Optimization)

*   **Dev:**
    *   [ ] Pembuatan *system prompt* untuk LLM (Encoder) yang memaksa output berupa JSON berstruktur ketat (tanpa teks penjelasan tambahan).
    *   [ ] Pemetaan (*mapping*) variabel panjang menjadi format ringkas (misal: "Kamar Tidur" -> "kt").
    *   [ ] Pembuatan *Pydantic model* di sisi *Decoder* untuk memvalidasi JSON hasil keluaran LLM.
    *   [ ] Konversi JSON yang sudah divalidasi ke format parameter yang dikenali oleh `params.pkl` ChatHouseDiffusion.
*   **Test:**
    *   [ ] Pengukuran kalkulasi jumlah token *prompt* masuk dan keluar (target reduksi > 30%).
    *   [ ] Unit test *Decoder* menggunakan *input* JSON yang *malformed* untuk menguji penanganan kegagalan (*error handling*).

### D. Fitur Lingkungan & Lokasi (Environment Analysis)

*   **Dev:**
    *   [ ] Integrasi API Nominatim (OSM) untuk melakukan *reverse geocoding* koordinat menjadi nama area.
    *   [ ] Kalkulasi sudut deklinasi matahari berdasarkan parameter *latitude* untuk menentukan rekomendasi arah bukaan cahaya (*sun path*).
    *   [ ] HTTP GET ke Open-Meteo API (parameter suhu harian, kelembaban, dan dominasi arah angin).
    *   [ ] Pembuatan algoritma berbasis aturan (*rule-based*) untuk estimasi kebisingan jalan (rentang desibel) menggunakan kalkulasi jarak (*haversine formula*) dari titik koordinat ke struktur jalan terdekat di OSM.
*   **Test:**
    *   [ ] Unit test kalkulasi *haversine*.
    *   [ ] API *mock test* untuk Nominatim dan Open-Meteo untuk menghindari pembatasan batas akses (*rate limiting*) selama pengembangan.

### E. Fitur Integrasi Cloud: MCP Server (Kaggle) & Generation (ChatHouseDiffusion)

*   **Dev (Kaggle Cloud - `mcp_server.py`):**
    *   [ ] Konfigurasi FastAPI dan `pyngrok` di dalam *notebook* Kaggle untuk membuka URL publik.
    *   [ ] Inisialisasi pembacaan memori GPU menggunakan `torch.device('cuda')`.
    *   [ ] Pemuatan file bobot `model-98.pt` ke VRAM GPU.
    *   [ ] Pembuatan endpoint POST `/mcp/tools/generate_floorplans` yang menerima parameter denah, mengeksekusi model (10 iterasi), dan mengonversi tensor keluaran menjadi *list of strings* (Base64).
*   **Dev (Local - `mcp_client.py`):**
    *   [ ] Implementasi Python `requests` dengan *timeout* tinggi (misal: 120 detik) untuk mengakomodasi waktu inferensi GPU.
    *   [ ] Parsing HTTP *response* kembali menjadi format data yang dikenali oleh lokal.
*   **Test:**
    *   [ ] Pengecekan stabilitas koneksi memori GPU di Kaggle (Cek log penggunaan VRAM).
    *   [ ] Pengujian *round-trip* dari pengiriman parameter lokal hingga penerimaan *string* Base64 utuh.

### F. Fitur AI Agent Orkestrasi (CrewAI)

*   **Dev:**
    *   [ ] Definisi `Analyst Agent`: Diberikan instrumen `rag_tool` untuk menarik standar RPLAN.
    *   [ ] Definisi `Environment Agent`: Diberikan instrumen `env_tool` untuk memproses koordinat.
    *   [ ] Definisi `Generator Agent`: Diberikan instrumen `generation_tool` (MCP Client) untuk mengirim parameter ke Kaggle.
    *   [ ] Definisi `Evaluator Agent`: Diberikan tugas untuk menjalankan fungsi skoring terhadap 10 desain yang dikembalikan dari Kaggle.
    *   [ ] Penyusunan *Crew workflow* dengan mode proses secara berurutan (*sequential*).
*   **Test:**
    *   [ ] Pengujian siklus eksekusi penuh (E2E) CrewAI secara terisolasi tanpa frontend.

### G. Fitur Evaluasi & Ranking (RFP-A)

*   **Dev:**
    *   [ ] Translasi formula matematis evaluasi (misal: matriks konektivitas ruangan, kalkulasi metrik rasio luas) menjadi modul Python murni menggunakan `NumPy`.
    *   [ ] Eksekusi metrik RFP-A terhadap matriks 10 gambar *staging*.
    *   [ ] Implementasi algoritma pengurutan data dari skor tertinggi ke terendah dan pemotongan data (seleksi Top 5).
    *   [ ] Agregasi JSON final: Menggabungkan gambar (Base64), skor numerik RFP-A, dan rincian teks mitigasi lingkungan.
*   **Test:**
    *   [ ] Unit test fungsi matematis RFP-A menggunakan matriks ukuran ruang yang diisi secara statis untuk memastikan akurasi perhitungan.

---

## 5. Alur Proses Keseluruhan (End-to-End Flow Presisi)

1. **Input User:** Pengguna menekan titik pada peta (UI Leaflet) dan memasukkan parameter bahasa natural pada text area.
2. **REST API Call:** Frontend mengirimkan JSON *payload* (`lat`, `lon`, `nlp_text`) menuju Backend (FastAPI).
3. **CrewAI Trigger:** Backend menerima *payload* dan mengeksekusi siklus *Crew workflow*.
4. **Data Acquisition (Local):** 
   - `Analyst Agent` melakukan pencarian (Pinecone RAG).
   - `Environment Agent` menghitung parameter pencahayaan, angin, dan desibel (Nominatim & Open-Meteo).
5. **Token Optimization (Local):** `Encoder` memproses `nlp_text` dan konteks RAG menjadi JSON instruksi minimal.
6. **Remote Generation (MCP Client -> Server):** 
   - `Generator Agent` memanggil `generation_tool`.
   - Tool mengirimkan HTTP POST melalui MCP Client menuju URL ngrok (Kaggle).
   - MCP Server (Kaggle) mengeksekusi `model-98.pt` di GPU dan mengembalikan 10 desain gambar (*array Base64*).
7. **Scoring & Ranking (Local):** `Evaluator Agent` menerima Base64, memproses metrik matematis RFP-A, dan memfilter 5 desain dengan skor tertinggi.
8. **Output Delivery:** Backend menggabungkan seluruh informasi dan mengembalikan struktur JSON terpusat ke Frontend untuk dirender kepada pengguna.

---

## 6. Operasional & Deployment

*   **Kaggle (Cloud GPU):** 
    - Hanya menjalankan `mcp_server.py`. 
    - Harus dijalankan manual sebelum sistem lokal digunakan.
    - URL ngrok yang dihasilkan dimasukkan ke file `.env` lokal (`KAGGLE_MCP_URL`).
*   **Local (Docker):** 
    - Menjalankan Frontend dan Backend.
    - Menggunakan instruksi `docker-compose up -d --build`.
    - Kebutuhan spesifikasi: Prosesor multithread standar, RAM minimal 8GB, GPU lokal tidak diperlukan.