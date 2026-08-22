import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.workflow.agentic_refine import AgenticWorkflow

def run_test():
    mcp_url = "https://lather-resume-unadvised.ngrok-free.dev"
    
    target_rooms = [
        {"name": "living room", "category": "LivingRoom", "size": "L", "location": "south", "links": ["dinning room", "kitchen", "bathroom"]},
        {"name": "master room", "category": "MasterRoom", "size": "M", "location": "east", "links": ["living room", "bathroom"]},
        {"name": "dinning room", "category": "DinningRoom", "size": "M", "location": "center", "links": ["living room", "kitchen", "storage"]},
        {"name": "kitchen", "category": "Kitchen", "size": "S", "location": "north", "links": ["dinning room", "storage"]},
        {"name": "bathroom", "category": "Bathroom", "size": "S", "location": "west", "links": ["master room", "living room"]},
        {"name": "storage room", "category": "Storage", "size": "XS", "location": "northwest", "links": ["kitchen", "bathroom"]}
    ]
    
    workflow = AgenticWorkflow(mcp_url=mcp_url)
    workflow.execute(target_rooms=target_rooms, output_prefix="test_output_variant_b")

if __name__ == "__main__":
    run_test()