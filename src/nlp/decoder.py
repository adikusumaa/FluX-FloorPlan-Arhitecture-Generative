"""
src/nlp/decoder.py
Decoder: Validasi dan parsing output encoder menggunakan Pydantic.
"""
import json
import logging
from typing import Union, Dict, Any, Tuple
from pydantic import ValidationError

from .schemas import FloorPlanRequest

logger = logging.getLogger(__name__)

# ============================================================
# Custom Error Classes
# ============================================================
class DecoderError(Exception):
    """Base exception untuk decoder"""
    pass

class ValidationErrorDetail(DecoderError):
    """Error saat validasi Pydantic gagal"""
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(self._format_errors())
    
    def _format_errors(self) -> str:
        messages = []
        for error in self.errors:
            loc = ' -> '.join(str(l) for l in error['loc'])
            messages.append(f"{loc}: {error['msg']}")
        return f"Validasi gagal:\n" + "\n".join(messages)

class MalformedJSONError(DecoderError):
    """Error saat input bukan JSON yang valid"""
    pass


# ============================================================
# Fungsi Validasi Utama
# ============================================================
def validate_and_parse(raw_json: Union[str, dict]) -> FloorPlanRequest:
    """
    Validasi dan parse output encoder menjadi FloorPlanRequest.
    
    Args:
        raw_json: JSON string atau dict dari encoder (/encode_detailed)
    
    Returns:
        FloorPlanRequest: Objek Pydantic yang sudah divalidasi
    
    Raises:
        MalformedJSONError: Jika input bukan JSON yang valid
        ValidationErrorDetail: Jika validasi Pydantic gagal
    """
    # 1. Parse JSON jika masih string
    if isinstance(raw_json, str):
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise MalformedJSONError(f"JSON tidak valid: {e}")
    else:
        data = raw_json
    
    # 2. Pastikan ada field 'rooms'
    if 'rooms' not in data or not data['rooms']:
        # Coba cari di dalam 'summary' atau langsung di root
        if 'summary' in data and 'rooms' not in data:
            # Kemungkinan ini output dari /encode (lama), bukan /encode_detailed
            # Kita perlu mengkonversi summary ke format rooms
            logger.warning("Input dari /encode (lama), mengkonversi ke format detailed")
            data = _convert_summary_to_detailed(data)
        else:
            raise ValidationErrorDetail([{
                'loc': ('rooms',),
                'msg': 'Field "rooms" tidak ditemukan atau kosong'
            }])
    
    # 3. Validasi dengan Pydantic
    try:
        validated = FloorPlanRequest(**data)
        logger.info(f"✅ Validasi berhasil! {len(validated.rooms)} ruangan terdeteksi.")
        return validated
    except ValidationError as e:
        raise ValidationErrorDetail(e.errors())


def _convert_summary_to_detailed(summary_data: dict) -> dict:
    """
    Konversi output /encode (summary saja) ke format detailed.
    Ini adalah fallback untuk kompatibilitas dengan encoder lama.
    """
    room_types = {
        'bedroom': ['master room', 'bedroom', 'guest room'],
        'bathroom': ['bathroom', 'toilet'],
        'living_room': ['living room', 'lounge'],
        'kitchen': ['kitchen'],
        'balcony': ['balcony', 'terrace'],
        'common_room': ['common room', 'dining room']
    }
    
    rooms = []
    for room_type, names in room_types.items():
        count = summary_data.get(room_type, 0)
        for i in range(count):
            name = names[0] if count == 1 else f"{names[0]} {i+1}"
            rooms.append({
                'name': name,
                'type': room_type,
                'size': {'width': 10.0, 'height': 10.0},  # default size
                'links': []
            })
    
    return {'rooms': rooms, 'summary': summary_data}


def validate_json_str(json_str: str) -> Tuple[bool, Union[FloorPlanRequest, str]]:
    """
    Fungsi helper untuk validasi dengan return tuple (success, result/error).
    
    Returns:
        (True, FloorPlanRequest) jika berhasil
        (False, error_message) jika gagal
    """
    try:
        result = validate_and_parse(json_str)
        return True, result
    except (MalformedJSONError, ValidationErrorDetail) as e:
        return False, str(e)


# ============================================================
# Funsi untuk integrasi dengan alur utama
# ============================================================
def process_encoder_output(encoder_result: Union[str, dict]) -> dict:
    """
    Proses output dari encoder dan siapkan untuk ChatHouseDiffusion.
    
    Args:
        encoder_result: Output dari encoder_client.encode_text()
    
    Returns:
        dict: Data yang siap dikirim ke MCP Client / ChatHouseDiffusion
    
    Raises:
        DecoderError: Jika validasi gagal
    """
    try:
        validated = validate_and_parse(encoder_result)
        
        # Konversi ke format ChatHouseDiffusion
        chd_format = validated.to_chd_format()
        
        return {
            'status': 'success',
            'validated_data': validated.model_dump(),
            'chd_format': chd_format,
            'total_area': validated.get_total_area(),
            'room_counts': validated.get_room_counts()
        }
    except DecoderError as e:
        return {
            'status': 'error',
            'error': str(e)
        }


# ============================================================
# Contoh penggunaan
# ============================================================
if __name__ == "__main__":
    # Test dengan output encoder
    sample_output = {
        "rooms": [
            {
                "name": "master room",
                "type": "bedroom",
                "size": {"width": 16, "height": 16},
                "location": "middle of the west side",
                "links": ["living room", "balcony"]
            },
            {
                "name": "bathroom",
                "type": "bathroom",
                "size": {"width": 10, "height": 4},
                "location": "middle of the east side",
                "links": ["kitchen", "common room"]
            }
        ],
        "summary": {"bedroom": 1, "bathroom": 1}
    }
    
    print("="*60)
    print("🧪 Testing Decoder")
    print("="*60)
    
    result = process_encoder_output(sample_output)
    if result['status'] == 'success':
        print("✅ Validasi berhasil!")
        print(f"📊 Total area: {result['total_area']:.2f} ft²")
        print(f"📊 Room counts: {result['room_counts']}")
        print(f"\n📤 ChatHouseDiffusion format:")
        print(json.dumps(result['chd_format'], indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error: {result['error']}")