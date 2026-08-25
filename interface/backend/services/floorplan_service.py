import sys
import os
import logging
import json
import traceback
import uuid
import base64
import tempfile
import time
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


def calculate_score(analysis: Dict[str, Any]) -> float:
    """Hitung composite score sederhana untuk ranking."""
    missing = analysis.get("missing_count", 0)
    loc_err = analysis.get("location_errors", 0)
    score = 100.0 - (missing * 10) - (loc_err * 5)
    return max(0.0, score)


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
    # STEP 4: GENERATE 15 VARIANTS + POST-PROCESS + RANKING
    # ------------------------------------------------------------
    try:
        chd_base_url = os.getenv("CHATHOUSE_URL")
        if not chd_base_url:
            raise FloorPlanGenerationError("[MCP_CLIENT] CHATHOUSE_URL not set in .env")

        logger.info(f"[MCP_CLIENT] Initializing AgenticWorkflow at {chd_base_url}")
        workflow = AgenticWorkflow(mcp_url=chd_base_url)

        # 4a. Topological mask (sama untuk semua varian)
        logger.info("[MCP_CLIENT] Generating topological mask from room layout.")
        custom_mask_b64 = workflow.generate_topological_mask(chd_rooms)
        logger.info("[MCP_CLIENT] Topological mask generated successfully.")

        client = MCPClient(base_url=chd_base_url)
        cond_scale = 1.5
        NUM_VARIANTS = 15
        TOP_K = 5

        candidates = []

        for idx in range(NUM_VARIANTS):
            seed = 1000 + idx * 17   # seed unik, bisa juga int(time.time()*1000)+idx
            logger.info(f"[MCP_CLIENT] Generating variant {idx+1}/{NUM_VARIANTS} with seed={seed}")

            generation_result = client.generate_floorplan(
                rooms=chd_rooms,
                cond_scale=cond_scale,
                custom_mask=custom_mask_b64,
                seed=seed
            )

            # Extract image
            images = generation_result.get("data") or generation_result.get("images", [])
            if not images or not isinstance(images, list) or len(images) == 0:
                logger.warning(f"[MCP_CLIENT] Variant {idx+1}: No images received, skipping.")
                continue
            raw_image = images[0]
            if isinstance(raw_image, str) and raw_image.startswith("data:image"):
                raw_image = raw_image.split(",")[1]

            # Save temporary for analysis and post-processing
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(base64.b64decode(raw_image))
            logger.info(f"[POST-PROCESS] Variant {idx+1}: temp saved to {tmp_path}")

            # Reconstruction
            logger.info(f"[POST-PROCESS] Variant {idx+1}: applying reconstruction.")
            workflow.apply_reconstruction(tmp_path)

            # Analysis
            analysis = workflow.analyzer.analyze(tmp_path, chd_rooms)
            missing = analysis.get("missing_count", 0)
            loc_err = analysis.get("location_errors", 0)
            score = calculate_score(analysis)
            logger.info(
                f"[POST-PROCESS] Variant {idx+1}: missing={missing}, loc_errors={loc_err}, score={score:.2f}"
            )

            # Upscale with NEAREST
            img = cv2.imread(tmp_path)
            if img is None:
                logger.warning(f"[POST-PROCESS] Variant {idx+1}: failed to read image, skipping upscale.")
                os.unlink(tmp_path)
                continue
            h, w = img.shape[:2]
            scale_factor = 8
            new_w, new_h = w * scale_factor, h * scale_factor
            img_hd = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
            cv2.imwrite(tmp_path, img_hd)
            logger.info(f"[POST-PROCESS] Variant {idx+1}: upscaled to {new_w}x{new_h} using NEAREST.")

            # Optional DPI metadata
            with Image.open(tmp_path) as pil_img:
                pil_img.save(tmp_path, dpi=(300, 300))

            # Read as base64
            with open(tmp_path, "rb") as f:
                reconstructed_b64 = base64.b64encode(f.read()).decode('utf-8')

            # Clean up temp
            os.unlink(tmp_path)
            logger.info(f"[POST-PROCESS] Variant {idx+1}: temp file cleaned up.")

            # Save candidate
            candidate = {
                "id": str(uuid.uuid4()),
                "image_url": f"data:image/png;base64,{reconstructed_b64}",
                "seed": seed,
                "rank": 0,  # akan diisi setelah sorting
                "scores": {
                    "composite": score,
                    "missing_count": missing,
                    "location_errors": loc_err
                },
                "analysis": analysis
            }
            candidates.append(candidate)

        if not candidates:
            raise FloorPlanGenerationError("[MCP_CLIENT] No valid variants generated.")

        # Ranking
        candidates.sort(key=lambda x: x["scores"]["composite"], reverse=True)
        top_candidates = candidates[:TOP_K]
        for i, cand in enumerate(top_candidates):
            cand["rank"] = i + 1

        logger.info(f"[PIPELINE] Ranking completed. Returning top {len(top_candidates)} floor plans.")
        for cand in top_candidates:
            logger.info(f"  Rank {cand['rank']}: {cand['id']} score={cand['scores']['composite']:.2f}")

    except Exception as e:
        logger.error(f"[MCP_CLIENT] Generation or post-processing failed: {e}\n{traceback.format_exc()}")
        raise FloorPlanGenerationError(f"[MCP_CLIENT] {str(e)}") from e

    # ------------------------------------------------------------
    # STEP 5: FINAL RESPONSE
    # ------------------------------------------------------------
    try:
        logger.info("[PIPELINE] Assembling final response.")
        final_response = {
            "data": top_candidates,   # <-- hanya 5 terbaik
            "parsed_data": {
                "validated_rooms": validated_request.model_dump(),
                "chd_format": chd_rooms,
                "total_area_sqft": validated_request.get_total_area(),
                "room_counts": validated_request.get_room_counts(),
                "generation_meta": generation_result.get("meta", {}),
                "analysis_summary": [
                    {
                        "rank": cand["rank"],
                        "seed": cand["seed"],
                        "score": cand["scores"]["composite"],
                        "missing_count": cand["scores"]["missing_count"],
                        "location_errors": cand["scores"]["location_errors"]
                    }
                    for cand in top_candidates
                ]
            }
        }
        logger.info("[PIPELINE] Pipeline finished successfully.")
        return final_response

    except Exception as e:
        logger.error(f"[PIPELINE] Assembly failed: {e}")
        raise FloorPlanGenerationError(f"[PIPELINE] {str(e)}") from e