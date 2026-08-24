import logging
import base64
import json
import io
import cv2
import numpy as np
from typing import List, Dict
from PIL import Image, ImageDraw
from src.mcp.client.mcp_client import MCPClient
from src.agents.vision.floorplan_analyzer import FloorplanAnalyzer

logging.basicConfig(level=logging.INFO, format='[WORKFLOW] %(message)s')

class AgenticWorkflow:
    def __init__(self, mcp_url: str):
        self.client = MCPClient(mcp_url)
        self.analyzer = FloorplanAnalyzer(min_area_threshold=40)
        self.size_weights = {"XS": 10, "S": 12, "M": 16, "L": 20, "XL": 26}
        self.valid_colors_rgb = [
            [238, 232, 170],  # LivingRoom
            [255, 165, 0],    # MasterRoom
            [240, 128, 128],  # Kitchen
            [173, 216, 210],  # Bathroom
            [107, 142, 35],   # Balcony
            [218, 112, 214],  # DinningRoom
            [216, 191, 216],  # Storage
            [255, 215, 0]     # CommonRoom (akan di-map ke LivingRoom di converter)
        ]

    def generate_topological_mask(self, rooms: List[Dict]) -> str:
        img = Image.new('L', (64, 64), 255)
        draw = ImageDraw.Draw(img)
        
        cx, cy = 32, 32
        
        for room in rooms:
            loc = room.get("location", "center")
            s = self.size_weights.get(room.get("size", "M"), 12)
            
            x1, y1, x2, y2 = cx, cy, cx, cy
            
            if "north" in loc:
                y1 = cy - s - 10
                y2 = cy
            elif "south" in loc:
                y1 = cy
                y2 = cy + s + 10
                
            if "east" in loc:
                x1 = cx
                x2 = cx + s + 10
            elif "west" in loc:
                x1 = cx - s - 10
                x2 = cx
                
            if loc == "center":
                x1, y1, x2, y2 = cx - s - 4, cy - s - 4, cx + s + 4, cy + s + 4
            else:
                if x1 == x2: 
                    x1 -= (s + 4)
                    x2 += (s + 4)
                if y1 == y2:
                    y1 -= (s + 4)
                    y2 += (s + 4)

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

    def execute(self, target_rooms: List[Dict], output_prefix: str = "floorplan"):
        logging.info("Initiating Topology-Driven Dynamic Masking Workflow.")
        
        custom_mask_b64 = self.generate_topological_mask(target_rooms)
        
        response = self.client.generate_floorplan(
            rooms=target_rooms,
            cond_scale=1.5,
            custom_mask=custom_mask_b64
        )

        if not response or "images" not in response or len(response["images"]) == 0:
            logging.error("Invalid response from MCP Server")
            return

        img_data = response["images"][0].split(",")[1]
        output_filename = f"{output_prefix}_dynamic.png"
        
        with open(output_filename, "wb") as fh:
            fh.write(base64.b64decode(img_data))
            
        self.apply_reconstruction(output_filename)
        
        analysis = self.analyzer.analyze(output_filename, target_rooms)
        
        logging.info(f"\nFINAL ANALYSIS:\n{json.dumps(analysis['detected_rooms'], indent=2)}")
        logging.info(f"Missing Rooms: {analysis['missing_count']} | Location Errors: {analysis['location_errors']}")
        logging.info(f"Workflow completed. Result saved to {output_filename}")