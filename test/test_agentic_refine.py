import sys
import os

# Tambahkan root project ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.workflow.agentic_refine import AgenticWorkflow

def run_test():
    mcp_url = "https://lather-resume-unadvised.ngrok-free.dev"
    
    # ============================================================
    # TARGET ROOMS sesuai output converter Anda
    # ============================================================
    target_rooms = [
        {
            "name": "master bedroom",
            "category": "MasterRoom",
            "size": "S",
            "location": "Unknown",
            "links": ["living room"]
        },
        {
            "name": "bathroom 1",
            "category": "Bathroom",
            "size": "S",
            "location": "north",
            "links": ["living room"]
        },
        {
            "name": "bathroom 2",
            "category": "Bathroom",
            "size": "S",
            "location": "north",
            "links": ["living room"]
        },
        {
            "name": "living room",
            "category": "LivingRoom",
            "size": "S",
            "location": "Unknown",
            "links": ["master bedroom"]
        },
        {
            "name": "kitchen",
            "category": "Kitchen",
            "size": "S",
            "location": "northeast",
            "links": ["living room"]
        },
        {
            "name": "balcony",
            "category": "Balcony",
            "size": "S",
            "location": "southeast",
            "links": ["living room"]
        },
        {
            "name": "common room",
            "category": "Unknown",
            "size": "S",
            "location": "Unknown",
            "links": ["living room"]
        }
    ]
    
    workflow = AgenticWorkflow(mcp_url=mcp_url)
    workflow.execute(target_rooms=target_rooms, output_prefix="test_output_variant_b")

if __name__ == "__main__":
    run_test()