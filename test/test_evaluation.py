import sys
import os
import json
import tempfile
import cv2

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.agents.vision.floorplan_analyzer import FloorplanAnalyzer
from src.agents.evaluation.rfpa_metrics import calculate_rfpa_metrics

IMAGE_PATH = os.path.join(ROOT_DIR, "test_output_topological_dynamic.png")

REQUESTED_ROOMS = [
    {
        "name": "living room",
        "category": "LivingRoom",
        "size": "L",
        "location": "center",
        "links": ["master bedroom", "bathroom 1", "common room", "kitchen", "balcony"]
    },
    {
        "name": "master bedroom",
        "category": "MasterRoom",
        "size": "M",
        "location": "northwest",
        "links": ["living room", "bathroom 1"]
    },
    {
        "name": "bathroom 1",
        "category": "Bathroom",
        "size": "S",
        "location": "west",
        "links": ["living room", "master bedroom"]
    },
    {
        "name": "common room",
        "category": "CommonRoom",
        "size": "M",
        "location": "southwest",
        "links": ["living room", "balcony"]
    },
    {
        "name": "balcony",
        "category": "Balcony",
        "size": "S",
        "location": "south",
        "links": ["living room", "common room"]
    },
    {
        "name": "kitchen",
        "category": "Kitchen",
        "size": "M",
        "location": "east",
        "links": ["living room"]
    }
]

def prepare_image_64(image_path: str) -> str:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    h, w = img.shape[:2]
    if (h, w) == (64, 64):
        return image_path

    img_resized = cv2.resize(img, (64, 64), interpolation=cv2.INTER_NEAREST)

    temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    cv2.imwrite(temp.name, img_resized)
    return temp.name

resized_path = prepare_image_64(IMAGE_PATH)

analyzer = FloorplanAnalyzer(min_area_threshold=15)
analysis = analyzer.analyze(resized_path, REQUESTED_ROOMS)

rfpa = calculate_rfpa_metrics(
    analysis=analysis,
    requested_rooms=REQUESTED_ROOMS,
    image_path=resized_path,
)

print(json.dumps(rfpa, indent=2))

if resized_path != IMAGE_PATH:
    os.unlink(resized_path)