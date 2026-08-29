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

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.mcp.client.encoder_client import encode_text
from src.nlp.decoder import validate_and_parse, DecoderError, MalformedJSONError, ValidationErrorDetail
from src.agents.workflow.agentic_refine import AgenticWorkflow
from src.mcp.client.mcp_client import MCPClient
from src.mcp.client.environment_client import evaluate_plans
from src.agents.crew.crew_runner import generate_crew_summary   # <-- Import CrewAI runner

logger = logging.getLogger(__name__)

class FloorPlanGenerationError(Exception):
    pass

def calculate_score(analysis: Dict[str, Any]) -> float:
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

    # ================= INPUT MAPPICKER =================
    if location:
        logger.info(f"[INPUT][MAPPICKER] Coordinates received: lat={location.get('lat')}, lng={location.get('lng')}")
    else:
        logger.warning("[INPUT][MAPPICKER] No location provided, environment evaluation will be skipped.")
    # ===================================================

    # --- Encoder ---
    try:
        encoder_url = os.getenv("ENCODER_URL")
        if not encoder_url:
            raise FloorPlanGenerationError("[ENCODER] ENCODER_URL not set in .env")
        logger.info(f"[ENCODER] Request to {encoder_url}/encode_detailed")
        detailed_room_json = encode_text(user_text)
        if not isinstance(detailed_room_json, dict):
            raise FloorPlanGenerationError(f"[ENCODER] Invalid response type: {type(detailed_room_json)}")
        room_count = len(detailed_room_json.get("rooms", []))
        logger.info(f"[ENCODER] Extraction completed. Rooms found: {room_count}")
    except Exception as e:
        logger.error(f"[ENCODER] Failed: {e}\n{traceback.format_exc()}")
        raise FloorPlanGenerationError(f"[ENCODER] {str(e)}") from e

    # --- Decoder ---
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

    # --- Converter ---
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

    # --- Generation + Post-processing ---
    try:
        chd_base_url = os.getenv("CHATHOUSE_URL")
        if not chd_base_url:
            raise FloorPlanGenerationError("[MCP_CLIENT] CHATHOUSE_URL not set in .env")

        logger.info(f"[MCP_CLIENT] Initializing AgenticWorkflow at {chd_base_url}")
        workflow = AgenticWorkflow(mcp_url=chd_base_url)
        client = MCPClient(base_url=chd_base_url)

        cond_scale = 1.5
        NUM_VARIANTS = 15
        TOP_K = 5
        candidates = []

        for idx in range(NUM_VARIANTS):
            seed = 1000 + idx * 17
            logger.info(f"[MCP_CLIENT] Generating variant {idx+1}/{NUM_VARIANTS} with seed={seed}")

            custom_mask_b64 = workflow.generate_topological_mask(chd_rooms, seed=seed)

            generation_result = client.generate_floorplan(
                rooms=chd_rooms,
                cond_scale=cond_scale,
                custom_mask=custom_mask_b64,
                seed=seed
            )

            images = generation_result.get("data") or generation_result.get("images", [])
            if not images or not isinstance(images, list) or len(images) == 0:
                logger.warning(f"[MCP_CLIENT] Variant {idx+1}: No images received, skipping.")
                continue
            raw_image = images[0]
            if isinstance(raw_image, str) and raw_image.startswith("data:image"):
                raw_image = raw_image.split(",")[1]

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(base64.b64decode(raw_image))
            logger.info(f"[POST-PROCESS] Variant {idx+1}: temp saved to {tmp_path}")

            workflow.apply_reconstruction(tmp_path)

            analysis = workflow.analyzer.analyze(tmp_path, chd_rooms)
            missing = analysis.get("missing_count", 0)
            loc_err = analysis.get("location_errors", 0)
            score = calculate_score(analysis)
            logger.info(
                f"[POST-PROCESS] Variant {idx+1}: missing={missing}, loc_errors={loc_err}, score={score:.2f}"
            )

            # Upscale dan simpan gambar
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
            with Image.open(tmp_path) as pil_img:
                pil_img.save(tmp_path, dpi=(300, 300))
            with open(tmp_path, "rb") as f:
                reconstructed_b64 = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp_path)

            # Variasikan orientasi berdasarkan seed (0-359 derajat)
            orientation = float(seed % 360)
            logger.info(f"[POST-PROCESS] Variant {idx+1}: assigned orientation = {orientation} deg")

            candidate = {
                "id": str(uuid.uuid4()),
                "image_url": f"data:image/png;base64,{reconstructed_b64}",
                "seed": seed,
                "rank": 0,
                "scores": {
                    "composite": score,
                    "missing_count": float(missing),
                    "location_errors": float(loc_err)
                },
                "analysis": analysis,
                "suggestions": {},
                "energy": {},
                "rfpa": None,
                "orientation": orientation,
                "location": {"lat": 0.0, "lng": 0.0}
            }
            candidates.append(candidate)

        if not candidates:
            raise FloorPlanGenerationError("[MCP_CLIENT] No valid variants generated.")

        candidates.sort(key=lambda x: x["scores"]["composite"], reverse=True)
        top_candidates = candidates[:TOP_K]
        for i, cand in enumerate(top_candidates):
            cand["rank"] = i + 1

        logger.info(f"[PIPELINE] Ranking completed. Returning top {len(top_candidates)} floor plans.")

        # ================= ENV INTEGRATION =================
        if location and isinstance(location, dict) and "lat" in location and "lng" in location:
            lat = location["lat"]
            lon = location["lng"]
            logger.info(f"[ENV INTEGRATION] Environment evaluation requested for lat={lat}, lon={lon}")

            env_plans = []
            for cand in top_candidates:
                rooms_for_env = [{"name": r["name"], "center": [0, 0], "windows": []} for r in chd_rooms]
                env_plans.append({
                    "name": f"Variant {cand['rank']} (seed {cand['seed']})",
                    "orientation": cand["orientation"],
                    "rooms": rooms_for_env
                })

            initial_scores_env = [c["scores"]["composite"] / 100.0 for c in top_candidates]

            try:
                logger.info("[ENV INTEGRATION] Calling environment evaluation API...")
                env_result = evaluate_plans(lat, lon, env_plans, initial_scores_env)
                env_results = env_result.get("results", [])
                if len(env_results) != len(top_candidates):
                    logger.warning("[ENV INTEGRATION] Mismatch results count, skip env ranking.")
                else:
                    # Log hasil environment dari API
                    logger.info("[ENV INTEGRATION] Environment API returned results:")
                    for env_item in env_results:
                        logger.info(
                            f"  Plan: {env_item['plan']['name']} | "
                            f"env_score={env_item.get('env_score', 0):.3f} | "
                            f"combined={env_item.get('combined_score', 0):.3f}"
                        )

                    for cand, env_item in zip(top_candidates, env_results):
                        combined = env_item.get("combined_score", cand["scores"]["composite"] / 100.0)
                        env_score = env_item.get("env_score", 0.0)
                        cand["scores"]["composite"] = round(combined * 100, 2)
                        cand["scores"]["env_score"] = round(env_score, 3)

                        env_detail = env_item.get("scores_detail", {})
                        cand["scores"]["spatial_openness"] = env_detail.get("noise_score", 0.0)
                        cand["scores"]["circulation_efficiency"] = env_detail.get("ventilation_score", 0.0)
                        cand["scores"]["layout_rationality"] = env_detail.get("daylight_score", 0.0)
                        cand["scores"]["adaptability"] = env_score

                        cand["energy"] = {
                            "EUI": round(env_score * 100, 2),
                            "total_area": validated_request.get_total_area() * 0.092903,
                            "fire_safety_status": "OK" if env_score > 0.3 else "WARN",
                            "noise_score": env_detail.get("noise_score", 0.0),
                            "daylight_score": env_detail.get("daylight_score", 0.0),
                            "ventilation_score": env_detail.get("ventilation_score", 0.0),
                            "suggestions_list": env_detail.get("suggestions", [])
                        }

                        mitigation_text = env_item.get("mitigation", "")
                        cand["suggestions"] = {
                            "environment": mitigation_text
                        }
                        cand["qwen_analysis"] = mitigation_text

                        cand["scores"]["orca"] = {
                            "O": cand["scores"]["spatial_openness"],
                            "C": cand["scores"]["circulation_efficiency"],
                            "R": cand["scores"]["layout_rationality"],
                            "A": cand["scores"]["adaptability"],
                            "mitigation_text": mitigation_text
                        }

                        cand["location"] = {"lat": lat, "lng": lon}

                    # Re-rank
                    top_candidates.sort(key=lambda x: x["scores"]["composite"], reverse=True)
                    for new_rank, cand in enumerate(top_candidates, start=1):
                        cand["rank"] = new_rank

                    logger.info("[ENV INTEGRATION] Environment evaluation completed. Final ranking:")
                    for cand in top_candidates:
                        logger.info(f"  Rank {cand['rank']}: {cand['id']} composite={cand['scores']['composite']:.2f}")

            except Exception as e:
                logger.error(f"[ENV INTEGRATION] Environment evaluation failed: {e}. Using original ranking.")
                for cand in top_candidates:
                    cand["scores"]["spatial_openness"] = 0.0
                    cand["scores"]["circulation_efficiency"] = 0.0
                    cand["scores"]["layout_rationality"] = 0.0
                    cand["scores"]["adaptability"] = 0.0
                    cand["scores"]["orca"] = {"O": 0, "C": 0, "R": 0, "A": 0, "mitigation_text": ""}
                    cand["energy"] = {
                        "EUI": 0.0,
                        "total_area": validated_request.get_total_area() * 0.092903,
                        "fire_safety_status": "N/A",
                        "noise_score": 0.0,
                        "daylight_score": 0.0,
                        "ventilation_score": 0.0
                    }
                    cand["qwen_analysis"] = ""
        else:
            logger.info("[ENV INTEGRATION] No location provided, skipping environment evaluation.")
            for cand in top_candidates:
                cand["scores"]["spatial_openness"] = 0.0
                cand["scores"]["circulation_efficiency"] = 0.0
                cand["scores"]["layout_rationality"] = 0.0
                cand["scores"]["adaptability"] = 0.0
                cand["scores"]["orca"] = {"O": 0, "C": 0, "R": 0, "A": 0, "mitigation_text": ""}
                cand["energy"] = {
                    "EUI": 0.0,
                    "total_area": validated_request.get_total_area() * 0.092903,
                    "fire_safety_status": "N/A",
                    "noise_score": 0.0,
                    "daylight_score": 0.0,
                    "ventilation_score": 0.0
                }
                cand["qwen_analysis"] = ""
        # ================= END ENV INTEGRATION =================

        # ================= CREWAI SUMMARY =================
        try:
            logger.info("[CREW] Generating final summary using CrewAI...")
            crew_summary = generate_crew_summary(top_candidates, user_text, location)
            if crew_summary:
                # Tambahkan ringkasan ke parsed_data, bukan per kandidat
                logger.info("[CREW] Summary generated successfully.")
            else:
                logger.warning("[CREW] Empty summary, skipping.")
        except Exception as e:
            logger.error(f"[CREW] Failed to generate summary: {e}")
            crew_summary = ""
        # ================= END CREWAI SUMMARY =================

    except Exception as e:
        logger.error(f"[MCP_CLIENT] Generation or post-processing failed: {e}\n{traceback.format_exc()}")
        raise FloorPlanGenerationError(f"[MCP_CLIENT] {str(e)}") from e

    # --- Final Assembly ---
    try:
        logger.info("[PIPELINE] Assembling final response.")
        final_response = {
            "data": top_candidates,
            "parsed_data": {
                "validated_rooms": validated_request.model_dump(),
                "chd_format": chd_rooms,
                "total_area_sqft": validated_request.get_total_area(),
                "room_counts": validated_request.get_room_counts(),
                "generation_meta": generation_result.get("meta", {}),
                "analysis_summary": [
                    {
                        "rank": c["rank"],
                        "seed": c["seed"],
                        "score": c["scores"]["composite"],
                        "missing_count": c["scores"]["missing_count"],
                        "location_errors": c["scores"]["location_errors"],
                        "env_score": c["scores"].get("env_score", None),
                        "has_environment": "env_score" in c["scores"]
                    }
                    for c in top_candidates
                ],
                "environment_applied": any("env_score" in c["scores"] for c in top_candidates),
                "crew_summary": crew_summary  # <-- Tambahkan ke parsed_data
            }
        }
        logger.info("[PIPELINE] Pipeline finished successfully.")
        return final_response
    except Exception as e:
        logger.error(f"[PIPELINE] Assembly failed: {e}")
        raise FloorPlanGenerationError(f"[PIPELINE] {str(e)}") from e