"""
src/mcp/client/mcp_client.py
MCP Client untuk ChatHouseDiffusion (Kaggle Cloud)
"""
import os
import base64
import io
import time
from typing import List, Dict, Any, Optional

import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

DEFAULT_ENDPOINT = os.getenv("CHATHOUSE_ENDPOINT", "/mcp/tools/generate_floorplans")
DEFAULT_BASE_URL = os.getenv("CHATHOUSE_URL", "https://your-ngrok-url.ngrok-free.dev")


class ChatHouseClient:
    def __init__(self, base_url: Optional[str] = None, endpoint: Optional[str] = None):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        self.url = f"{self.base_url}{self.endpoint}"

    def _format_rooms(self, rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Konversi ukuran ke kategori S/M/L, pastikan field penting ada."""
        formatted = []
        for room in rooms:
            r = room.copy()
            if "category" not in r:
                r["category"] = "Unknown"
            if "size" in r and not isinstance(r["size"], str):
                size = r["size"]
                w, h = 10, 10
                if isinstance(size, dict):
                    w = int(float(size.get("width", 10)))
                    h = int(float(size.get("height", 10)))
                elif isinstance(size, list) and len(size) == 2:
                    w = int(float(size[0]))
                    h = int(float(size[1]))
                area = w * h
                if area > 300:
                    category_size = "L"
                elif area > 150:
                    category_size = "M"
                else:
                    category_size = "S"
                r["size"] = category_size
            if "location" not in r:
                r["location"] = "Unknown"
            if "links" not in r or not isinstance(r["links"], list):
                r["links"] = []
            formatted.append(r)
        return formatted

    def generate_floorplans(
        self,
        rooms: List[Dict[str, Any]],
        style: str = "modern",
        mask_template: int = 0,
        iterations: int = 1,
        timeout: int = 180
    ) -> List[Image.Image]:
        """
        Kirim request generate floorplan ke server.
        iterations: jumlah iterasi (server akan memperbaiki hasil).
        """
        rooms = self._format_rooms(rooms)
        payload = {
            "rooms": rooms,
            "style": style,
            "mask_template": mask_template,
            "iterations": iterations
        }
        print(f"[MCP] Sending request to: {self.url}")
        print(f"[MCP] Payload: {payload}")

        start = time.time()
        try:
            response = requests.post(self.url, json=payload, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timeout setelah {timeout} detik")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request gagal: {e}") from e

        elapsed = time.time() - start
        print(f"[MCP] Response diterima dalam {elapsed:.2f} detik")

        data = response.json()
        if data.get("status") != "success" or not data.get("images"):
            raise RuntimeError(f"Server error: {data.get('message', 'Unknown')}")

        images = []
        for img_b64 in data["images"]:
            if img_b64.startswith("data:image"):
                img_b64 = img_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(img_b64)
            images.append(Image.open(io.BytesIO(img_bytes)))

        return images

    def save(
        self,
        rooms: List[Dict[str, Any]],
        output_path: str,
        style: str = "modern",
        mask_template: int = 0,
        iterations: int = 1
    ) -> None:
        images = self.generate_floorplans(rooms, style, mask_template, iterations)
        if images:
            images[0].save(output_path)
            print(f"[MCP] Denah disimpan di: {output_path}")