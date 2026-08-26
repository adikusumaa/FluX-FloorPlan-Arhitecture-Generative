import logging
import base64
import io
import cv2
import random
import numpy as np
from typing import List, Dict
from PIL import Image, ImageDraw
from src.mcp.client.mcp_client import MCPClient
from src.agents.vision.floorplan_analyzer import FloorplanAnalyzer

logger = logging.getLogger(__name__)

class AgenticWorkflow:
    def __init__(self, mcp_url: str):
        self.client = MCPClient(mcp_url)
        self.analyzer = FloorplanAnalyzer(min_area_threshold=40)
        self.size_weights = {"XS": 10, "S": 12, "M": 16, "L": 20, "XL": 26}
        self.valid_colors_rgb = [
            [238, 232, 170],
            [255, 165, 0],
            [240, 128, 128],
            [173, 216, 210],
            [107, 142, 35],
            [218, 112, 214],
            [216, 191, 216],
            [255, 215, 0]
        ]

    def generate_topological_mask(self, rooms: List[Dict], seed: int = 42) -> str:
        random.seed(seed)
        img = Image.new('L', (64, 64), 255)
        draw = ImageDraw.Draw(img)
        
        cx, cy = 32, 32
        
        for room in rooms:
            loc = room.get("location", "center")
            base_s = self.size_weights.get(room.get("size", "M"), 12)
            
            jitter = random.uniform(0.85, 1.15)
            ar = random.uniform(0.75, 1.25)
            
            area = (base_s ** 2) * jitter
            w = int(np.sqrt(area * ar))
            h = int(np.sqrt(area / ar))
            
            x1, y1, x2, y2 = cx, cy, cx, cy
            
            offset_dist = random.randint(8, 12)
            shift = random.randint(-3, 3)
            
            if "north" in loc:
                y1 = cy - h - offset_dist
                y2 = cy
                x1 = cx - w + shift
                x2 = cx + w + shift
            elif "south" in loc:
                y1 = cy
                y2 = cy + h + offset_dist
                x1 = cx - w + shift
                x2 = cx + w + shift
            elif "east" in loc:
                x1 = cx
                x2 = cx + w + offset_dist
                y1 = cy - h + shift
                y2 = cy + h + shift
            elif "west" in loc:
                x1 = cx - w - offset_dist
                x2 = cx
                y1 = cy - h + shift
                y2 = cy + h + shift
            else:
                c_margin_w = random.randint(2, 6)
                c_margin_h = random.randint(2, 6)
                x1, y1 = cx - w - c_margin_w, cy - h - c_margin_h
                x2, y2 = cx + w + c_margin_w, cy + h + c_margin_h

            x1, y1 = max(2, x1), max(2, y1)
            x2, y2 = min(61, x2), min(61, y2)
            
            draw.rectangle([x1, y1, x2, y2], fill=0)
            
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def apply_reconstruction(self, image_path: str):
        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        clean_canvas = np.full(img_rgb.shape, 255, dtype=np.uint8)
        footprint_mask = np.zeros(img_rgb.shape[:2], dtype=np.uint8)
        
        for color in self.valid_colors_rgb:
            lower = np.array(color, dtype=np.uint8)
            upper = np.array(color, dtype=np.uint8)
            mask = cv2.inRange(img_rgb, lower, upper)
            
            kernel_close = np.ones((5, 5), np.uint8)
            mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=1)
            
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask_closed, connectivity=4)
            for i in range(1, num_labels):
                area = stats[i, cv2.CC_STAT_AREA]
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                w = stats[i, cv2.CC_STAT_WIDTH]
                h = stats[i, cv2.CC_STAT_HEIGHT]
                
                touches_border = (x == 0) or (y == 0) or (x + w == 64) or (y + h == 64)
                
                if area >= 40 and not touches_border:
                    blob_mask = np.zeros_like(mask_closed)
                    blob_mask[labels == i] = 255
                    
                    contours, _ = cv2.findContours(blob_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        cv2.drawContours(blob_mask, contours, -1, 255, thickness=cv2.FILLED)
                    
                    kernel_open = np.ones((3, 3), np.uint8)
                    blob_mask = cv2.morphologyEx(blob_mask, cv2.MORPH_OPEN, kernel_open, iterations=1)
                    
                    clean_canvas[blob_mask == 255] = color
                    footprint_mask[blob_mask == 255] = 255

        kernel_fuse = np.ones((5, 5), np.uint8)
        solid_silhouette = cv2.morphologyEx(footprint_mask, cv2.MORPH_CLOSE, kernel_fuse, iterations=2)
        
        contours, _ = cv2.findContours(solid_silhouette, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            outer_mask = np.zeros_like(footprint_mask)
            cv2.drawContours(outer_mask, [main_contour], -1, 255, thickness=cv2.FILLED)
            
            kernel_square = np.ones((3, 3), np.uint8)
            outer_dilated = cv2.dilate(outer_mask, kernel_square, iterations=1)
            exterior_outline = cv2.subtract(outer_dilated, outer_mask)
            
            clean_canvas[exterior_outline > 0] = (0, 0, 0)
        
        clean_bgr = cv2.cvtColor(clean_canvas, cv2.COLOR_RGB2BGR)
        cv2.imwrite(image_path, clean_bgr)