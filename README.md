# 🏠 FluX! - Intelligent Generative Floor Plan System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

**FluX!** adalah Sistem AI generatif berbasis arsitektur cerdas yang mampu merancang dan menghasilkan denah rumah secara otomatis dari input teks (Natural Language). Tidak sekadar membuat gambar, FluX! memvalidasi setiap rancangan denah menggunakan standar regulasi bangunan (via RAG), simulasi energi termal (PDE), dan metrik evaluasi spasial 4-dimensi (RFP-A) untuk memastikan desain yang optimal, rasional, dan fungsional.

![FluX Input Interface](img/Screenshot%202026-07-30%20105052.png)
*Antarmuka input kebutuhan pengguna berbasis teks natural.*

![FluX Output Interface](img/Screenshot%202026-07-30%20105154.png)
*Output rekomendasi 5 denah terbaik berdasarkan skor energi dan ruang.*

## ✨ Fitur Utama

- 🗣️ **Natural Language Parsing**: Mengekstraksi intent dan kebutuhan ruang pengguna (jumlah kamar, gaya, luasan, dsb) secara otomatis menggunakan LLM Groq (Llama-3.1).
- 📚 **RAG for Building Regulations**: Mengambil batasan hukum tata bangunan (SNI, PERMEN PUPR) secara real-time dari lebih dari 2.800 dokumen menggunakan Pinecone Vector Database.
- 📐 **Topological Spatial Planning**: Menghasilkan *Bubble Diagram* dan graf relasi antarruang secara terstruktur.
- 🧠 **Smart Generator & Evaluator**: Memproduksi ratusan kandidat denah, lalu memfilternya dengan ketat menggunakan algoritma A*, Visibility Graph Analysis (VGA), dan evaluasi termal.
- 🎨 **Minimalist Apple-Style UI**: Antarmuka web modern yang dibangun dengan React murni dan CSS tanpa dependensi berlebih, super responsif dan intuitif.

## 🛠️ Teknologi yang Digunakan (Tech Stack)

Proyek ini menggunakan arsitektur **Monorepo** yang memisahkan Frontend, Backend, dan Modul AI/Evaluator.

### Frontend (Client-Side)
- **Framework**: React.js
- **Styling**: Pure CSS (Apple-Style Design)
- **HTTP Client**: Axios

### Backend & AI (Server-Side)
- **Bahasa**: Python 3.10+
- **Framework API**: FastAPI
- **Server**: Uvicorn
- **AI Engine**: Groq API (Llama-3.1-8b-instant)
- **Vector Database**: Pinecone (llama-text-embed-v2)

## 🚀 Cara Menjalankan Proyek (Instalasi)

Ikuti langkah-langkah berikut untuk menjalankan aplikasi FluX! di lingkungan lokal Anda.

### Prasyarat
- Node.js & npm (terbaru)
- Python (v3.10 ke atas)
- API Key Groq (Untuk Parsing NLP)
- API Key Pinecone (Untuk RAG Regulasi)

### 1. Clone Repositori
```bash
git clone https://github.com/adikusumaa/FluX--FloorPlan-Arhitecture-Gen-RFP-A-Parameter.git
cd FluX--FloorPlan-Arhitecture-Gen-RFP-A-Parameter
```

### 2. Setup Backend
Buka terminal, arahkan ke folder `backend`:
```bash
cd backend

# Buat Virtual Environment
python -m venv venv

# Aktivasi Venv (Windows):
venv\Scripts\activate
# Aktivasi Venv (Mac/Linux):
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
```

**Konfigurasi Environment Backend:**
Buat file `.env` di dalam folder `backend/` dan isi dengan konfigurasi Anda:
```env
GROQ_API_KEY=Kunci_API_Groq_Anda
PINECONE_API_KEY=Kunci_API_Pinecone_Anda
```

**Jalankan Server Backend:**
```bash
uvicorn main:app --reload
```
API akan berjalan dan dokumentasi Swagger dapat diakses di `http://127.0.0.1:8000/docs`

### 3. Setup Frontend
Buka terminal baru, masuk ke folder `frontend`:
```bash
cd frontend

# Install Dependencies
npm install

# Jalankan Server Frontend
npm start
```
Aplikasi web akan berjalan dan bisa diakses di `http://localhost:3000`

## 📂 Struktur Direktori Utama
```text
FluX!/
├── backend/                # Layanan API & AI Agent
│   ├── main.py             # Entry point FastAPI & Ruting
│   ├── parser.py           # Logika Groq NLP Parser
│   ├── rag_engine.py       # Interaksi dengan Pinecone DB
│   ├── requirements.txt    # Dependensi Python
│   └── .env                # File Environment
│
├── frontend/               # Antarmuka Pengguna
│   ├── src/
│   │   ├── components/     # UI Components (Input, Output Cards)
│   │   ├── styles/         # Pure CSS files
│   │   └── App.js          # Main React App
│   └── package.json        # Dependensi JS
│
└── README.md               # Dokumentasi Proyek
```

## 📊 Metrik Evaluasi Spasial (RFP-A)

Sistem ini tidak sekadar membuat gambar secara acak, namun dinilai oleh AI Agent berdasarkan 4 dimensi utama:

| Kode | Dimensi Evaluasi | Metode / Algoritma | Deskripsi |
|------|------------------|--------------------|-----------|
| **S1** | Keterbukaan Spasial | Visibility Graph Analysis (VGA) | Mengukur rasio ruang terbuka visual (isovist) dalam layout. |
| **S2** | Efisiensi Sirkulasi | Algoritma A* | Menghitung rute terpendek dan kelancaran akses antar zona fungsional. |
| **S3** | Rasionalitas Tata Letak | Weighted Distance Metric | Memastikan ruangan yang berelasi tinggi (misal: Dapur & Ruang Makan) saling berdekatan. |
| **S4** | Adaptabilitas Ruang | Spatial Relation Metric (SDR) | Mengevaluasi fleksibilitas ruang untuk perubahan fungsi di masa depan. |

## 🤝 Kontribusi

Status Proyek saat ini berada di persentase **~54%** (Fase Integrasi RAG & Evaluator). Jika Anda tertarik dengan arsitektur generatif dan AI, kontribusi sangat diterima:
1. Fork repositori ini.
2. Buat branch fitur baru (`git checkout -b feature/NamaFitur`).
3. Commit perubahan Anda (`git commit -m 'Menambahkan fitur AI baru'`).
4. Push ke branch (`git push origin feature/NamaFitur`).
5. Buat Pull Request.

## 📜 Referensi Akademik
- **GreenPlanner** (ACM Multimedia 2026) - Energy-Aware Generative Framework
- **RFP-A Metrics** (Buildings MDPI 2025)
- **Deep Learning for Small Residential Space** (Jobe 2026)

---
*Dikembangkan oleh [adikusumaa]*