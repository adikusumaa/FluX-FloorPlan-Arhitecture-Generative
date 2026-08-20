from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import base64
import io

router = APIRouter()

class GenerateRequest(BaseModel):
    rooms: List[Dict[str, Any]] = Field(...)
    style: Optional[str] = "modern"

class GenerateResponse(BaseModel):
    status: str
    images: List[str]
    message: Optional[str] = None

@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    from interface.backend.services.floorplan_service import generate_floorplan_image
    try:
        image = generate_floorplan_image(request.rooms, request.style)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        return GenerateResponse(status="success", images=[f"data:image/png;base64,{img_b64}"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))