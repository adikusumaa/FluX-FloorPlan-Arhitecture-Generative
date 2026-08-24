import sys
import os
import logging
import json
import traceback
import uuid
import base64
import tempfile
from typing import Dict, Any, List, Optional

import cv2
import numpy as np
from PIL import Image

# Tambahkan root proyek ke sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.mcp.client.encoder_client import encode_text
from src.nlp.decoder import validate_and_parse, DecoderError, MalformedJSONError, ValidationErrorDetail
from src.agents.workflow.agentic_refine import AgenticWorkflow
from src.mcp.client.mcp_client import MCPClient

logger = logging.getLogger(__name__)


class FloorPlanGenerationError(Exception):
    pass


def generate_floorplans(
    user_text: str,
    weights: Optional[List[float]] = None,
    location: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    logger.info("[PIPELINE] Starting floor plan generation process with AgenticWorkflow.")

    # ------------------------------------------------------------
    # STEP 1: ENCODER
    # ------------------------------------------------------------
    try:
        encoder_url = os.getenv("ENCODER_URL")
        if not encoder_url:
            raise FloorPlanGenerationError("[ENCODER] ENCODER_URL not set in .env")
        logger.info(f"[ENCODER] Request to {encoder_url}/encode_detailed")
        logger.info(f"[ENCODER] Payload length: {len(user_text)} characters")
        detailed_room_json = encode_text(user_text)
        if not isinstance(detailed_room_json, dict):
            raise FloorPlanGenerationError(f"[ENCODER] Invalid response type: {type(detailed_room_json)}")
        room_count = len(detailed_room_json.get("rooms", []))
        logger.info(f"[ENCODER] Extraction completed. Rooms found: {room_count}")
    except Exception as e:
        logger.error(f"[ENCODER] Failed: {e}\n{traceback.format_exc()}")
        raise FloorPlanGenerationError(f"[ENCODER] {str(e)}") from e

    # ------------------------------------------------------------
    # STEP 2: DECODER
    # ------------------------------------------------------------
    try:
        logger.info("[DECODER] Validating JSON against Pydantic schema.")
        validated_request = validate_and_parse(detailed_room_json)
        total_area = validated_request.get_total_area()
        room_counts = validated_request.get_room_counts()
        logger.info(
            f"[DECODER] Validation OK. Rooms: {len(validated_request.rooms)}, "
            f"Area: {total_area:.2f} sqft, Counts: {room_counts}"
        )
    except (MalformedJSONError, ValidationErrorDetail, DecoderError) as e:
        logger.error(f"[DECODER] Validation failed: {e}")
        raise FloorPlanGenerationError(f"[DECODER] {str(e)}") from e
    except Exception as e:
        logger.error(f"[DECODER] Unexpected error: {e}\n{traceback.format_exc()}")
        raise FloorPlanGenerationError(f"[DECODER] {str(e)}") from e

    # ------------------------------------------------------------
    # STEP 3: CONVERTER
    # ------------------------------------------------------------
    try:
        logger.info("[CONVERTER] Converting to CHD format.")
        chd_rooms = validated_request.to_chd_format()
        if not isinstance(chd_rooms, list):
            raise FloorPlanGenerationError(f"[CONVERTER] Expected list, got {type(chd_rooms)}")
        logger.info(f"[CONVERTER] Conversion OK. {len(chd_rooms)} room entries.")
        logger.info("[CONVERTER] CHD input structure:\n" + json.dumps(chd_rooms, indent=2))
    except Exception as e:
        logger.error(f"[CONVERTER] Failed: {e}\n{traceback.format_exc()}")
        raise FloorPlanGenerationError(f"[CONVERTER] {str(e)}") from e

    # ------------------------------------------------------------
    # STEP 4: GENERATE + POST‑PROCESS + UPSCALE
    # ------------------------------------------------------------
    try:
        chd_base_url = os.getenv("CHATHOUSE_URL")
        if not chd_base_url:
            raise FloorPlanGenerationError("[MCP_CLIENT] CHATHOUSE_URL not set in .env")

        logger.info(f"[MCP_CLIENT] Initializing AgenticWorkflow at {chd_base_url}")
        workflow = AgenticWorkflow(mcp_url=chd_base_url)

        # 4a. Topological mask
        logger.info("[MCP_CLIENT] Generating topological mask from room layout.")
        custom_mask_b64 = workflow.generate_topological_mask(chd_rooms)
        logger.info("[MCP_CLIENT] Topological mask generated successfully.")

        # 4b. Generate
        client = MCPClient(base_url=chd_base_url)
        cond_scale = 1.5
        logger.info(f"[MCP_CLIENT] Sending generation request with custom_mask. Rooms: {len(chd_rooms)}, cond_scale: {cond_scale}")
        generation_result = client.generate_floorplan(
            rooms=chd_rooms,
            cond_scale=cond_scale,
            custom_mask=custom_mask_b64
        )

        # 4c. Extract image
        images = generation_result.get("data") or generation_result.get("images", [])
        if not images or not isinstance(images, list) or len(images) == 0:
            raise FloorPlanGenerationError("[MCP_CLIENT] No images received from CHD server.")
        raw_image = images[0]
        if isinstance(raw_image, str) and raw_image.startswith("data:image"):
            raw_image = raw_image.split(",")[1]

        logger.info("[MCP_CLIENT] Raw image retrieved successfully.")

        # 4d. Save temporary
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(base64.b64decode(raw_image))
        logger.info(f"[POST-PROCESS] Temporary image saved to {tmp_path}")

        # 4e. Reconstruction
        logger.info("[POST-PROCESS] Starting reconstruction and analysis.")
        workflow.apply_reconstruction(tmp_path)
        logger.info("[POST-PROCESS] Reconstruction completed.")

        # 4f. Analysis (optional)
        analysis = workflow.analyzer.analyze(tmp_path, chd_rooms)
        logger.info(
            f"[POST-PROCESS] Analysis: missing_count={analysis.get('missing_count', 0)}, "
            f"location_errors={analysis.get('location_errors', 0)}"
        )

        # ============================================================
        # 4g. UPSCALE dengan NEAREST NEIGHBOR (tajam, tidak buram)
        # ============================================================
        logger.info("[POST-PROCESS] Upscaling image with NEAREST interpolation (sharp edges).")
        img = cv2.imread(tmp_path)
        if img is None:
            raise FloorPlanGenerationError("[POST-PROCESS] Failed to read reconstructed image for upscaling.")

        h, w = img.shape[:2]
        scale_factor = 8  # 64x64 -> 512x512
        new_w, new_h = w * scale_factor, h * scale_factor

        # Gunakan INTER_NEAREST untuk pixel-art sharp
        img_hd = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(tmp_path, img_hd)
        logger.info(f"[POST-PROCESS] Upscaled to {new_w}x{new_h} using NEAREST.")

        # 4h. (Opsional) Set DPI metadata ke 300 menggunakan PIL
        # Ini hanya metadata, tidak memengaruhi tampilan web, tapi bagus untuk cetak.
        with Image.open(tmp_path) as pil_img:
            pil_img.save(tmp_path, dpi=(300, 300))
        logger.info("[POST-PROCESS] DPI metadata set to 300.")

        # 4i. Baca dan encode base64
        with open(tmp_path, "rb") as f:
            reconstructed_b64 = base64.b64encode(f.read()).decode('utf-8')

        # 4j. Clean up
        os.unlink(tmp_path)
        logger.info("[POST-PROCESS] Temporary file cleaned up.")

        # 4k. Siapkan response
        image_url = f"data:image/png;base64,{reconstructed_b64}"
        floor_plan = {
            "id": str(uuid.uuid4()),
            "image_url": image_url,
            "scores": {},
            "rank": 1
        }

    except Exception as e:
        logger.error(f"[MCP_CLIENT] Generation or post-processing failed: {e}\n{traceback.format_exc()}")
        raise FloorPlanGenerationError(f"[MCP_CLIENT] {str(e)}") from e

    # ------------------------------------------------------------
    # STEP 5: FINAL RESPONSE
    # ------------------------------------------------------------
    try:
        logger.info("[PIPELINE] Assembling final response.")
        final_response = {
            "data": [floor_plan],
            "parsed_data": {
                "validated_rooms": validated_request.model_dump(),
                "chd_format": chd_rooms,
                "total_area_sqft": validated_request.get_total_area(),
                "room_counts": validated_request.get_room_counts(),
                "generation_meta": generation_result.get("meta", {}),
                "analysis": analysis
            }
        }
        logger.info("[PIPELINE] Pipeline finished successfully.")
        return final_response

    except Exception as e:
        logger.error(f"[PIPELINE] Assembly failed: {e}")
        raise FloorPlanGenerationError(f"[PIPELINE] {str(e)}") from e