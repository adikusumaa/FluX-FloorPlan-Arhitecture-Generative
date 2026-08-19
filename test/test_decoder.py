"""
tests/test_decoder.py
Unit test untuk decoder.
"""

import sys
import os
# Tambahkan root proyek ke sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

import pytest
import json
import copy
from src.nlp.decoder import validate_and_parse, process_encoder_output, ValidationErrorDetail
from src.nlp.schemas import FloorPlanRequest, RoomDetail

# ============================================================
# Sample data (output dari encoder)
# ============================================================
VALID_ENCODER_OUTPUT = {
    "rooms": [
        {
            "name": "master room",
            "type": "bedroom",
            "size": {"width": 16.0, "height": 16.0},
            "location": "middle of the west side",
            "links": ["living room", "balcony"]
        },
        {
            "name": "bathroom",
            "type": "bathroom",
            "size": {"width": 10.0, "height": 4.0},
            "location": "middle of the east side",
            "links": ["kitchen", "common room"]
        },
        {
            "name": "common room",
            "type": "common_room",
            "size": {"width": 14.0, "height": 14.0},
            "location": "north and east side",
            "links": ["bathroom", "master room"]
        },
        {
            "name": "kitchen",
            "type": "kitchen",
            "size": {"width": 10.0, "height": 4.0},
            "location": "south and east corner",
            "links": ["storage", "bathroom"]
        },
        {
            "name": "living room",
            "type": "living_room",
            "size": {"width": 20.0, "height": 18.0},
            "location": "south east corner",
            "links": []
        },
        {
            "name": "balcony",
            "type": "balcony",
            "size": {"width": 16.0, "height": 4.0},
            "location": "north and west corner",
            "links": ["master room", "common room"]
        },
        {
            "name": "storage",
            "type": "storage",
            "size": {"width": 4.0, "height": 4.0},
            "location": "south and east corner",
            "links": ["living room", "kitchen"]
        }
    ],
    "summary": {
        "bedroom": 1,
        "bathroom": 1,
        "living_room": 1,
        "kitchen": 1,
        "balcony": 1,
        "common_room": 1
    }
}


def test_valid_decoder():
    """Test validasi dengan data yang benar"""
    result = validate_and_parse(VALID_ENCODER_OUTPUT)
    assert isinstance(result, FloorPlanRequest)
    assert len(result.rooms) == 7
    assert result.summary.bedroom == 1
    assert result.get_total_area() > 0


def test_no_bedroom():
    """Test error jika tidak ada kamar tidur"""
    data = copy.deepcopy(VALID_ENCODER_OUTPUT)
    data['rooms'] = [r for r in data['rooms'] if r['type'] != 'bedroom']
    
    with pytest.raises(ValidationErrorDetail) as exc:
        validate_and_parse(data)
    
    assert "Minimal harus ada 1 kamar tidur" in str(exc.value)


def test_duplicate_room_names():
    """Test error jika ada nama ruangan duplikat"""
    data = copy.deepcopy(VALID_ENCODER_OUTPUT)
    data['rooms'][0]['name'] = 'living room'  # Duplikat dengan living room yang sudah ada
    
    with pytest.raises(ValidationErrorDetail) as exc:
        validate_and_parse(data)
    
    assert "Nama ruangan duplikat" in str(exc.value)


def test_invalid_links():
    """Test error jika links merujuk ke ruangan yang tidak ada"""
    data = copy.deepcopy(VALID_ENCODER_OUTPUT)
    # Pastikan tidak ada duplikat nama, baru ubah links
    data['rooms'][0]['links'] = ['non_existent_room']
    
    with pytest.raises(ValidationErrorDetail) as exc:
        validate_and_parse(data)
    
    # Pesan error harus menyebutkan link yang tidak valid
    assert "tidak merujuk ke ruangan yang valid" in str(exc.value)


def test_negative_size():
    """Test error jika ukuran negatif"""
    data = copy.deepcopy(VALID_ENCODER_OUTPUT)
    data['rooms'][0]['size']['width'] = -5.0
    
    with pytest.raises(ValidationErrorDetail) as exc:
        validate_and_parse(data)
    
    # Pesan error dari Pydantic v2: "greater than or equal to 0.5"
    assert "greater than or equal to 0.5" in str(exc.value).lower()


def test_missing_rooms_field():
    """Test error jika field 'rooms' hilang"""
    data = {"summary": {"bedroom": 1}}
    
    with pytest.raises(ValidationErrorDetail):
        validate_and_parse(data)


def test_process_encoder_output_success():
    """Test process_encoder_output dengan data valid"""
    result = process_encoder_output(VALID_ENCODER_OUTPUT)
    # Jika error, tampilkan detail untuk debugging
    if result['status'] == 'error':
        print(f"DEBUG: {result['error']}")
    assert result['status'] == 'success'
    assert 'validated_data' in result
    assert 'chd_format' in result
    assert result['total_area'] > 0


def test_process_encoder_output_error():
    """Test process_encoder_output dengan data invalid"""
    data = {"summary": {"bedroom": 1}}  # Tidak ada rooms
    
    result = process_encoder_output(data)
    assert result['status'] == 'error'
    assert 'error' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])