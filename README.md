# 🏠 FluX! - Intelligent Generative Floor Plan System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

**FluX!** is an intelligent generative AI system that automatically designs and produces floor plans from natural language input. Beyond simple image generation, FluX! validates every design against building regulations (via RAG), thermal energy simulation (PDE), and a 4‑dimensional spatial evaluation metric (RFP‑A) to ensure optimal, rational, and functional layouts.

![FluX Input Interface](img/Screenshot%202026-07-30%20105052.png)
*Natural language input interface.*

![FluX Output Interface](img/Screenshot%202026-07-30%20105154.png)
*Top‑5 recommended floor plans ranked by energy and spatial scores.*

## ✨ Key Features

- 🗣️ **Natural Language Parsing**: Automatically extracts user intent, room requirements, style, and dimensions using Groq’s LLM (Llama-3.1).
- 📚 **RAG for Building Regulations**: Retrieves real‑time legal constraints (SNI, PERMEN PUPR) from over 2,800 documents via Pinecone vector database.
- 📐 **Topological Spatial Planning**: Generates bubble diagrams and room‑relation graphs.
- 🧠 **Smart Generator & Evaluator**: Produces hundreds of candidates, then filters them using A* algorithm, Visibility Graph Analysis (VGA), and thermal evaluation.
- 🎨 **Minimalist Apple‑Style UI**: Modern React frontend with pure CSS – lightweight, responsive, and intuitive.

## 🛠️ Tech Stack

The project uses a **monorepo** structure separating Frontend, Backend, and AI/Evaluation modules.

### Frontend (Client‑Side)
- **Framework**: React.js
- **Styling**: Pure CSS (Apple‑inspired design)
- **HTTP Client**: Axios

### Backend & AI (Server‑Side)
- **Language**: Python 3.10+
- **API Framework**: FastAPI
- **Server**: Uvicorn
- **AI Engine**: Groq API (Llama-3.1-8b-instant)
- **Vector DB**: Pinecone (llama-text-embed-v2)

## 🚀 Installation & Setup

Follow these steps to run FluX! locally.

### Prerequisites
- Node.js & npm (latest)
- Python 3.10+
- Groq API key (for NLP parsing)
- Pinecone API key (for RAG regulations)

### 1. Clone the Repository
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