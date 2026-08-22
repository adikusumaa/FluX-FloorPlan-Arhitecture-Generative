import logging
import base64
import json
import io
from typing import List, Dict
from PIL import Image, ImageDraw
from src.mcp.client.mcp_client import MCPClient
from src.agents.vision.floorplan_analyzer import FloorplanAnalyzer

logging.basicConfig(level=logging.INFO, format='[WORKFLOW] %(message)s')

class AgenticWorkflow:
    def __init__(self, mcp_url: str):
        self.client = MCPClient(mcp_url)
        self.analyzer = FloorplanAnalyzer()
        self.size_weights = {"XS": 1, "S": 2, "M": 3, "L": 4, "XL": 5}

    def generate_dynamic_mask(self, rooms: List[Dict]) -> str:
        total_weight = sum(self.size_weights.get(r.get("size", "M"), 3) for r in rooms)
        
        mask_dim = min(40, 16 + int(total_weight * 1.2))
        
        img = Image.new('L', (64, 64), 255)
        draw = ImageDraw.Draw(img)
        
        start_x = (64 - mask_dim) // 2
        start_y = (64 - mask_dim) // 2
        end_x = start_x + mask_dim
        end_y = start_y + mask_dim
        
        draw.rectangle([start_x, start_y, end_x, end_y], fill=0)
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def execute(self, target_rooms: List[Dict], output_prefix: str = "floorplan"):
        logging.info("Initiating dynamic masking workflow.")
        
        custom_mask_b64 = self.generate_dynamic_mask(target_rooms)
        
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
        
        analysis = self.analyzer.analyze(output_filename, target_rooms)
        logging.info(f"Analysis: {json.dumps(analysis, indent=2)}")
        logging.info("Workflow completed.")