from src.environment.analyzer import analyze_environment
from src.environment.evaluator import rank_plans_by_environment

def final_ranking_with_environment(
    top_5_plans: list,
    initial_scores: list,
    lat: float,
    lon: float
) -> list:
    """
    Mendapatkan ranking final dengan mempertimbangkan faktor lingkungan.

    Args:
        top_5_plans: list dari 5 denah teratas (dari ranking awal)
        initial_scores: skor awal untuk 5 denah tersebut
        lat, lon: koordinat lokasi

    Returns:
        List hasil ranking dengan environment score dan mitigasi
    """
    # 1. Ambil data lingkungan real-time
    env_report = analyze_environment(lat, lon)

    # 2. Ranking ulang dengan environment score
    ranked = rank_plans_by_environment(
        plans=top_5_plans,
        env_report=env_report,
        initial_scores=initial_scores,
        weight_env=0.3  # 30% bobot lingkungan, 70% skor awal
    )

    return ranked