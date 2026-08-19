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
    pass

class ValidationErrorDetail(DecoderError):
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(self._format_errors())
    
    def _format_errors(self) -> str:
        messages = []
        for error in self.errors:
            loc = ' -> '.join(str(l) for l in error['loc'])
            messages.append(f"{loc}: {error['msg']}")
        return "Validasi gagal:\n" + "\n".join(messages)

class MalformedJSONError(DecoderError):
    pass

# ============================================================
# Fungsi Konversi yang Diperbaiki
# ============================================================

def _convert_summary_to_detailed(summary_data: dict) -> dict:
    """
    Konversi dari summary (jumlah per tipe) ke list rooms dengan default size.
    """
    # Pastikan summary_data adalah dict
    if not isinstance(summary_data, dict):
        try:
            summary_data = dict(summary_data)
        except:
            return {'rooms': [], 'summary': summary_data}
    
    # Mapping tipe ruangan ke nama default
    room_mapping = {
        'bedroom': ['master room', 'bedroom', 'guest room'],
        'bathroom': ['bathroom', 'toilet'],
        'living_room': ['living room', 'lounge'],
        'kitchen': ['kitchen'],
        'balcony': ['balcony', 'terrace'],
        'common_room': ['common room', 'dining room']
    }
    
    rooms = []
    for room_type, names in room_mapping.items():
        # Ambil count dari summary, bisa berupa int atau string
        count = summary_data.get(room_type, 0)
        try:
            count = int(count)
        except:
            count = 0
        
        if count > 0:
            default_name = names[0]  # nama utama
            for i in range(count):
                if count == 1:
                    name = default_name
                else:
                    name = f"{default_name} {i+1}"
                rooms.append({
                    'name': name,
                    'type': room_type,
                    'size': {'width': 10.0, 'height': 10.0},
                    'links': []
                })
    
    # Jika rooms masih kosong, coba ambil dari field lain di summary
    if not rooms:
        # Coba semua key di summary yang nilainya integer >0
        for key, val in summary_data.items():
            if key in room_mapping:
                continue  # sudah diproses
            try:
                count = int(val)
                if count > 0:
                    # Tambahkan sebagai common_room atau tipe yang tidak dikenal
                    for i in range(count):
                        rooms.append({
                            'name': f"{key.replace('_', ' ')} {i+1}" if count > 1 else key.replace('_', ' '),
                            'type': 'common_room',  # fallback
                            'size': {'width': 10.0, 'height': 10.0},
                            'links': []
                        })
            except:
                pass
    
    return {'rooms': rooms, 'summary': summary_data}


def _convert_root_to_detailed(root_data: dict) -> dict:
    """
    Konversi dari field root langsung (bedroom, bathroom, dll.) ke format detailed.
    """
    room_mapping = {
        'bedroom': ['master room', 'bedroom', 'guest room'],
        'bathroom': ['bathroom', 'toilet'],
        'living_room': ['living room', 'lounge'],
        'kitchen': ['kitchen'],
        'balcony': ['balcony', 'terrace'],
        'common_room': ['common room', 'dining room']
    }
    
    rooms = []
    for room_type, names in room_mapping.items():
        count = root_data.get(room_type, 0)
        try:
            count = int(count)
        except:
            count = 0
        if count > 0:
            default_name = names[0]
            for i in range(count):
                if count == 1:
                    name = default_name
                else:
                    name = f"{default_name} {i+1}"
                rooms.append({
                    'name': name,
                    'type': room_type,
                    'size': {'width': 10.0, 'height': 10.0},
                    'links': []
                })
    return {'rooms': rooms, 'summary': root_data}


# ============================================================
# Fungsi Validasi Utama
# ============================================================

def validate_and_parse(raw_json: Union[str, dict]) -> FloorPlanRequest:
    """
    Validasi dan parse output encoder menjadi FloorPlanRequest.
    """
    # 1. Parse JSON
    if isinstance(raw_json, str):
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise MalformedJSONError(f"JSON tidak valid: {e}")
    else:
        data = raw_json

    # 2. Pastikan ada rooms
    if 'rooms' not in data or not data['rooms']:
        # Coba dari summary
        if 'summary' in data and data['summary']:
            logger.warning("rooms kosong, mencoba membuat dari summary")
            data = _convert_summary_to_detailed(data['summary'])
        else:
            # Coba dari root fields
            room_keys = ['bedroom', 'bathroom', 'living_room', 'kitchen', 'balcony', 'common_room']
            if any(k in data for k in room_keys):
                logger.warning("Mengkonversi dari root fields")
                data = _convert_root_to_detailed(data)
            else:
                raise ValidationErrorDetail([{
                    'loc': ('rooms',),
                    'msg': 'Field "rooms" tidak ditemukan dan tidak ada sumber lain'
                }])

    # 3. Pastikan rooms tidak kosong setelah konversi
    if 'rooms' not in data or not data['rooms']:
        raise ValidationErrorDetail([{
            'loc': ('rooms',),
            'msg': 'Tidak dapat menghasilkan rooms dari data yang diberikan'
        }])

    # 4. Validasi Pydantic
    try:
        validated = FloorPlanRequest(**data)
        logger.info(f"✅ Validasi berhasil! {len(validated.rooms)} ruangan terdeteksi.")
        return validated
    except ValidationError as e:
        raise ValidationErrorDetail(e.errors())


# ============================================================
# Helper & Integrasi
# ============================================================

def validate_json_str(json_str: str) -> Tuple[bool, Union[FloorPlanRequest, str]]:
    try:
        result = validate_and_parse(json_str)
        return True, result
    except (MalformedJSONError, ValidationErrorDetail) as e:
        return False, str(e)

def process_encoder_output(encoder_result: Union[str, dict]) -> dict:
    try:
        validated = validate_and_parse(encoder_result)
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