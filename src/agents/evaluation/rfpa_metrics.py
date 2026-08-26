import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

COLOR_MAP = {
    "LivingRoom": [238, 232, 170],
    "MasterRoom": [255, 165, 0],
    "Kitchen": [240, 128, 128],
    "Bathroom": [173, 216, 210],
    "Balcony": [107, 142, 35],
    "DiningRoom": [218, 112, 214],
    "Storage": [221, 160, 221],
    "CommonRoom": [255, 215, 0],
}

MIN_AREA = 40
DILATE_KERNEL = np.ones((3, 3), np.uint8)

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

def normalize_category(category: str) -> str:
    if category in BEDROOM_GROUP:
        return "Bedroom"
    return category

def extract_rooms_from_image(image_path: str, min_area: int = MIN_AREA) -> List[Dict]:
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        logger.error(f"Failed to read image: {image_path}")
        return []

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    rooms = []
    index_counter = 0

    for category, color in COLOR_MAP.items():
        lower = np.array(color, dtype=np.uint8)
        upper = np.array(color, dtype=np.uint8)
        mask = cv2.inRange(img_rgb, lower, upper)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=4)

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < min_area:
                continue

            x, y, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], \
                         stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            cx, cy = int(centroids[i][0]), int(centroids[i][1])

            room_mask = np.zeros_like(mask)
            room_mask[labels == i] = 255

            rooms.append({
                "index": index_counter,
                "category": category,
                "mask": room_mask,
                "bbox": (x, y, w, h),
                "centroid": (cx, cy),
                "area": int(area),
            })
            index_counter += 1

    return rooms

def extract_adjacency_from_rooms(rooms: List[Dict], dilation_kernel: Optional[np.ndarray] = None) -> List[Tuple[int, int]]:
    if dilation_kernel is None:
        dilation_kernel = DILATE_KERNEL

    edges = []
    n = len(rooms)
    dilated_masks = [cv2.dilate(room["mask"], dilation_kernel, iterations=2) for room in rooms]

    for i in range(n):
        for j in range(i + 1, n):
            overlap = cv2.bitwise_and(dilated_masks[i], dilated_masks[j])
            if cv2.countNonZero(overlap) > 0:
                edges.append((rooms[i]["index"], rooms[j]["index"]))

    return edges

def extract_graph_from_image(image_path: str, min_area: int = MIN_AREA) -> Tuple[List[Dict], List[Tuple[int, int]]]:
    rooms = extract_rooms_from_image(image_path, min_area)
    edges = extract_adjacency_from_rooms(rooms)
    logger.info(f"Graph extractor: {len(rooms)} rooms, {len(edges)} adjacency edges")
    return rooms, edges

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

def calculate_stage2_rfp_ged(requested_rooms, detected_rooms, adjacency_edges):
    name_to_req_idx = {room.get("name", ""): idx for idx, room in enumerate(requested_rooms)}

    ref_edges = []
    for i, room in enumerate(requested_rooms):
        for link in room.get("links", []):
            j = name_to_req_idx.get(link)
            if j is not None and i < j:
                ref_edges.append((i, j))

    mapping = match_requested_to_detected(requested_rooms, detected_rooms)
    node_to_req = {det_idx: req_idx for req_idx, det_idx in mapping.items()}

    detected_adjacency_req = set()
    for a, b in adjacency_edges:
        ra = node_to_req.get(a)
        rb = node_to_req.get(b)
        if ra is not None and rb is not None:
            if ra < rb:
                detected_adjacency_req.add((ra, rb))
            else:
                detected_adjacency_req.add((rb, ra))

    missing_edge_cost = 0
    ref_set = set(ref_edges)
    for edge in ref_set:
        if edge not in detected_adjacency_req:
            missing_edge_cost += 1

    extra_edge_cost = 0
    for edge in detected_adjacency_req:
        if edge not in ref_set:
            extra_edge_cost += 1

    cost = missing_edge_cost + extra_edge_cost
    max_cost = max(len(ref_set) + extra_edge_cost, 1)
    score = max(0.0, 1.0 - cost / max_cost)

    return {
        "edit_distance": cost,
        "missing_edge_cost": missing_edge_cost,
        "extra_edge_cost": extra_edge_cost,
        "score": score,
    }

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

def generate_expected_mask(room, size_weights):
    size = room.get("size", "M")
    s = size_weights.get(size, 16)
    mask = np.zeros((64, 64), dtype=np.uint8)
    
    cx, cy = 32, 32
    x1 = max(0, cx - s // 2)
    y1 = max(0, cy - s // 2)
    x2 = min(64, cx + s // 2)
    y2 = min(64, cy + s // 2)
    
    cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
    return mask

def shift_mask(mask, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    shifted = cv2.warpAffine(mask, M, (mask.shape[1], mask.shape[0]))
    return shifted

def calculate_stage4_rfp_iou(requested_rooms, detected_rooms, size_weights):
    mapping = match_requested_to_detected(requested_rooms, detected_rooms)
    
    total_iou = 0.0
    valid_count = 0
    
    for req_idx, req in enumerate(requested_rooms):
        det_idx = mapping.get(req_idx)
        if det_idx is None:
            continue
            
        det_room = detected_rooms[det_idx]
        det_mask = det_room.get("mask")
        if det_mask is None:
            continue
            
        exp_mask = generate_expected_mask(req, size_weights)
        
        exp_coords = cv2.findNonZero(exp_mask)
        det_coords = cv2.findNonZero(det_mask)
        
        if exp_coords is None or det_coords is None:
            continue
            
        exp_coords = exp_coords.reshape(-1, 2)
        det_coords = det_coords.reshape(-1, 2)
        
        exp_cx = int(np.mean(exp_coords[:, 0]))
        exp_cy = int(np.mean(exp_coords[:, 1]))
        
        det_cx = int(np.mean(det_coords[:, 0]))
        det_cy = int(np.mean(det_coords[:, 1]))
        
        dx = exp_cx - det_cx
        dy = exp_cy - det_cy
        
        aligned_det_mask = shift_mask(det_mask, dx, dy)
        
        intersection = cv2.bitwise_and(exp_mask, aligned_det_mask)
        union = cv2.bitwise_or(exp_mask, aligned_det_mask)
        
        inter_area = cv2.countNonZero(intersection)
        union_area = cv2.countNonZero(union)
        
        iou = inter_area / union_area if union_area > 0 else 0.0
        total_iou += iou
        valid_count += 1
        
    score = total_iou / valid_count if valid_count > 0 else 0.0
    return {
        "score": score
    }

def calculate_rfpa_metrics(analysis=None, requested_rooms=None, image_path=None,
                           size_weights=None, composite_weights=None):
    if size_weights is None:
        size_weights = {"XS": 10, "S": 12, "M": 16, "L": 20, "XL": 26}
    if composite_weights is None:
        composite_weights = DEFAULT_COMPOSITE_WEIGHTS

    if image_path is not None:
        graph_rooms, adjacency_edges = extract_graph_from_image(image_path)
        detected_rooms = graph_rooms
    elif analysis is not None:
        detected_rooms = analysis.get("detected_rooms", [])
        adjacency_edges = []
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