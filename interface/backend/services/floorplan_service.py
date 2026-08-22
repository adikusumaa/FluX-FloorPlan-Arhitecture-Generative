import base64
import io
import random
import re
from PIL import Image, ImageDraw
from typing import Dict, Any, List
from api.schemas import FloorPlanData

def generate_floorplans(user_text: str, weights: List[float], location: Dict[str, float]) -> Dict[str, Any]:
    """
    Simulasi generate floor plan.
    Data berasal dari user_text, bukan default.
    """
    parsed_data = extract_parsed_data(user_text)

    plans = []
    for i in range(5):
        image_base64 = generate_floorplan_image(parsed_data, i)
        scores = {
            "composite": round(0.75 + i * 0.04, 2),
            "spatial_openness": round(random.uniform(0.6, 0.9), 2),
            "circulation_efficiency": round(random.uniform(0.6, 0.9), 2),
            "layout_rationality": round(random.uniform(0.6, 0.9), 2),
            "adaptability": round(random.uniform(0.6, 0.9), 2),
        }
        plan = FloorPlanData(
            id=f"plan_{i+1}",
            rank=i+1,
            image_url=f"data:image/png;base64,{image_base64}",
            style=parsed_data.get("style", "Modern"),
            scores=scores,
            energy={
                "EUI": round(random.uniform(70, 110), 1),
                "total_area": parsed_data["area"],
                "fire_safety_status": "OK"
            },
            suggestions={
                "improvement": "Tambahkan ventilasi silang untuk meningkatkan sirkulasi udara.",
                "layout": "Pertimbangkan penempatan dapur dekat ruang makan."
            }
        )
        plans.append(plan)

    return {
        "data": plans,
        "parsed_data": parsed_data
    }

def extract_parsed_data(user_text: str) -> Dict[str, Any]:
    """Ekstrak jumlah kamar, luas, gaya dari teks user."""
    # Default jika tidak terbaca – tapi user_text wajib diisi, jadi minimal ada teks
    rooms = 3
    bathrooms = 2
    area = 120
    style = "Modern"

    text = user_text.lower()

    # Deteksi jumlah kamar tidur
    match = re.search(r'(\d+)\s*kamar\s*tidur', text)
    if match:
        rooms = int(match.group(1))

    # Deteksi jumlah kamar mandi
    match = re.search(r'(\d+)\s*kamar\s*mandi', text)
    if match:
        bathrooms = int(match.group(1))

    # Deteksi luas (meter persegi)
    match = re.search(r'(\d+)\s*(m2|meter|m\s*persegi)', text)
    if match:
        area = int(match.group(1))

    # Deteksi gaya
    if "modern" in text:
        style = "Modern"
    elif "klasik" in text:
        style = "Klasik"
    elif "minimalis" in text:
        style = "Minimalis"

    return {
        "rooms": rooms,
        "bathrooms": bathrooms,
        "area": area,
        "style": style
    }

def generate_floorplan_image(parsed_data: Dict[str, Any], variant: int) -> str:
    """Generate gambar denah sederhana (PNG base64)."""
    width, height = 800, 600
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Gambar grid
    draw.line([(0, height//2), (width, height//2)], fill="gray", width=1)
    draw.line([(width//2, 0), (width//2, height)], fill="gray", width=1)

    room_count = parsed_data.get("rooms", 3)
    colors = ["#FFDDCC", "#CCFFCC", "#CCCCFF", "#FFFFCC", "#FFCCFF"]
    cell_w = width // 2
    cell_h = height // 2

    for i in range(min(room_count, 4)):  # batasi maks 4 agar tidak overflow
        x = (i % 2) * cell_w + 20
        y = (i // 2) * cell_h + 20
        w = cell_w - 40
        h = cell_h - 40
        draw.rectangle([x, y, x+w, y+h], fill=colors[i % len(colors)], outline="black", width=2)
        draw.text((x+10, y+10), f"Room {i+1}", fill="black")

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()