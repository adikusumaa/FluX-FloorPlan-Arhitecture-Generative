import os
import asyncio
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY tidak ditemukan di .env")

MODEL_CANDIDATES = [
    "gemini/gemini-3.5-flash",
    "gemini/gemini-flash-latest",
    "gemini/gemini-3.1-pro-preview",
    "gemini/gemini-3.6-flash",
]

def create_llm(model_name: str):
    return LLM(
        model=model_name,
        api_key=GOOGLE_API_KEY,
        temperature=0.7,
        use_native=False,
    )

llm = None
for model in MODEL_CANDIDATES:
    try:
        llm = create_llm(model)
        print(f"✅ Menggunakan model default: {model}")
        break
    except Exception as e:
        print(f"⚠️ Gagal inisialisasi {model}: {e}")
        continue

if llm is None:
    raise RuntimeError("Tidak ada model Gemini yang dapat digunakan.")

# --- Agen ---
def create_analyst_agent():
    return Agent(
        role="Architectural Data Analyst",
        goal="Analyze floor plan candidate data and provide qualitative insights",
        backstory="You are an expert in architectural and environmental data analysis.",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

def create_summarizer_agent():
    return Agent(
        role="Report Summarizer",
        goal="Create a concise, structured, and easy-to-understand executive summary",
        backstory="You are a technical writer capable of summarizing complex information into clear points.",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

# --- Core async ---
async def _generate_crew_summary_async_core(
    top_candidates: List[Dict[str, Any]],
    user_text: str,
    location: Optional[Dict[str, float]] = None
) -> str:
    analyst = create_analyst_agent()
    summarizer = create_summarizer_agent()

    task_analisis = Task(
        description=f"""
        Analyze the following floor plan candidates data:
        {top_candidates}
        
        User requirements: {user_text}
        Location: {location if location else 'Not available'}
        
        Provide insights on:
        - Strengths and weaknesses of each candidate
        - Suitability with user requirements
        - Most critical architectural layout improvements
        """,
        expected_output="Analysis report in paragraphs written in English.",
        agent=analyst,
    )

    # Prompt ringkasan profesional (tanpa emoji) dalam Bahasa Inggris
    task_ringkasan = Task(
        description="""
        Create a CONCISE, STRUCTURED, and PROFESSIONAL executive summary based on the analysis results in ENGLISH.

        YOU MUST STRICTLY FOLLOW THIS EXACT FORMAT (use the brackets as labels):

        [LOCATION]
        Write the location name, city, and brief climate condition (e.g., tropical, coastal).

        [BEST CANDIDATE]
        Write the rank and candidate ID, including the composite score.

        [PROS]
        - Point 1 (max 3 points)
        - Point 2
        - Point 3

        [CONS]
        - Point 1 (max 3 points)
        - Point 2
        - Point 3

        [MAIN RECOMMENDATIONS]
        - Point 1 (concrete and technical architectural steps)
        - Point 2
        - Point 3 (max 3 points)

        [CONCLUSION]
        One closing sentence emphasizing the value of the best candidate.

        RULES:
        - Write entirely in ENGLISH.
        - Avoid long paragraphs.
        - Max 1 sentence per point.
        - Use formal and technical architectural language.
        - Do not use emojis or informal symbols.
        """,
        expected_output="Executive summary with bracket labels and bullet points in English.",
        agent=summarizer,
        context=[task_analisis],
    )

    crew = Crew(
        agents=[analyst, summarizer],
        tasks=[task_analisis, task_ringkasan],
        process=Process.sequential,
        verbose=True,
    )

    last_exception = None
    for model in MODEL_CANDIDATES:
        try:
            new_llm = create_llm(model)
            analyst.llm = new_llm
            summarizer.llm = new_llm
            print(f"🔄 Mencoba dengan model: {model}")
            result = await crew.kickoff_async()
            print(f"✅ Berhasil dengan model: {model}")
            break
        except Exception as e:
            last_exception = e
            print(f"❌ Gagal dengan model {model}: {e}")
            continue
    else:
        raise last_exception or RuntimeError("Semua model gagal.")

    if hasattr(result, 'output'):
        return result.output
    elif hasattr(result, 'raw'):
        return result.raw
    else:
        return str(result)

# --- Fungsi async (dipanggil dari FastAPI) ---
async def generate_crew_summary_async(
    top_candidates: List[Dict[str, Any]],
    user_text: str,
    location: Optional[Dict[str, float]] = None
) -> str:
    return await _generate_crew_summary_async_core(top_candidates, user_text, location)

# --- Fungsi sync (untuk test_cli) ---
def generate_crew_summary(
    top_candidates: List[Dict[str, Any]],
    user_text: str,
    location: Optional[Dict[str, float]] = None
) -> str:
    return asyncio.run(_generate_crew_summary_async_core(top_candidates, user_text, location))