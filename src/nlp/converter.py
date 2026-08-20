"""
src/nlp/converter.py
Konversi output decoder ke format ChatHouseDiffusion (CHD).
"""

def convert_to_chd_format(parsed: dict) -> dict:
    """
    Konversi dari format decoder (Pydantic) ke format ChatHouseDiffusion.
    Format input (parsed) memiliki 'rooms' dengan size dict: {'width': w, 'height': h}
    Format output: size menjadi string "WxH" (contoh "16x16")
    """
    if 'rooms' not in parsed:
        raise ValueError("Input harus memiliki key 'rooms'")
    
    chd_rooms = []
    for room in parsed['rooms']:
        # Ambil size
        size = room.get('size', {})
        if isinstance(size, dict):
            w = size.get('width', 10)
            h = size.get('height', 10)
            size_str = f"{w}x{h}"
        elif isinstance(size, list):
            w, h = size[0], size[1]
            size_str = f"{w}x{h}"
        else:
            size_str = str(size)  # jika sudah string, biarkan
        
        # Ambil links
        links = room.get('links', [])
        if not isinstance(links, list):
            links = []
        
        chd_room = {
            'name': room.get('name', ''),
            'type': room.get('type', 'unknown'),
            'size': size_str,  # string "WxH"
            'links': links
        }
        chd_rooms.append(chd_room)
    
    return {"rooms": chd_rooms}