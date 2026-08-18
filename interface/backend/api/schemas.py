# interface/backend/api/schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any

class GenerateRequest(BaseModel):
    """Payload yang diterima dari frontend."""
    user_text: str = Field(..., min_length=10, description="Deskripsi kebutuhan ruang")
    weights: List[float] = Field(..., length=4, description="Bobot prioritas [Keterbukaan, Sirkulasi, Rasionalitas, Adaptabilitas]")
    location: Dict[str, float] = Field(..., description="Koordinat {lat, lng}")

    @validator('weights')
    def weights_sum_to_one(cls, v):
        if abs(sum(v) - 1.0) > 0.01:
            raise ValueError('Bobot harus berjumlah 1.0')
        return v

    @validator('location')
    def location_has_lat_lng(cls, v):
        if 'lat' not in v or 'lng' not in v:
            raise ValueError('location harus memiliki kunci "lat" dan "lng"')
        return v

class FloorPlanData(BaseModel):
    """Data satu denah."""
    id: str
    rank: int
    image_url: str  # Base64 atau URL
    style: Optional[str] = "RPLAN"
    scores: Dict[str, float]  # composite, spatial_openness, etc.
    energy: Optional[Dict[str, Any]] = None
    suggestions: Optional[Dict[str, str]] = None
    rfpa: Optional[Dict[str, Any]] = None
    orientation: Optional[Dict[str, str]] = None
    location: Optional[Dict[str, float]] = None

class GenerateResponse(BaseModel):
    """Response yang dikirim ke frontend."""
    status: str
    message: str
    data: List[FloorPlanData]
    parsed_data: Optional[Dict[str, Any]] = None