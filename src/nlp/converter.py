"""
src/nlp/converter.py
Konversi output decoder ke format ChatHouseDiffusion (CHD).
"""

def convert_to_chd_format(parsed: dict) -> dict:
    """
    Konversi dari format decoder (Pydantic) ke format ChatHouseDiffusion.
    
    Format input (parsed):
        {
            "rooms": [
                {
                    "name": "master room",
                    "type": "bedroom",
                    "size": {"width": 16.0, "height": 16.0},
                    "location": "middle...",
                    "links": ["living room", "balcony"]
                }
            ]
        }
    
    Format output (CHD):
        {
            "rooms": [
                {
                    "name": "master room",
                    "type": "bedroom",
                    "size": [16.0, 16.0],      # LIST, bukan dict!
                    "links": ["living room", "balcony"]
                }
            ]
        }
    """
    if 'rooms' not in parsed:
        raise ValueError("Input harus memiliki key 'rooms'")
    
    chd_rooms = []
    for room in parsed['rooms']:
        # 1. Ambil ukuran
        if 'size' in room:
            if isinstance(room['size'], dict):
                # Konversi dict → list [width, height]
                w = room['size'].get('width', 10.0)
                h = room['size'].get('height', 10.0)
                size_list = [float(w), float(h)]
            elif isinstance(room['size'], list):
                size_list = room['size']
            else:
                size_list = [10.0, 10.0]  # default
        else:
            size_list = [10.0, 10.0]  # default
        
        # 2. Ambil links (pastikan list)
        links = room.get('links', [])
        if not isinstance(links, list):
            links = []
        
        # 3. Bangun kamar untuk CHD
        chd_room = {
            'name': room.get('name', ''),
            'type': room.get('type', 'unknown'),
            'size': size_list,
            'links': links
        }
        chd_rooms.append(chd_room)
    
    return {"rooms": chd_rooms}