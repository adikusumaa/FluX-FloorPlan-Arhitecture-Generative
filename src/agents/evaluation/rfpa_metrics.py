import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from .graph_extractor import extract_graph_from_image

logger = logging.getLogger(__name__)

# ========== KONFIGURASI ==========
BEDROOM_GROUP = ["MasterRoom", "ChildRoom", "StudyRoom", "SecondRoom", "GuestRoom"]

CATEGORY_WEIGHTS = {
    "LivingRoom": 3.0,
    "Bedroom": 3.0,
    "Kitchen": 3.0,
    "Bathroom": 2.0,
    "DiningRoom": 1.5,
    "Balcony": 1.0,
    "Storage": 0.5,
    "CommonRoom": 1.0,
}

DEFAULT_COMPOSITE_WEIGHTS = {
    "stage1": 0.30,
    "stage2": 0.20,
    "stage3": 0.20,
    "stage4": 0.30,
}

GAP = 4
ALIGN_RANGE = 5


def normalize_category(category: str) -> str:
    if category in BEDROOM_GROUP:
        return "Bedroom"
    return category


# ======================================================================
# STAGE 1
# ======================================================================
def calculate_stage1_room_count(requested_rooms, detected_rooms, category_weights=None):
    weights = category_weights if category_weights is not None else CATEGORY_WEIGHTS
    requested_counts = {}
    detected_counts = {}

    for room in requested_rooms:
        cat = normalize_category(room.get("category", "Unknown"))
        requested_counts[cat] = requested_counts.get(cat, 0) + 1

    for room in detected_rooms:
        cat = normalize_category(room.get("category", "Unknown"))
        detected_counts[cat] = detected_counts.get(cat, 0) + 1

    all_cats = set(requested_counts.keys()) | set(detected_counts.keys())
    penalty = 0.0
    max_penalty = 0.0

    for cat in sorted(all_cats):
        req = requested_counts.get(cat, 0)
        det = detected_counts.get(cat, 0)
        w = weights.get(cat, 1.0)
        max_penalty += req * w

        if det < req:
            penalty += (req - det) * w
        elif det > req:
            penalty += (det - req) * w * 0.5

    score = max(0.0, 1.0 - penalty / max_penalty) if max_penalty > 0 else 1.0
    return {
        "requested_counts": requested_counts,
        "detected_counts": detected_counts,
        "penalty": penalty,
        "max_penalty": max_penalty,
        "score": score,
    }


# ======================================================================
# MATCHING REQUESTED -> DETECTED
# ======================================================================
def match_requested_to_detected(requested_rooms, detected_rooms):
    detected_by_cat = {}
    for idx, det in enumerate(detected_rooms):
        cat = normalize_category(det.get("category", "Unknown"))
        detected_by_cat.setdefault(cat, []).append(idx)

    used = set()
    mapping = {}

    for req_idx, req in enumerate(requested_rooms):
        cat = normalize_category(req.get("category", "Unknown"))
        candidates = [idx for idx in detected_by_cat.get(cat, []) if idx not in used]
        if not candidates:
            continue
        det_idx = candidates[0]
        mapping[req_idx] = det_idx
        used.add(det_idx)

    return mapping


# ======================================================================
# STAGE 2
# ======================================================================
def calculate_stage2_rfp_ged(requested_rooms, detected_rooms, adjacency_edges):
    name_to_req_idx = {room.get("name", ""): idx for idx, room in enumerate(requested_rooms)}

    ref_edges = []
    for i, room in enumerate(requested_rooms):
        for link in room.get("links", []):
            j = name_to_req_idx.get(link)
            if j is not None and i < j:
                ref_edges.append((i, j))

    # Asumsikan detected_rooms urutannya sama dengan graph extractor nodes (0..n-1)
    mapping = match_requested_to_detected(requested_rooms, detected_rooms)

    # Build mapping dari node extractor ke request idx (karena adjacency_edges memakai node index)
    node_to_req = {}
    for req_idx, det_idx in mapping.items():
        node_to_req[det_idx] = req_idx

    detected_adjacency_req = set()
    for a, b in adjacency_edges:
        ra = node_to_req.get(a)
        rb = node_to_req.get(b)
        if ra is not None and rb is not None:
            detected_adjacency_req.add((ra, rb))
            detected_adjacency_req.add((rb, ra))

    missing_door_cost = 0
    for (i, j) in ref_edges:
        if (i, j) not in detected_adjacency_req:
            missing_door_cost += 2

    # Extra wall edges: adjacency yang bukan door
    extra_wall_cost = 0
    ref_set = set(ref_edges)
    for (i, j) in detected_adjacency_req:
        if i < j and (i, j) not in ref_set:
            extra_wall_cost += 1

    cost = missing_door_cost + extra_wall_cost
    max_cost = max(2 * len(ref_edges) + extra_wall_cost, 1)
    score = max(0.0, 1.0 - cost / max_cost)

    return {
        "edit_distance": cost,
        "missing_door_cost": missing_door_cost,
        "extra_wall_cost": extra_wall_cost,
        "score": score,
    }


# ======================================================================
# STAGE 3
# ======================================================================
def get_quadrant_rotated(dx, dy):
    angle = np.pi / 4
    u = dx * np.cos(angle) - dy * np.sin(angle)
    v = dx * np.sin(angle) + dy * np.cos(angle)

    if u >= 0 and v < 0:
        return "north"
    elif u >= 0 and v >= 0:
        return "east"
    elif u < 0 and v >= 0:
        return "south"
    else:
        return "west"


def calculate_stage3_location_quadrant(requested_rooms, detected_rooms):
    mapping = match_requested_to_detected(requested_rooms, detected_rooms)

    living_centroid = None
    for det in detected_rooms:
        if normalize_category(det.get("category", "Unknown")) == "LivingRoom":
            living_centroid = det.get("centroid")
            break
    if living_centroid is None and detected_rooms:
        living_centroid = detected_rooms[0].get("centroid", (32, 32))
    elif living_centroid is None:
        living_centroid = (32, 32)

    total_checked = 0
    correct = 0

    for req_idx, req in enumerate(requested_rooms):
        req_loc = req.get("location", "Unknown")
        if req_loc not in ["north", "south", "east", "west"]:
            continue

        det_idx = mapping.get(req_idx)
        if det_idx is None or det_idx >= len(detected_rooms):
            continue

        det_centroid = detected_rooms[det_idx].get("centroid")
        if det_centroid is None:
            continue

        dx = det_centroid[0] - living_centroid[0]
        dy = det_centroid[1] - living_centroid[1]
        quadrant = get_quadrant_rotated(dx, dy)

        total_checked += 1
        if quadrant == req_loc:
            correct += 1

    score = (correct / total_checked) if total_checked > 0 else 1.0
    return {
        "total_checked": total_checked,
        "correct": correct,
        "score": score,
    }


# ======================================================================
# STAGE 4
# ======================================================================
def bbox_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[0] + box1[2], box2[0] + box2[2])
    y2 = min(box1[1] + box1[3], box2[1] + box2[3])

    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = box1[2] * box1[3]
    area2 = box2[2] * box2[3]
    union_area = area1 + area2 - inter_area
    return inter_area / union_area if union_area > 0 else 0.0


def build_expected_bbox(room, size_weights, living_size, gap=GAP):
    size = room.get("size", "M")
    s = size_weights.get(size, 16)
    location = room.get("location", "Unknown")

    cx = cy = 32
    if location == "north":
        cy = 32 - living_size // 2 - gap - s // 2
    elif location == "south":
        cy = 32 + living_size // 2 + gap + s // 2
    elif location == "east":
        cx = 32 + living_size // 2 + gap + s // 2
    elif location == "west":
        cx = 32 - living_size // 2 - gap - s // 2

    x = cx - s // 2
    y = cy - s // 2
    return (x, y, s, s)


def calculate_stage4_rfp_iou(requested_rooms, detected_rooms, size_weights, align_range=ALIGN_RANGE, gap=GAP):
    mapping = match_requested_to_detected(requested_rooms, detected_rooms)

    living_size = size_weights.get("M", 16)
    for req in requested_rooms:
        if normalize_category(req.get("category", "Unknown")) == "LivingRoom":
            living_size = size_weights.get(req.get("size", "M"), 16)
            break

    expected_boxes = [build_expected_bbox(req, size_weights, living_size, gap) for req in requested_rooms]

    best_total_iou = 0.0
    best_shift = (0, 0)

    for dx_shift in range(-align_range, align_range + 1):
        for dy_shift in range(-align_range, align_range + 1):
            total_iou = 0.0
            valid_count = 0

            for req_idx, expected_box in enumerate(expected_boxes):
                det_idx = mapping.get(req_idx)
                if det_idx is None:
                    continue
                det_bbox = detected_rooms[det_idx].get("bbox")
                if det_bbox is None:
                    continue

                shifted_box = (
                    det_bbox[0] + dx_shift,
                    det_bbox[1] + dy_shift,
                    det_bbox[2],
                    det_bbox[3],
                )
                iou = bbox_iou(expected_box, shifted_box)
                total_iou += iou
                valid_count += 1

            avg_iou = total_iou / valid_count if valid_count > 0 else 0.0
            if avg_iou > best_total_iou:
                best_total_iou = avg_iou
                best_shift = (dx_shift, dy_shift)

    return {
        "score": best_total_iou,
        "best_shift": best_shift,
    }


# ======================================================================
# COMPOSITE
# ======================================================================
def calculate_rfpa_metrics(analysis=None, requested_rooms=None, image_path=None,
                           size_weights=None, composite_weights=None):
    """
    Hitung semua stage dan composite score.
    """
    if size_weights is None:
        size_weights = {"XS": 10, "S": 12, "M": 16, "L": 20, "XL": 26}
    if composite_weights is None:
        composite_weights = DEFAULT_COMPOSITE_WEIGHTS

    # Gunakan graph extractor sebagai sumber utama detected_rooms
    if image_path is not None:
        graph_rooms, adjacency_edges = extract_graph_from_image(image_path)
        detected_rooms = graph_rooms
    elif analysis is not None:
        detected_rooms = analysis.get("detected_rooms", [])
        adjacency_edges = []  # tidak tersedia
    else:
        detected_rooms = []
        adjacency_edges = []

    stage1 = calculate_stage1_room_count(requested_rooms, detected_rooms)
    stage2 = calculate_stage2_rfp_ged(requested_rooms, detected_rooms, adjacency_edges) if adjacency_edges else {"score": 0.0, "edit_distance": -1}
    stage3 = calculate_stage3_location_quadrant(requested_rooms, detected_rooms)
    stage4 = calculate_stage4_rfp_iou(requested_rooms, detected_rooms, size_weights)

    composite = (
        composite_weights.get("stage1", 0.30) * stage1.get("score", 0.0)
        + composite_weights.get("stage2", 0.20) * stage2.get("score", 0.0)
        + composite_weights.get("stage3", 0.20) * stage3.get("score", 0.0)
        + composite_weights.get("stage4", 0.30) * stage4.get("score", 0.0)
    )
    composite = max(0.0, min(1.0, composite))

    return {
        "stage1_room_count": stage1,
        "stage2_rfp_ged": stage2,
        "stage3_location_quadrant": stage3,
        "stage4_rfp_iou": stage4,
        "composite_score": composite,
    }