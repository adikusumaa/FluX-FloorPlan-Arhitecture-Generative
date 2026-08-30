# 🏠 FluX! - Intelligent Generative Floor Plan System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.70+-purple.svg)](https://crewai.com/)

**FluX!** is an intelligent generative AI system that automatically designs and produces floor plans from natural language input utilizing the **ChatHouseDiffusion** architecture. Beyond simple image generation, FluX! validates every design through rigorous geometric constraints (RFP-A, RFP-IOU, RFP-D), environmental analysis (sun path, wind, noise), and AI‑driven summarization to ensure optimal, rational, and functional layouts.

![FluX Input Interface](img/Screenshot%202026-08-22%20145415.png)
*Natural language input interface.*

![FluX Input MAPPICK](img/Screenshot%202026-08-30%20125203.png)
*Map picker input interface.*

![FluX Output Interface](img/Screenshot%202026-08-26%20180554.png)
*Top‑5 recommended floor plans ranked by energy and spatial scores.*

![Analyze every RPLAN](img/Screenshot%202026-08-30%20125218.png)
*Environment analysis based on location – recommendations for weather and orientation optimization.*

![Conclusion Crew AI](img/Screenshot%202026-08-30%20125146.png)
*AI‑generated executive summary with pros and cons of each RPLAN candidate.*

---

## ✨ Key Features
- 🗣️ **Natural Language Processing**: Extracts room requirements, dimensions, and style via Qwen2.5-14B-Instruct.
- 📐 **Generative Core (ChatHouseDiffusion)**: Generates 15 layout variants per request based on topological inputs.
- 🌍 **Location‑Aware Design**: Fetches real‑time climate data (Open-Meteo, Overpass API) to optimize orientation.
- 📊 **RFP Spatial Metrics**: Every plan is scored strictly on **RFP-A (Alignment)**, **RFP-IOU (Intersection over Union)**, and **RFP-D (Distance)**.
- 🧠 **AI Agent Orchestration (CrewAI)**: Multi‑agent system for analysis, evaluation, and summarization.
- 🤖 **Google Gemini 3.5‑Flash**: Powers the CrewAI agents for natural language reasoning.
- 🌿 **Environment Evaluator**: External API calculates daylight, ventilation, and noise scores.
- 🎨 **Minimalist Apple‑Style UI**: Modern React (Vite) frontend with pure Glassmorphism CSS.

---

## 🛠️ Tech Stack
The project uses a **hybrid architecture** separating local execution (UI, orchestration, evaluation) and cloud execution (heavy AI generation).

### Frontend (Client‑Side)
- **Framework**: React.js (Vite)
- **Styling**: Pure CSS (Apple iOS Glassmorphism design)
- **Map Integration**: Leaflet

### Backend (Local)
- **Language**: Python 3.10+
- **API Framework**: FastAPI & Uvicorn
- **Orchestration**: CrewAI (multi‑agent system)
- **LLM Engine**: Qwen2.5-14B-Instruct (4-bit quantized) & Gemini 3.5-Flash
- **Environment Analysis**: Open‑Meteo API, Nominatim (OSM), Overpass API

### Cloud AI (Kaggle GPU)
- **Generative Model**: ChatHouseDiffusion
- **Integration**: MCP Server (FastAPI + ngrok)

---

## 🏗️ System Architecture

```text
User Input (text + location)
│
▼
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Backend                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │       NLP Encoder → Room List → CHD Format        │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │    MCP Client → Kaggle GPU (ChatHouseDiffusion)   │  │
│  │       → 15 layout variants returned as Base64     │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │    Spatial Evaluator → RFP-A, RFP-IOU, RFP-D      │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │     Environment Evaluator (Qwen 14B via ngrok)    │  │
│  │        → Daylight, Ventilation, Noise scores      │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │       CrewAI Agents → Analyst & Summariser        │  │
│  │    → Executive summary with pros, cons, & reco    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
│
▼
Top 5 Plans + AI Summary
```

---

## 📊 Spatial Evaluation (RFP Metrics)
FluX! evaluates generated floor plans against strict geometric and topological boundaries using standard Room-Floor Polygon (RFP) metrics:

| Metric | Name | Description |
| :--- | :--- | :--- |
| **RFP-A** | Alignment | Measures the alignment accuracy between the generated room polygons and the overall floor boundary. |
| **RFP-IOU** | Intersection over Union | Evaluates the overlap ratio between the predicted room bounding boxes and the topological constraints. |
| **RFP-D** | Distance | Calculates the positional error distance between the generated room coordinates and their intended placement. |

These are combined with **environmental scores** (Daylight, Ventilation, Noise) into a final **composite score** for ranking.

---

## 🚀 Installation & Setup

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- Google Gemini API key
- Ngrok auth token

### 1. Clone the Repository
```bash
git clone [https://github.com/adikusumaa/FluX--FloorPlan-Arhitecture-Gen-RFP-A-Parameter.git](https://github.com/adikusumaa/FluX--FloorPlan-Arhitecture-Gen-RFP-A-Parameter.git)
cd FluX--FloorPlan-Arhitecture-Gen-RFP-A-Parameter
```

### 2. Setup Backend
```bash
cd interface/backend

python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

Configure `.env`:
```env
GOOGLE_API_KEY=your_gemini_key
ENCODER_URL=http://localhost:8000
CHATHOUSE_URL=http://your-mcp-endpoint
```

Run Backend:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Setup Environment Evaluator & ChatHouseDiffusion (Kaggle)
Run the MCP server notebook on Kaggle with ngrok to expose the evaluation and diffusion endpoint. The URLs will be used in the local backend.

### 4. Setup Frontend
```bash
cd interface/frontend

npm install
npm run dev
```

---

## 🤖 AI Agent Orchestration (CrewAI)
FluX! uses CrewAI to orchestrate multiple AI agents working sequentially:

| Agent | Role | Tools Used |
|-------|------|------------|
| Analyst Agent | Analyses each floor plan variant for strengths, weaknesses, and compliance | – |
| Summariser Agent | Generates a concise executive summary with pros, cons, and recommendations | – |
| Generator Agent | Communicates with the MCP client to invoke ChatHouseDiffusion on Kaggle | generation_tool |
| Evaluator Agent | Calculates RFP metrics and ranks candidates | rfpa_metrics.py |

---

## 🧪 End‑to‑End Flow
1. **User Input:** User clicks on the map (Leaflet) and types a natural language description.
2. **API Call:** Frontend sends `{ lat, lon, user_text }` to FastAPI endpoint.
3. **CrewAI Trigger:** Backend launches the CrewAI workflow.
4. **NLP Encoding:** User text is parsed into structured room requirements.
5. **Generation (Cloud):** MCP Client sends request to Kaggle GPU – ChatHouseDiffusion generates variants.
6. **Scoring & Ranking:** RFP metrics and environment scores are calculated, top 5 selected.
7. **Summarization:** CrewAI agents generate an executive summary.
8. **Response:** Backend returns JSON with top 5 plans, scores, and AI summary.
9. **Rendering:** Frontend displays the gallery, ORCA scores, and the AI summary.

---

## 🤝 Contributing
Project status: ≈75% complete. Areas for contribution:
- Integration of RAG (Pinecone) for building regulations
- Enhanced thermal simulation (PDE solver)
- More robust error handling and logging

To contribute:
1. Fork this repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📜 Academic References
- ChatHouseDiffusion – Generative Floor Plan Framework
- GreenPlanner (ACM Multimedia 2026) – Energy‑Aware Generative Framework
- RFP Metrics (Buildings MDPI 2025)
- Deep Learning for Small Residential Space (Jobe 2026)

---

## 📄 License
Distributed under the MIT License. See LICENSE for more information.

*Developed by Nur Adiyanto Kusuma Nuhgraha*