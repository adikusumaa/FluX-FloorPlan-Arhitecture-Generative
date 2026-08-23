import requests
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/mcp/tools/generate_floorplans"
        logger.info(f"[MCP_CLIENT] Initialized with endpoint: {self.endpoint}")

    def generate_floorplan(
        self,
        rooms: List[Dict],
        mask_template: int = 0,
        cond_scale: float = 1.5,
        custom_mask: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send generation request to ChatHouseDiffusion server.

        Args:
            rooms: List of room dicts with keys: name, category, size, location, links.
            mask_template: Template index for mask (0-9).
            cond_scale: Conditioning scale.
            custom_mask: Optional custom mask string.

        Returns:
            Dict with 'status', 'data' (list of base64 images), and optional 'meta'.
        """
        payload = {
            "rooms": rooms,
            "style": "modern",
            "mask_template": mask_template,
            "cond_scale": cond_scale
        }
        if custom_mask:
            payload["custom_mask"] = custom_mask

        headers = {"Content-Type": "application/json"}

        # Log input payload (truncate if too long)
        payload_str = json.dumps(payload, indent=2)
        logger.debug(f"[MCP_CLIENT] Request payload: {payload_str[:1000]}...")

        try:
            response = requests.post(
                self.endpoint,
                data=json.dumps(payload),
                headers=headers,
                timeout=120
            )
            response.raise_for_status()

            # Parse response
            result = response.json()
            logger.info(f"[MCP_CLIENT] Raw response keys: {list(result.keys())}")

            # Normalize response: support different key names
            if "data" in result and isinstance(result["data"], list):
                images = result["data"]
            elif "images" in result and isinstance(result["images"], list):
                images = result["images"]
            elif isinstance(result, list):
                # If response is directly a list of images
                images = result
                result = {"data": images}
            else:
                # Try to find any list value in response
                images = None
                for key, value in result.items():
                    if isinstance(value, list) and len(value) > 0:
                        images = value
                        break
                if images is None:
                    images = []

            # Ensure 'data' key exists
            if "data" not in result:
                result["data"] = images

            logger.info(f"[MCP_CLIENT] Extracted {len(images)} images from response.")

            if len(images) == 0:
                logger.warning("[MCP_CLIENT] No images received. Response content may be empty or malformed.")
                logger.warning(f"[MCP_CLIENT] Full response: {json.dumps(result, indent=2)[:500]}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"[MCP_CLIENT] Request failed: {str(e)}")
            return {"status": "error", "message": str(e), "data": []}
        except json.JSONDecodeError as e:
            logger.error(f"[MCP_CLIENT] Invalid JSON response: {str(e)}")
            return {"status": "error", "message": "Invalid JSON response", "data": []}