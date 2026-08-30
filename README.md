# FluX! – Generative Floor Plan System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.70+-purple.svg)](https://crewai.com/)

> From natural language to the 5 best floor plans – validated by environment, energy, and spatial intelligence.

---

## Overview
FluX! is an end-to-end generative AI system that transforms a simple text description into optimal, energy-efficient floor plans. The system utilizes ChatHouseDiffusion for layout generation and evaluates the outputs using strict Room-Floor Polygon (RFP) spatial metrics. It combines:
- Natural Language Understanding (LLM Encoder)
- Generative Diffusion Models (ChatHouseDiffusion)
- Environment & Energy Simulation (solar, wind, noise)
- Geometric Spatial Evaluation (RFP-A, RFP-IOU, RFP-D)
- Intelligent Summarization (CrewAI agents)

---

## Key Features

| Feature | Description |
|---------|-------------|
| Natural Language Input | Extract room types, sizes, and links via Qwen2.5-14B encoder. |
| Location-Aware Design | Fetch real-time climate data (sun path, wind, noise) to optimize orientation. |
| ChatHouseDiffusion | Generate continuous and discrete floor plan representations based on topological inputs. |
| RFP Spatial Metrics | Evaluate generated plans against spatial constraints using RFP-A, RFP-IOU, and RFP-D. |
| Environmental Evaluation | Calculate daylight, ventilation, and noise scores based on local weather. |
| AI-Powered Summary | CrewAI agents analyze the top 5 plans and generate professional executive summaries. |
| Modern UI | Clean, responsive interface with map picker and live results (React/Vite). |

---

## Tech Stack

### Frontend
- React 18 (Vite)
- Pure CSS (Apple iOS Glassmorphism design)
- Leaflet

### Backend & AI
- Python 3.10+
- FastAPI + Uvicorn
- ChatHouseDiffusion
- Qwen2.5-14B-Instruct (4-bit quantized)
- CrewAI + Gemini API
- Open-Meteo & Overpass API

---

## System Architecture

```text
User Input (text + location)
│
▼
┌─────────────────────────────┐
│       FastAPI Backend       │
│  ┌───────────────────────┐  │
│  │     Encoder (NLP)     │  │
│  │  → Qwen2.5-14B        │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │       Generator       │  │
│  │ → ChatHouseDiffusion  │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │  Spatial Evaluator    │  │
│  │ → RFP Metrics         │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │ Environment Evaluator │  │
│  │ → Open-Meteo + LLM    │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │     CrewAI Agents     │  │
│  │ → Executive Summary   │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
│
▼
Top 5 Plans + Summary
```

---

## Spatial Evaluation (RFP Metrics)

Every generated plan is strictly evaluated against topological boundaries and constraints using standard Room-Floor Polygon (RFP) metrics:

| Metric | Name | Description |
|------|--------|------------------|
| RFP-A | Alignment | Measures the alignment accuracy between the generated room polygons and the overall floor boundary. |
| RFP-IOU | Intersection over Union | Evaluates the overlap ratio between the predicted room bounding boxes and the topological constraints. |
| RFP-D | Distance | Calculates the positional error distance between the generated room coordinates and their intended placement. |

---

## Screenshots

| Input & Map Picker | Top 5 Results | Detailed Analysis |
|--------------------|---------------|-------------------|
| ![Input](img/input.png) | ![Gallery](img/gallery.png) | ![Detail](img/detail.png) |

| Environmental Feedback | CrewAI Summary |
|------------------------|----------------|
| ![Env](img/env.png)    | ![Summary](img/summary.png) |

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/adikusumaa/FluX--FloorPlan-Arhitecture-Gen-RFP-A-Parameter.git](https://github.com/adikusumaa/FluX--FloorPlan-Arhitecture-Gen-RFP-A-Parameter.git)
cd FluX--FloorPlan-Arhitecture-Gen-RFP-A-Parameter
```

### 2. Backend Setup
```bash
cd interface/backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_key
NGROK_AUTH_LLM=your_ngrok_token
```

Run the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Environment Evaluator & Encoder (Qwen 14B)
```bash
cd services/environment_api
python app.py
```

### 4. Frontend Setup
```bash
cd interface/frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## How It Works (Step-by-Step)
1. User describes their dream home.
2. Location is picked on the map for climate context.
3. The encoder (Qwen2.5-14B) parses the text into structured room requirements.
4. ChatHouseDiffusion generates layout variants using topological masks.
5. Each variant is scored for spatial accuracy using RFP-A, RFP-IOU, and RFP-D.
6. The environment API evaluates daylight, ventilation, and noise based on local climate data.
7. CrewAI agents analyze the top 5 plans and produce a professional executive summary.
8. The frontend displays the results with interactive cards and the AI summary.

---

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License
Distributed under the MIT License. See `LICENSE` for more information.

---

## Academic References
- ChatHouseDiffusion – Generative Floor Plan Framework
- RFP Metrics – Spatial Evaluation Parameters
- Deep Learning for Small Residential Space – Jobe 2026

---

## Author
**Nur Adiyanto Kusuma Nuhgraha**  
[GitHub](https://github.com/adikusumaa) · LinkedIn  
Built as a research portfolio project for generative architecture and AI.