import numpy as np
import cv2
import logging
import base64
import io
from PIL import Image, ImageDraw

logging.basicConfig(level=logging.INFO, format='[ANALYZER] %(message)s')

class FloorplanAnalyzer:
    def __init__(self):
        self.color_map = {
            "LivingRoom": [238, 232, 170],
            "MasterRoom": [255, 165, 0],
            "Kitchen": [240, 128, 128],
            "Bathroom": [173, 216, 210],
            "Balcony": [107, 142, 35],
            "SecondRoom": [255, 215, 0],
            "ExteriorWall": [0, 0, 0],
            "External": [255, 255, 255]
        }

    def analyze_image(self, image_path):
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        analysis_result = {}
        
        for room_name, color in self.color_map.items():
            lower = np.array(color, dtype=np.uint8)
            upper = np.array(color, dtype=np.uint8)
            mask = cv2.inRange(img, lower, upper)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=4)
            
            room_instances = []
            for i in range(1, num_labels):
                area = stats[i, cv2.CC_STAT_AREA]
                if area > 10:
                    x = stats[i, cv2.CC_STAT_LEFT]
                    y = stats[i, cv2.CC_STAT_TOP]
                    w = stats[i, cv2.CC_STAT_WIDTH]
                    h = stats[i, cv2.CC_STAT_HEIGHT]
                    cx, cy = centroids[i]
                    
                    room_instances.append({
                        "area": int(area),
                        "bbox": [int(x), int(y), int(w), int(h)],
                        "centroid": [int(cx), int(cy)]
                    })
            
            if room_instances:
                analysis_result[room_name] = room_instances

        return analysis_result

    def create_tight_mask_base64(self, analysis_result, size=(64, 64)):
        img = Image.new('L', size, 255)
        draw = ImageDraw.Draw(img)
        
        for room_name, instances in analysis_result.items():
            if room_name in ["External", "ExteriorWall"]:
                continue
            for inst in instances:
                x, y, w, h = inst["bbox"]
                draw.rectangle([x, y, x+w, y+h], fill=0)
                
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')