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

    # ============================================================
    # FUNGSI KONVERSI SIZE -> KATEGORI
    # ============================================================
    def _format_rooms(self, rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ubah size dari dict/list/string ke kategori: 'large', 'medium', 'small'
        Berdasarkan luas area (width * height).
        """
        formatted = []
        for room in rooms:
            r = room.copy()
            if "size" in r:
                size = r["size"]
                w, h = 10, 10
                if isinstance(size, dict):
                    w = int(float(size.get("width", 10)))
                    h = int(float(size.get("height", 10)))
                elif isinstance(size, list) and len(size) == 2:
                    w = int(float(size[0]))
                    h = int(float(size[1]))
                elif isinstance(size, str):
                    if "x" in size:
                        parts = size.split("x")
                        try:
                            w = int(float(parts[0]))
                            h = int(float(parts[1]))
                        except:
                            pass
                    else:
                        # Sudah kategori, biarkan
                        formatted.append(r)
                        continue
                # Konversi ke kategori berdasarkan luas
                area = w * h
                if area > 300:
                    category = "large"
                elif area > 150:
                    category = "medium"
                else:
                    category = "small"
                r["size"] = category
            formatted.append(r)
        return formatted

    def generate_floorplans(
        self,
        rooms: List[Dict[str, Any]],
        style: str = "modern",
        timeout: int = 180
    ) -> List[Image.Image]:
        """
        Kirim request generate floorplan ke server.
        """
        # Format rooms sebelum dikirim
        rooms = self._format_rooms(rooms)
        payload = {"rooms": rooms, "style": style}

        print(f"🌐 Sending request to: {self.url}")
        print(f"📦 Payload (size converted to categories): {payload}")

        start = time.time()
        try:
            response = requests.post(self.url, json=payload, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timeout setelah {timeout} detik")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request gagal: {e}") from e

        elapsed = time.time() - start
        print(f"⏱️ Response diterima dalam {elapsed:.2f} detik")

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

    def save(self, rooms: List[Dict[str, Any]], output_path: str, style: str = "modern") -> None:
        images = self.generate_floorplans(rooms, style)
        if images:
            images[0].save(output_path)
            print(f"✅ Denah disimpan di: {output_path}")