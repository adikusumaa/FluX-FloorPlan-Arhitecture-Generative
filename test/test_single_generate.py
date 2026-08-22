"""
test/test_single_generate.py
Test satu kali generate dan analisis (tanpa iterasi).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.client.mcp_client import ChatHouseClient
from src.agents.vision.floorplan_analyzer import FloorplanAnalyzer

if __name__ == "__main__":
    client = ChatHouseClient()
    analyzer = FloorplanAnalyzer()

    rooms = [
        {"name": "living room", "category": "LivingRoom", "size": "L", "location": "center", "links": ["master room", "kitchen", "bathroom", "balcony", "second room"]},
        {"name": "master room", "category": "MasterRoom", "size": "M", "location": "north", "links": ["living room", "bathroom"]},
        {"name": "kitchen", "category": "Kitchen", "size": "M", "location": "east", "links": ["living room"]},
        {"name": "bathroom", "category": "Bathroom", "size": "S", "location": "west", "links": ["living room", "master room"]},
        {"name": "second room", "category": "SecondRoom", "size": "M", "location": "southwest", "links": ["living room"]},
        {"name": "balcony", "category": "Balcony", "size": "S", "location": "south", "links": ["living room"]}
    ]

    image = client.generate_floorplan(rooms, mask_template=0, cond_scale=1.0)
    output = "single_result.png"
    image.save(output)
    print(f"Image saved: {output}")

    analysis = analyzer.analyze(image, rooms)
    print("Analysis:", analysis)