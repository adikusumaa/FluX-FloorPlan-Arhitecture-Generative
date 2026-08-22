import numpy as np
import cv2
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='[VISION] %(message)s')

class FloorplanAnalyzer:
    def __init__(self, min_area_threshold: int = 40):
        self.min_area_threshold = min_area_threshold
        self.color_map = {
            "LivingRoom": [238, 232, 170],
            "MasterRoom": [255, 165, 0],
            "Kitchen": [240, 128, 128],
            "Bathroom": [173, 216, 210],
            "Balcony": [107, 142, 35],
            "DinningRoom": [218, 112, 214],
            "Storage": [216, 191, 216],
            "CommonRoom": [255, 215, 0] 
        }
        self.total_pixels = 64 * 64
        self.max_area_limits = {
            "S": 350,
            "M": 600,
            "L": 900,
            "XL": 1200
        }

    def analyze(self, image_path: str, target_rooms: List[Dict]) -> Dict:
        img = cv2.imread(image_path)
        if img is None:
            logging.error(f"Cannot read image at {image_path}")
            return {
                "missing_rooms": target_rooms, 
                "detected_rooms": [], 
                "missing_count": len(target_rooms), 
                "location_errors": 0, 
                "total_penalty": float('inf')
            }

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        detected_blobs = {cat: [] for cat in self.color_map}
        living_room_centroid = (32, 32)
        
        for category, color in self.color_map.items():
            lower = np.array(color, dtype=np.uint8)
            upper = np.array(color, dtype=np.uint8)
            mask = cv2.inRange(img, lower, upper)
            
            num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=4)
            
            valid_blobs = []
            for i in range(1, num_labels):
                area = stats[i, cv2.CC_STAT_AREA]
                if area >= self.min_area_threshold:
                    valid_blobs.append({
                        "area": int(area),
                        "centroid": (int(centroids[i][0]), int(centroids[i][1]))
                    })
            
            valid_blobs.sort(key=lambda x: x["area"], reverse=True)
            detected_blobs[category] = valid_blobs
            
            if category == "LivingRoom" and valid_blobs:
                living_room_centroid = valid_blobs[0]["centroid"]

        missing_rooms = []
        detected_rooms_data = []
        location_errors = 0
        assigned_counts = {cat: 0 for cat in self.color_map}
        
        for room in target_rooms:
            mapped_cat = room.get("category", "")
            
            blobs = detected_blobs.get(mapped_cat, [])
            assigned_idx = assigned_counts.get(mapped_cat, 0)
            
            req_size = room.get("size", "M")
            max_allowed_area = self.max_area_limits.get(req_size, 600)
            
            if assigned_idx < len(blobs):
                blob = blobs[assigned_idx]
                
                if blob["area"] > max_allowed_area:
                    missing_rooms.append(room)
                    continue
                    
                assigned_counts[mapped_cat] += 1
                
                req_loc = room.get("location", "center")
                dx = blob["centroid"][0] - living_room_centroid[0]
                dy = blob["centroid"][1] - living_room_centroid[1]
                
                actual_loc = "center"
                if abs(dx) > 5 or abs(dy) > 5:
                    if abs(dx) > abs(dy):
                        actual_loc = "east" if dx > 0 else "west"
                    else:
                        actual_loc = "south" if dy > 0 else "north"
                        
                if req_loc not in ["Unknown", "center"] and req_loc not in actual_loc:
                    location_errors += 1
                    
                detected_rooms_data.append({
                    "category": mapped_cat,
                    "name": room.get("name", ""),
                    "pixel_count": blob["area"],
                    "area_percent": float((blob["area"] / self.total_pixels) * 100),
                    "centroid": blob["centroid"],
                    "requested_size": req_size,
                    "requested_location": req_loc,
                    "actual_location": actual_loc
                })
            else:
                missing_rooms.append(room)

        return {
            "missing_rooms": missing_rooms,
            "detected_rooms": detected_rooms_data,
            "missing_count": len(missing_rooms),
            "location_errors": location_errors,
            "total_penalty": (len(missing_rooms) * 10) + location_errors
        }