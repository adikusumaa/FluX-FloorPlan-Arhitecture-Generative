import requests
import json
import logging
import base64
import os
from analyzer import FloorplanAnalyzer

logging.basicConfig(level=logging.INFO, format='[AGENT] %(message)s')

def execute_agentic_workflow():
    url = "https://lather-resume-unadvised.ngrok-free.dev/mcp/tools/generate_floorplans"
    
    base_rooms = [
        {"name": "living room", "category": "LivingRoom", "size": "L", "location": "center", "links": ["master room", "kitchen", "bathroom", "balcony", "second room"]},
        {"name": "master room", "category": "MasterRoom", "size": "M", "location": "north", "links": ["living room", "bathroom"]},
        {"name": "kitchen", "category": "Kitchen", "size": "M", "location": "east", "links": ["living room"]},
        {"name": "bathroom", "category": "Bathroom", "size": "S", "location": "west", "links": ["living room", "master room"]},
        {"name": "second room", "category": "SecondRoom", "size": "M", "location": "southwest", "links": ["living room"]},
        {"name": "balcony", "category": "Balcony", "size": "S", "location": "south", "links": ["living room"]}
    ]
    
    headers = {"Content-Type": "application/json"}
    analyzer = FloorplanAnalyzer()
    custom_mask_b64 = None

    for iteration in range(5):
        logging.info(f"--- Starting Iteration {iteration} ---")
        
        payload = {
            "rooms": base_rooms,
            "style": "modern",
            "mask_template": 0,
            "cond_scale": 1.5,
            "iterations": 1
        }
        
        if custom_mask_b64:
            payload["custom_mask"] = custom_mask_b64

        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=120)
        
        if response.status_code == 200:
            response_data = response.json()
            if "images" in response_data and len(response_data["images"]) > 0:
                img_data = response_data["images"][0].split(",")[1]
                output_filename = f"floorplan_iter_{iteration}.png"
                
                with open(output_filename, "wb") as fh:
                    fh.write(base64.b64decode(img_data))
                logging.info(f"Image saved: {output_filename}")
                
                spatial_data = analyzer.analyze_image(output_filename)
                custom_mask_b64 = analyzer.create_tight_mask_base64(spatial_data)
                logging.info("Tight mask generated for next iteration.")
        else:
            logging.error(f"Failed at iteration {iteration}: {response.status_code}")
            logging.error(response.text)
            break

if __name__ == "__main__":
    execute_agentic_workflow()