import numpy as np
import cv2
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='[VISION] %(message)s')

class FloorplanAnalyzer:
    def __init__(self, min_area_threshold: int = 15):
        self.min_area_threshold = min_area_threshold
        self.color_map = {
            "LivingRoom": [238, 232, 170],
            "MasterRoom": [255, 165, 0],
            "Kitchen": [240, 128, 128],
            "Bathroom": [173, 216, 210],
            "Balcony": [107, 142, 35],
            "SecondRoom": [255, 215, 0] 
        }
        self.total_pixels = 64 * 64

    def analyze(self, image_path: str, target_rooms: List[Dict]) -> Dict:
        img = cv2.imread(image_path)
        if img is None:
            logging.error(f"Cannot read image at {image_path}")
            return {"missing_rooms": target_rooms, "detected_rooms": [], "missing_count": len(target_rooms)}

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        detected_rooms_data = []
        detected_categories = set()
        
        for category, color in self.color_map.items():
            lower = np.array(color, dtype=np.uint8)
            upper = np.array(color, dtype=np.uint8)
            mask = cv2.inRange(img, lower, upper)
            pixel_count = cv2.countNonZero(mask)
            
            if pixel_count >= self.min_area_threshold:
                detected_categories.add(category)
                
            if pixel_count > 0:
                area_percent = (pixel_count / self.total_pixels) * 100
                detected_rooms_data.append({
                    "category": category,
                    "pixel_count": int(pixel_count),
                    "area_percent": float(area_percent)
                })

        missing_rooms = []
        for room in target_rooms:
            room_cat = room.get("category", "")
            mapped_cat = "SecondRoom" if room_cat in ["GuestRoom", "ChildRoom", "StudyRoom", "CommonRoom"] else room_cat
            
            if mapped_cat not in detected_categories:
                missing_rooms.append(room)
                detected_rooms_data.append({
                    "category": mapped_cat,
                    "name": room.get("name", ""),
                    "pixel_count": 0,
                    "area_percent": 0.0
                })
            else:
                for det in detected_rooms_data:
                    if det["category"] == mapped_cat:
                        det["name"] = room.get("name", "")

        return {
            "missing_rooms": missing_rooms,
            "detected_rooms": detected_rooms_data,
            "missing_count": len(missing_rooms)
        }