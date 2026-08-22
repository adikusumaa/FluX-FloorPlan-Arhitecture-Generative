import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.workflow.agentic_refine import AgenticWorkflow

def run_test():
    mcp_url = "https://lather-resume-unadvised.ngrok-free.dev"
    
    target_rooms = [
        {"name": "living room", "category": "LivingRoom", "size": "L", "location": "center", "links": ["master room", "kitchen", "bathroom", "balcony", "second room"]},
        {"name": "master room", "category": "MasterRoom", "size": "M", "location": "north", "links": ["living room", "bathroom"]},
        {"name": "kitchen", "category": "Kitchen", "size": "M", "location": "east", "links": ["living room"]},
        {"name": "bathroom", "category": "Bathroom", "size": "S", "location": "west", "links": ["living room", "master room"]},
        {"name": "second room", "category": "SecondRoom", "size": "M", "location": "southwest", "links": ["living room"]},
        {"name": "balcony", "category": "Balcony", "size": "S", "location": "south", "links": ["living room"]}
    ]
    
    workflow = AgenticWorkflow(mcp_url=mcp_url)
    workflow.execute(target_rooms=target_rooms, output_prefix="test_output")

if __name__ == "__main__":
    run_test()