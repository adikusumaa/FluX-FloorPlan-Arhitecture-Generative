from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any

class GenerateRequest(BaseModel):
    user_text: str = Field(..., alias="userText", description="Deskripsi kebutuhan ruang")
    weights: List[float] = Field(..., min_length=4, max_length=4, description="Bobot prioritas")
    location: Dict[str, float] = Field(..., alias="coordinates", description="Koordinat {lat, lng}")

    @validator('weights')
    def weights_sum_to_one(cls, v):
        if abs(sum(v) - 1.0) > 0.01:
            raise ValueError('Bobot harus berjumlah 1.0')
        return v

    @validator('location')
    def location_has_lat_lng(cls, v):
        if 'lat' not in v or 'lng' not in v:
            raise ValueError('location harus memiliki kunci "lat" dan "lng"')
        if not (-90 <= v['lat'] <= 90):
            raise ValueError('lat tidak valid')
        if not (-180 <= v['lng'] <= 180):
            raise ValueError('lng tidak valid')
        return v

    model_config = {
        "populate_by_name": True,
        "allow_population_by_field_name": True
    }

class FloorPlanData(BaseModel):
    id: str
    rank: int
    image_url: str
    style: Optional[str] = "Modern"
    scores: Dict[str, Any] = Field(default_factory=dict)
    energy: Optional[Dict[str, Any]] = None
    suggestions: Optional[Dict[str, str]] = None
    rfpa: Optional[Dict[str, Any]] = None
    orientation: Optional[float] = None
    location: Optional[Dict[str, float]] = None
    mitigation: Optional[str] = None
    qwen_analysis: Optional[str] = None

class GenerateResponse(BaseModel):
    status: str
    message: str
    data: List[FloorPlanData]
    parsed_data: Optional[Dict[str, Any]] = None   # crew_summary ada di dalam parsed_data