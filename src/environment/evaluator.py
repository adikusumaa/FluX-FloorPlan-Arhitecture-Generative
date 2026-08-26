"""
src/environment/evaluator.py
Evaluasi denah terhadap faktor lingkungan: noise, daylight, ventilation.
Menghasilkan skor (0-1) dan teks mitigasi.
"""
import math
from typing import Dict, List, Tuple, Any
from .analyzer import EnvironmentReport


def evaluate_plan_environment(
    plan: dict,
    env: EnvironmentReport,
    weights: dict = None
) -> Tuple[float, str, dict]:
    """
    Menghitung skor lingkungan (0-1) dan teks mitigasi untuk satu denah.

    Args:
        plan: dictionary dengan keys:
            - 'orientation': derajat rotasi denah dari utara (0 = utara)
            - 'rooms': list of {'name': str, 'windows': list, 'center': [x,y]}
        env: EnvironmentReport dari analyze_environment()
        weights: dict dengan bobot untuk noise, daylight, ventilation

    Returns:
        (env_score, mitigation_text, scores_detail)
    """
    if weights is None:
        weights = {"noise": 0.4, "daylight": 0.3, "ventilation": 0.3}

    orientation = plan.get('orientation', 0)
    rooms = plan.get('rooms', [])

    # ============================================================
    # 1. SKOR KEBISINGAN (Noise Score)
    # ============================================================
    # Semakin dekat ke jalan, semakin tinggi noise
    distance_km = env.noise.nearest_road_distance_km
    # Normalisasi: jarak 0km -> noise tinggi (skor 0), jarak >2km -> noise rendah (skor 1)
    noise_raw = min(1.0, distance_km / 2.0)  # 0-1, makin jauh makin tinggi
    noise_score = noise_raw

    # Penalti jika ruang tidur menghadap sumber noise (sisi terdekat dengan jalan)
    # Asumsikan sumber noise dari arah jalan terdekat (kita tidak punya arah persis)
    # Pendekatan: ruangan dengan jendela di sisi utara/selatan (tergantung lokasi)
    # Untuk sekarang, kita gunakan noise_score berdasarkan jarak saja

    # ============================================================
    # 2. SKOR PENCAHAYAAN (Daylight Score)
    # ============================================================
    # Gunakan rekomendasi orientasi optimal dari sun_path
    optimal_text = env.sun_path.optimal_orientation.lower()
    if "selatan" in optimal_text or "south" in optimal_text:
        optimal_deg = 180
    elif "utara" in optimal_text or "north" in optimal_text:
        optimal_deg = 0
    elif "timur" in optimal_text or "east" in optimal_text:
        optimal_deg = 90
    elif "barat" in optimal_text or "west" in optimal_text:
        optimal_deg = 270
    else:
        optimal_deg = 180  # default

    # Hitung selisih orientasi denah terhadap optimal
    diff = abs(orientation - optimal_deg) % 360
    diff = min(diff, 360 - diff)  # ambil sudut terkecil
    daylight_score = max(0, 1 - diff / 180)  # 0 jika berlawanan arah

    # Bonus jika solar radiation tinggi (lokasi cerah)
    if env.sun_path.solar_radiation > 200:
        daylight_score = min(1.0, daylight_score * 1.2)

    # ============================================================
    # 3. SKOR VENTILASI (Ventilation Score)
    # ============================================================
    # Cross-ventilation: cek apakah ada bukaan di dua sisi berlawanan
    # Gunakan arah angin dominan dari weather
    wind_dir = env.weather.wind_direction

    # Semakin sejajar dengan arah angin, semakin baik untuk ventilasi
    # Idealnya denah memiliki bukaan di sisi yang sejajar dengan arah angin
    vent_diff = abs(orientation - wind_dir) % 360
    vent_diff = min(vent_diff, 360 - vent_diff)
    vent_score = max(0, 1 - vent_diff / 180)

    # Jika ada jendela di dua sisi berlawanan, bonus
    # Deteksi sederhana: cek apakah ada ruangan dengan jendela di orientasi berbeda
    window_orientations = set()
    for room in rooms:
        for win in room.get('windows', []):
            if 'direction' in win:
                window_orientations.add(win['direction'] % 360)
    if len(window_orientations) >= 2:
        # Cek apakah ada yang berlawanan (selisih ~180 derajat)
        orientations = list(window_orientations)
        for i in range(len(orientations)):
            for j in range(i+1, len(orientations)):
                if abs((orientations[i] - orientations[j]) % 360 - 180) < 30:
                    vent_score = min(1.0, vent_score * 1.3)
                    break

    # ============================================================
    # 4. SKOR GABUNGAN
    # ============================================================
    env_score = (
        weights["noise"] * noise_score +
        weights["daylight"] * daylight_score +
        weights["ventilation"] * vent_score
    )

    # ============================================================
    # 5. TEKS MITIGASI
    # ============================================================
    mitigation_parts = []
    suggestions = []

    # Noise
    if noise_score < 0.5:
        mitigation_parts.append(
            f"🔊 **Kebisingan**: Lokasi dekat jalan ({env.noise.nearest_road_distance_km:.2f} km, "
            f"~{env.noise.estimated_db} dB). Rekomendasi: pasang jendela kedap suara (double glazing), "
            "tanam pohon peredam di sisi luar, atau gunakan material insulasi akustik pada dinding."
        )
        suggestions.append("tambahkan insulasi suara")

    # Daylight
    if daylight_score < 0.5:
        mitigation_parts.append(
            f"☀️ **Pencahayaan**: Orientasi denah kurang optimal ({orientation}°). "
            f"Arah ideal: {env.sun_path.optimal_orientation}. Rekomendasi: tambah jendela di sisi "
            f"{env.sun_path.optimal_orientation}, gunakan skylight, atau cat dinding dengan warna cerah."
        )
        suggestions.append("optimalkan bukaan cahaya")

    # Ventilation
    if vent_score < 0.5:
        mitigation_parts.append(
            f"💨 **Ventilasi**: Kurang cross-ventilation. Arah angin dominan: {env.weather.wind_direction}°. "
            "Rekomendasi: tambahkan bukaan di dinding berlawanan arah angin, atau gunakan ventilasi mekanis."
        )
        suggestions.append("tingkatkan sirkulasi udara")

    # Solar radiation (informasi tambahan)
    if env.sun_path.solar_radiation > 400:
        mitigation_parts.append(
            f"☀️ **Radiasi tinggi**: {env.sun_path.solar_radiation} W/m². Pertimbangkan penggunaan kaca Low-E, "
            "overhang, atau tanaman rambat untuk mengurangi panas berlebih."
        )
        suggestions.append("pasang pelindung panas")

    if not mitigation_parts:
        mitigation_text = "✅ Denah ini sudah cukup responsif terhadap lingkungan sekitar."
    else:
        mitigation_text = "\n\n".join(mitigation_parts)

    scores_detail = {
        "noise_score": round(noise_score, 3),
        "daylight_score": round(daylight_score, 3),
        "ventilation_score": round(vent_score, 3),
        "env_score": round(env_score, 3),
        "suggestions": suggestions
    }

    return env_score, mitigation_text, scores_detail


def rank_plans_by_environment(
    plans: List[dict],
    env_report: EnvironmentReport,
    initial_scores: List[float] = None,
    weight_env: float = 0.3
) -> List[dict]:
    """
    Ranking denah berdasarkan kombinasi skor awal + skor lingkungan.

    Args:
        plans: list of plan dictionaries
        env_report: EnvironmentReport dari analyze_environment()
        initial_scores: list skor awal (misal dari aesthetic/functionality)
        weight_env: bobot untuk skor lingkungan (0-1)

    Returns:
        List of dict dengan keys: plan, initial_score, env_score, combined_score, mitigation, scores_detail
    """
    if initial_scores is None:
        initial_scores = [0.5] * len(plans)

    results = []
    for i, plan in enumerate(plans):
        env_score, mitigation, scores_detail = evaluate_plan_environment(plan, env_report)
        combined = (1 - weight_env) * initial_scores[i] + weight_env * env_score

        results.append({
            "plan": plan,
            "initial_score": initial_scores[i],
            "env_score": env_score,
            "combined_score": combined,
            "mitigation": mitigation,
            "scores_detail": scores_detail
        })

    # Urutkan berdasarkan combined_score descending
    results.sort(key=lambda x: x["combined_score"], reverse=True)
    return results


# ============================================================
# Testing
# ============================================================
if __name__ == "__main__":
    from .analyzer import analyze_environment

    # Sample plan
    sample_plan = {
        "orientation": 45,
        "rooms": [
            {"name": "kamar tidur", "center": [10, 10], "windows": [{"direction": 0}]},
            {"name": "ruang tamu", "center": [20, 20], "windows": [{"direction": 180}]}
        ]
    }

    env = analyze_environment(-6.2088, 106.8456)
    score, mitigation, detail = evaluate_plan_environment(sample_plan, env)

    print("="*60)
    print("🌱 Environmental Evaluation Result")
    print("="*60)
    print(f"Skor Lingkungan: {score:.3f}")
    print(f"Detail: {detail}")
    print("\n📝 Mitigation:")
    print(mitigation)