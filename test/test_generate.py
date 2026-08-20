# test/test_generate.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.client.mcp_client import ChatHouseClient

if __name__ == "__main__":
    client = ChatHouseClient()

    # ============================================================
    # GUNAKAN ROOMS DENGAN UKURAN BERVARIASI
    # ============================================================
    rooms = [
        {"name": "living room", "type": "living_room", "size": {"width": 20, "height": 18}, "links": ["kitchen"]},
        {"name": "kitchen", "type": "kitchen", "size": {"width": 10, "height": 8}, "links": ["living room"]},
        {"name": "master room", "type": "bedroom", "size": {"width": 16, "height": 16}, "links": ["living room"]},
    ]

    output = "floorplan_result.png"
    client.save(rooms, output, style="modern")