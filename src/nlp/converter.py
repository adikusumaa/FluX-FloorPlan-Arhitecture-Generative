"""
src/nlp/converter.py
Konversi output decoder (FloorPlanRequest) ke format yang diterima server ChatHouseDiffusion.
Output: list of dict dengan key: name, category, size, location, links.
"""

import re
from typing import List, Dict, Any, Union

# Pemetaan tipe ruangan ke kategori model CHD
TYPE_TO_CATEGORY = {
    "bedroom": "MasterRoom",
    "bathroom": "Bathroom",
    "living_room": "LivingRoom",
    "kitchen": "Kitchen",
    "balcony": "Balcony",
    "dining_room": "DiningRoom",
    "common_room": "LivingRoom",  # <-- PERUBAHAN: map common_room ke LivingRoom
    "storage": "Storage",
    "study_room": "StudyRoom",
    "child_room": "ChildRoom",
    "guest_room": "GuestRoom",
    "entrance": "Entrance",
    "second_room": "SecondRoom",
}

SIZE_THRESHOLDS = [
    (300, "XL"),
    (200, "L"),
    (100, "M"),
    (50, "S"),
    (0, "XS"),
]

def _area_to_size(area: float) -> str:
    for threshold, size in SIZE_THRESHOLDS:
        if area > threshold:
            return size
    return "XS"

def _normalize_size(size) -> str:
    if isinstance(size, dict):
        w = float(size.get("width", 10))
        h = float(size.get("height", 10))
        return _area_to_size(w * h)
    elif isinstance(size, (list, tuple)) and len(size) == 2:
        w = float(size[0]); h = float(size[1])
        return _area_to_size(w * h)
    elif isinstance(size, str):
        if size in {"XS", "S", "M", "L", "XL"}:
            return size
        if "x" in size:
            try:
                w, h = map(float, size.lower().split("x"))
                return _area_to_size(w * h)
            except:
                pass
        return "M"
    return "M"

def _extract_direction(location_text: str) -> str:
    if not location_text or location_text.lower() == "unknown":
        return "center"
    text = location_text.lower()
    dirs = []
    if "north" in text: dirs.append("north")
    if "south" in text: dirs.append("south")
    if "east" in text: dirs.append("east")
    if "west" in text: dirs.append("west")
    if "center" in text or "middle" in text:
        if not dirs:
            return "center"
    if not dirs:
        return "center"
    if len(dirs) == 1:
        return dirs[0]
    vertical = [d for d in dirs if d in ("north", "south")]
    horizontal = [d for d in dirs if d in ("east", "west")]
    if vertical and horizontal:
        return vertical[0] + horizontal[0]
    return dirs[0] + dirs[1] if len(dirs) >= 2 else dirs[0]

def _build_links(rooms: list, room_name: str) -> list:
    if not rooms:
        return []
    living = next((r for r in rooms if r.get("type") == "living_room" or r.get("category") == "LivingRoom"), None)
    if living and living.get("name") != room_name:
        return [living["name"]]
    first = next((r for r in rooms if r.get("name") != room_name), None)
    return [first["name"]] if first else []

def convert_to_chd_format(parsed: Union[dict, list]) -> List[Dict[str, Any]]:
    if isinstance(parsed, dict):
        if 'rooms' not in parsed:
            raise ValueError("Input harus memiliki key 'rooms'")
        raw_rooms = parsed['rooms']
    elif isinstance(parsed, list):
        raw_rooms = parsed
    else:
        raise TypeError("Input harus dict atau list")

    converted = []
    for room in raw_rooms:
        if hasattr(room, 'model_dump'):
            room = room.model_dump()

        name = room.get('name', 'Unknown')
        type_ = room.get('type', 'unknown')
        category = room.get('category', TYPE_TO_CATEGORY.get(type_, 'LivingRoom'))  # fallback ke LivingRoom
        size = _normalize_size(room.get('size', 'M'))
        location = _extract_direction(room.get('location', 'center'))
        links = room.get('links', [])

        if not links:
            links = _build_links(raw_rooms, name)

        if not isinstance(links, list):
            links = []
        links = [str(l) for l in links if l]

        converted.append({
            'name': name,
            'category': category,
            'size': size,
            'location': location,
            'links': links,
        })

    return converted