"""
Ekstraksi adjacency graph dari gambar floor plan hasil generate.

Proses:
1. Deteksi ruangan per warna (menggunakan connected components).
2. Dilatasi mask tiap ruangan untuk mendeteksi sentuhan/kedekatan.
3. Menghasilkan daftar edge adjacency (wall connection).
"""

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


def extract_rooms_from_image(image_path: str, min_area: int = MIN_AREA) -> List[Dict]:
    """
    Mendeteksi ruangan dari gambar RGB floor plan.

    Returns:
        List of room dicts:
        {
            "index": int,
            "category": str,
            "mask": np.ndarray (64x64 uint8),
            "bbox": (x, y, w, h),
            "centroid": (cx, cy),
            "area": int
        }
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        logger.error(f"Gagal membaca gambar: {image_path}")
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
    """
    Mendeteksi adjacency antar ruangan berdasarkan overlap mask setelah dilatasi.

    Returns:
        List of edge tuples: (room_idx_a, room_idx_b)
    """
    if dilation_kernel is None:
        dilation_kernel = DILATE_KERNEL

    edges = []
    n = len(rooms)

    # Dilate masks once for efficiency
    dilated_masks = []
    for room in rooms:
        dilated = cv2.dilate(room["mask"], dilation_kernel, iterations=1)
        dilated_masks.append(dilated)

    for i in range(n):
        for j in range(i + 1, n):
            overlap = cv2.bitwise_and(dilated_masks[i], dilated_masks[j])
            if cv2.countNonZero(overlap) > 0:
                edges.append((rooms[i]["index"], rooms[j]["index"]))

    return edges


def extract_graph_from_image(image_path: str, min_area: int = MIN_AREA) -> Tuple[List[Dict], List[Tuple[int, int]]]:
    """
    Wrapper: return rooms dan adjacency edges dari gambar.
    """
    rooms = extract_rooms_from_image(image_path, min_area)
    edges = extract_adjacency_from_rooms(rooms)
    logger.info(f"Graph extractor: {len(rooms)} rooms, {len(edges)} adjacency edges")
    return rooms, edges