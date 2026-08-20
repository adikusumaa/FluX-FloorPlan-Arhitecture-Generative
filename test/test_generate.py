import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='[INFO] %(message)s')

def test_generation():
    url = "https://lather-resume-unadvised.ngrok-free.dev/mcp/tools/generate_floorplans"
    
    payload = {
        "rooms": [
            {
                "name": "living room",
                "category": "LivingRoom",
                "size": "L",
                "location": "center",
                "links": ["master room", "kitchen", "bathroom", "balcony", "second room"]
            },
            {
                "name": "master room",
                "category": "MasterRoom",
                "size": "M",
                "location": "north",
                "links": ["living room", "bathroom"]
            },
            {
                "name": "kitchen",
                "category": "Kitchen",
                "size": "M",
                "location": "east",
                "links": ["living room"]
            },
            {
                "name": "bathroom",
                "category": "Bathroom",
                "size": "S",
                "location": "west",
                "links": ["living room", "master room"]
            },
            {
                "name": "second room",
                "category": "SecondRoom",
                "size": "M",
                "location": "southwest",
                "links": ["living room"]
            },
            {
                "name": "balcony",
                "category": "Balcony",
                "size": "S",
                "location": "south",
                "links": ["living room"]
            }
        ],
        "style": "modern",
        "mask_template": 0,
        "cond_scale": 1.5,
        "iterations": 1
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    logging.info(f"Sending request to: {url}")
    
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=120)
    
    if response.status_code == 200:
        logging.info("Response generated successfully")
        
        response_data = response.json()
        if "images" in response_data and len(response_data["images"]) > 0:
            import base64
            img_data = response_data["images"][0].split(",")[1]
            with open("floorplan_optimized.png", "wb") as fh:
                fh.write(base64.b64decode(img_data))
            logging.info("Image saved as floorplan_optimized.png")
    else:
        logging.error(f"Failed with status code: {response.status_code}")
        logging.error(response.text)

if __name__ == "__main__":
    test_generation()