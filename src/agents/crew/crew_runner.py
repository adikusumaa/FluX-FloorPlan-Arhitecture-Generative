import os
import json
import logging
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Process, LLM  # <-- Perhatikan: LLM dari crewai

logger = logging.getLogger(__name__)

def generate_crew_summary(
    top_candidates: List[Dict[str, Any]],
    user_text: str,
    location: Optional[Dict[str, float]] = None
) -> str:
    if not top_candidates:
        return "Tidak ada kandidat denah untuk dianalisis."

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("[CREW] OPENAI_API_KEY tidak ditemukan, lewati pembuatan ringkasan CrewAI.")
        return ""

    # Gunakan LLM dari CrewAI (bukan ChatOpenAI)
    llm = LLM(
        model="gpt-4o-mini",   # atau "gpt-3.5-turbo"
        temperature=0.3,
        api_key=openai_api_key
    )

    candidates_info = []
    for cand in top_candidates:
        info = {
            "rank": cand.get("rank"),
            "id": cand.get("id"),
            "composite_score": cand.get("scores", {}).get("composite"),
            "env_score": cand.get("scores", {}).get("env_score"),
            "orientation": cand.get("orientation"),
            "location": cand.get("location"),
            "mitigation": cand.get("suggestions", {}).get("environment", "")[:500]
        }
        candidates_info.append(info)

    prompt_data = json.dumps({
        "user_request": user_text,
        "location": location,
        "top_candidates": candidates_info
    }, indent=2, ensure_ascii=False)

    agent = Agent(
        role="Architectural Report Writer",
        goal="Tulis laporan ringkas dan profesional untuk rekomendasi denah terbaik berdasarkan data yang diberikan.",
        backstory="Anda adalah arsitek senior yang ahli dalam menjelaskan keputusan desain dan analisis lingkungan.",
        llm=llm,
        verbose=False
    )

    task = Task(
        description=(
            "Berdasarkan data berikut, buatlah ringkasan profesional yang mencakup:\n"
            "1. Deskripsi singkat kebutuhan pengguna.\n"
            "2. Peringkat denah terbaik dan alasan utama.\n"
            "3. Pertimbangan lingkungan utama (kebisingan, pencahayaan, ventilasi).\n"
            "4. Rekomendasi perbaikan yang paling penting.\n"
            "Gunakan bahasa yang jelas dan hindari jargon berlebihan.\n\n"
            f"DATA:\n{prompt_data}"
        ),
        agent=agent,
        expected_output="Paragraf terstruktur yang siap ditampilkan ke pengguna."
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False
    )

    try:
        result = crew.kickoff()
        summary = str(result)
        logger.info("[CREW] Ringkasan berhasil dibuat.")
        return summary
    except Exception as e:
        logger.error(f"[CREW] Gagal membuat ringkasan: {e}")
        return ""