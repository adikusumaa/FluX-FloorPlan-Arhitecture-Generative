import sys
import os
import json
import tempfile
import cv2

# Tambahkan root proyek ke path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.agents.vision.floorplan_analyzer import FloorplanAnalyzer
from src.agents.evaluation.rfpa_metrics import calculate_rfpa_metrics

# ================= CONFIG =================
IMAGE_PATH = os.path.join(ROOT_DIR, "test_output_topological_dynamic.png")

REQUESTED_ROOMS = [
    {
        "name": "master bedroom",
        "category": "MasterRoom",
        "size": "S",
        "location": "Unknown",
        "links": ["living room"]
    },
    {
        "name": "bathroom 1",
        "category": "Bathroom",
        "size": "S",
        "location": "north",
        "links": ["living room"]
    },
    {
        "name": "bathroom 2",
        "category": "Bathroom",
        "size": "S",
        "location": "north",
        "links": ["living room"]
    },
    {
        "name": "living room",
        "category": "LivingRoom",
        "size": "S",
        "location": "Unknown",
        "links": ["master bedroom"]
    },
    {
        "name": "kitchen",
        "category": "Kitchen",
        "size": "S",
        "location": "east",
        "links": ["living room"]
    },
    {
        "name": "balcony",
        "category": "Balcony",
        "size": "S",
        "location": "south",
        "links": ["living room"]
    },
    {
        "name": "common room",
        "category": "CommonRoom",   # sudah diganti dari DiningRoom
        "size": "S",
        "location": "Unknown",
        "links": ["living room"]
    },
]


def prepare_image_64(image_path: str) -> str:
    """
    Memastikan gambar berukuran 64x64.
    Jika tidak, resize dengan INTER_NEAREST dan simpan ke file temporary.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    h, w = img.shape[:2]
    if (h, w) == (64, 64):
        return image_path

    print(f"Resizing {w}x{h} to 64x64 using INTER_NEAREST")
    img_resized = cv2.resize(img, (64, 64), interpolation=cv2.INTER_NEAREST)

    # Simpan temporary file
    temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    cv2.imwrite(temp.name, img_resized)
    return temp.name


# ================= PERSIAPAN IMAGE =================
resized_path = prepare_image_64(IMAGE_PATH)
print(f"Using image: {resized_path}")

# ================= ANALYZE =================
print("\n=== FLOOR PLAN ANALYZER ===")
analyzer = FloorplanAnalyzer(min_area_threshold=40)
analysis = analyzer.analyze(resized_path, REQUESTED_ROOMS)

print("\nDetected rooms (dari FloorplanAnalyzer):")
for room in analysis.get("detected_rooms", []):
    print(f"  - {room['category']} ({room['name']}) | area={room['pixel_count']} | bbox={room.get('bbox')} | centroid={room['centroid']}")

print(f"\nMissing count : {analysis.get('missing_count')}")
print(f"Location errors: {analysis.get('location_errors')}")

# ================= RFP-A METRICS =================
print("\n=== RFP-A METRICS ===")
rfpa = calculate_rfpa_metrics(
    analysis=analysis,
    requested_rooms=REQUESTED_ROOMS,
    image_path=resized_path,
)

print(json.dumps(rfpa, indent=2))

# ================= CLEANUP =================
if resized_path != IMAGE_PATH:
    os.unlink(resized_path)
    print(f"Temporary file {resized_path} deleted.")