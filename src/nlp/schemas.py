"""
src/nlp/schemas.py
Pydantic models untuk validasi output encoder.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from enum import Enum

# ============================================================
# Model untuk setiap ruangan
# ============================================================
class RoomSize(BaseModel):
    """Ukuran ruangan dalam feet"""
    width: float = Field(..., ge=0.5, le=100, description="Lebar ruangan (feet)")
    height: float = Field(..., ge=0.5, le=100, description="Panjang ruangan (feet)")
    
    @validator('width', 'height')
    def check_positive(cls, v):
        if v <= 0:
            raise ValueError(f"Ukuran harus positif, mendapat {v}")
        return v
    
    def area(self) -> float:
        """Menghitung luas ruangan"""
        return self.width * self.height


class RoomDetail(BaseModel):
    """Detail satu ruangan"""
    name: str = Field(..., min_length=1, max_length=50, description="Nama unik ruangan")
    type: Literal[
        'bedroom', 'bathroom', 'living_room', 'kitchen', 
        'balcony', 'common_room', 'storage', 'dining_room'
    ] = Field(..., description="Tipe ruangan")
    size: RoomSize = Field(..., description="Ukuran ruangan (width x height)")
    location: Optional[str] = Field(None, max_length=100, description="Posisi ruangan")
    links: List[str] = Field(default_factory=list, description="Nama ruangan yang terhubung")


# ============================================================
# Model untuk summary (jumlah ruangan per tipe)
# ============================================================
class RoomSummary(BaseModel):
    """Ringkasan jumlah ruangan per tipe"""
    bedroom: int = Field(0, ge=0, description="Jumlah kamar tidur")
    bathroom: int = Field(0, ge=0, description="Jumlah kamar mandi")
    living_room: int = Field(0, ge=0, description="Jumlah ruang tamu")
    kitchen: int = Field(0, ge=0, description="Jumlah dapur")
    balcony: int = Field(0, ge=0, description="Jumlah balkon")
    common_room: int = Field(0, ge=0, description="Jumlah ruang bersama")
    
    @validator('*')
    def check_non_negative(cls, v):
        if v < 0:
            raise ValueError(f"Nilai tidak boleh negatif: {v}")
        return v


# ============================================================
# Model utama: Request yang akan dikirim ke ChatHouseDiffusion
# ============================================================
class FloorPlanRequest(BaseModel):
    """Struktur lengkap request untuk ChatHouseDiffusion"""
    rooms: List[RoomDetail] = Field(..., min_items=1, description="Daftar ruangan")
    summary: Optional[RoomSummary] = Field(None, description="Ringkasan jumlah ruangan")
    
    # Field opsional untuk konteks tambahan
    total_area: Optional[float] = Field(None, ge=30, le=500, description="Total luas bangunan (m²)")
    floors: Optional[int] = Field(1, ge=1, le=3, description="Jumlah lantai")
    style: Optional[Literal['modern', 'minimalis', 'klasik', 'skandinavia', 'jepang']] = Field(
        None, description="Gaya arsitektur"
    )
    
    @validator('rooms')
    def check_at_least_one_bedroom(cls, rooms):
        """Validasi: minimal ada 1 kamar tidur"""
        bedrooms = [r for r in rooms if r.type == 'bedroom']
        if len(bedrooms) == 0:
            raise ValueError("Minimal harus ada 1 kamar tidur (bedroom)")
        return rooms
    
    @validator('rooms')
    def check_unique_names(cls, rooms):
        """Validasi: nama ruangan harus unik"""
        names = [r.name.lower() for r in rooms]
        if len(names) != len(set(names)):
            duplicates = [n for n in set(names) if names.count(n) > 1]
            raise ValueError(f"Nama ruangan duplikat: {duplicates}")
        return rooms
    
    @validator('rooms')
    def check_links_valid(cls, rooms):
        """Validasi: semua links merujuk ke nama ruangan yang valid"""
        room_names = [r.name.lower() for r in rooms]
        for room in rooms:
            for link in room.links:
                if link.lower() not in room_names:
                    raise ValueError(
                        f"Link '{link}' di ruangan '{room.name}' "
                        f"tidak merujuk ke ruangan yang valid"
                    )
        return rooms
    
    def get_room_counts(self) -> dict:
        """Mendapatkan jumlah ruangan per tipe dari list rooms"""
        counts = {}
        for room in self.rooms:
            counts[room.type] = counts.get(room.type, 0) + 1
        return counts
    
    def get_total_area(self) -> float:
        """Menghitung total luas dari semua ruangan"""
        return sum(room.size.area() for room in self.rooms)
    
    def to_chd_format(self) -> dict:
        """Konversi ke format ChatHouseDiffusion (panggil converter)"""
        from .converter import convert_to_chd_format
        # Gunakan model_dump() untuk Pydantic v2
        return convert_to_chd_format(self.model_dump())