import requests
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='[MCP_CLIENT] %(message)s')

class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.endpoint = f"{self.base_url}/mcp/tools/generate_floorplans"

    def generate_floorplan(self, rooms: List[Dict], mask_template: int = 0, cond_scale: float = 1.5, custom_mask: str = None) -> Dict:
        payload = {
            "rooms": rooms,
            "style": "modern",
            "mask_template": mask_template,
            "cond_scale": cond_scale
        }
        
        if custom_mask:
            payload["custom_mask"] = custom_mask

        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(self.endpoint, data=json.dumps(payload), headers=headers, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            return {}