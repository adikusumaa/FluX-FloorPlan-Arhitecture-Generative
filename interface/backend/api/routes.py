from fastapi import APIRouter, HTTPException
from .schemas import GenerateRequest, GenerateResponse
import logging
from services.floorplan_service import generate_floorplans

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["generation"])

@router.post("/generate", response_model=GenerateResponse)
async def generate_floorplans_endpoint(request: GenerateRequest):
    user_text = request.user_text.strip()
    logger.info(f"user_text: {user_text[:50]}")

    try:
        result = generate_floorplans(user_text, request.weights, request.location)
        # Pastikan result selalu berisi data yang valid
        if result is None or "data" not in result:
            raise ValueError("Service tidak mengembalikan data yang valid")
        return GenerateResponse(
            status="success",
            message="Berhasil menghasilkan 5 denah terbaik",
            data=result["data"],
            parsed_data=result.get("parsed_data")
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))