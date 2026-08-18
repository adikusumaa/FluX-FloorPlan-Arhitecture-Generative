# interface/backend/services/crew_service.py
import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

async def run_crew_workflow(user_text: str, weights: List[float], location: Dict[str, float]) -> Dict[str, Any]:
    """
    Fungsi ini akan dipanggil oleh routes.py.
    Di sini nanti kita akan memanggil CrewAI.
    Saat ini hanya placeholder untuk testing endpoint.
    """
    logger.info("CrewAI workflow started (placeholder)")
    
    # Simulasi delay (nanti diganti dengan panggilan crew)
    await asyncio.sleep(1)
    
    # Data dummy untuk testing
    dummy_data = {
        "data": [
            {
                "id": f"plan_{i}",
                "rank": i+1,
                "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "style": "RPLAN",
                "scores": {
                    "composite": 0.85 - i*0.05,
                    "spatial_openness": 0.8 - i*0.03,
                    "circulation_efficiency": 0.7 - i*0.04,
                    "layout_rationality": 0.9 - i*0.02,
                    "adaptability": 0.75 - i*0.05
                },
                "energy": {
                    "EUI": 45 + i*2,
                    "total_area": 120 + i*5,
                    "fire_safety_status": "OK"
                },
                "suggestions": {
                    "lighting": "Orientasikan ruang tamu ke selatan untuk pencahayaan optimal.",
                    "ventilation": "Buat bukaan di timur dan barat untuk cross-ventilation."
                },
                "rfpa": {
                    "stage1": {"compliant": True, "roomCounts": [1, 2, 1, 1, 1]},
                    "stage2": {"graphId": f"G-{i}", "editDistance": 0},
                    "stage3": {"quadrant": "Quadrant I"},
                    "stage4": {"rfp_iou": 0.85 - i*0.02}
                },
                "orientation": {
                    "livingRoom": "South",
                    "bedrooms": "North-East"
                },
                "location": location
            }
            for i in range(5)
        ],
        "parsed_data": {
            "rooms": {"living": 1, "bedroom": 2, "bathroom": 1, "kitchen": 1, "balcony": 1},
            "style": "modern"
        }
    }
    return dummy_data