# interface/backend/api/routes.py
from fastapi import APIRouter, HTTPException, status
from .schemas import GenerateRequest, GenerateResponse, FloorPlanData
from services.crew_service import run_crew_workflow
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["generation"])

@router.post("/generate", response_model=GenerateResponse)
async def generate_floorplans(request: GenerateRequest):
    """
    Endpoint utama untuk generate floor plan.
    Menerima user_text, weights, location.
    Memanggil CrewAI untuk menjalankan seluruh alur.
    """
    try:
        logger.info(f"Received request: text='{request.user_text[:50]}...'")
        
        # Panggil CrewAI (fungsi async nanti)
        # Sementara kita gunakan placeholder
        result = await run_crew_workflow(
            user_text=request.user_text,
            weights=request.weights,
            location=request.location
        )
        
        # result harus berupa dict dengan kunci 'data' dan 'parsed_data'
        if not result or 'data' not in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CrewAI gagal menghasilkan data"
            )
        
        return GenerateResponse(
            status="success",
            message="Berhasil menghasilkan 5 denah terbaik",
            data=result['data'],
            parsed_data=result.get('parsed_data')
        )
        
    except Exception as e:
        logger.error(f"Error in /generate: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan: {str(e)}"
        )