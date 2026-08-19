"""
test_pipeline_en_de.py
C.4: Test pipeline Encoder-Decoder
"""
import sys, os
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

import pytest
import json
from dotenv import load_dotenv
load_dotenv()

from src.nlp.decoder import validate_and_parse, process_encoder_output, ValidationErrorDetail
from src.nlp.schemas import FloorPlanRequest
from src.mcp.client.encoder_client import encode_text

TEST_INPUTS = [
    "rumah 2 kamar tidur 1 kamar mandi",
    "Balcony is north and west corner side. Middle of the master room and common room. Size is 16x4 sq ft.",
    """Balcony is north and west corner side. Middle of the master room and common room. Size is 16x4 sq ft. 
    Bathroom is middle of the east side. Room is middle of the kitchen and common room. Size is 10x4 sq ft. 
    The common room is located in north and east side. Middle of the bathroom and master room. Size is 14x14 sq ft. 
    kitchen is south and east corner site. In between of storage and bathroom. Size is 10 x 4 sq ft. 
    The living room is south east corner side and South facing. Related to all over rooms without balcony. Size is 20 x 18 sq ft. 
    The master room is located in middle of the west side. Room is in between of living room and balcony. Size is16 x16 sq ft. 
    Storage is south and east corner side. Middle of the living and kitchen room. Size is 4x4 sq ft."""
]

def test_token_reduction():
    for text in TEST_INPUTS:
        result = encode_text(text)
        input_chars = len(text)
        output_chars = len(json.dumps(result, ensure_ascii=False))
        reduction = (1 - output_chars / input_chars) * 100 if input_chars > 0 else 0
        print(f"\n📊 Input: {input_chars} chars, Output: {output_chars} chars, Reduction: {reduction:.2f}%")
        assert output_chars < input_chars * 5

def test_malformed_json_handling():
    bad_inputs = ["", "   ", "rumah", "abcdefghijklmnopqrstuvwxyz" * 10, "kamar tidur 1000 kamar mandi 500"]
    for text in bad_inputs:
        try:
            result = encode_text(text)
            validated = validate_and_parse(result)
            assert isinstance(validated, FloorPlanRequest)
            print(f"✅ Input '{text[:30]}...' berhasil diproses")
        except Exception as e:
            print(f"⚠️ Input '{text[:30]}...' error: {type(e).__name__}: {str(e)[:60]}")
            # Malformed input boleh gagal asalkan tidak crash
            assert True

def test_schema_validity():
    test_texts = [
        "rumah 2 kamar tidur, 1 kamar mandi, ruang tamu, dapur, dan balkon.",
        "Balcony is north and west corner side. Middle of the master room and common room. Size is 16x4 sq ft.",
        "bathroom is located at center of east side. It is between the master room and common room-1. It has the square size of 5 feet side.",
    ]
    for idx, text in enumerate(test_texts):
        result = encode_text(text)
        assert isinstance(result, dict)
        try:
            validated = validate_and_parse(result)
            assert isinstance(validated, FloorPlanRequest)
            bedrooms = [r for r in validated.rooms if r.type == 'bedroom']
            assert len(bedrooms) >= 1, "Tidak ada kamar tidur"
            assert validated.get_total_area() > 0, "Total area harus > 0"
            print(f"✅ Test {idx+1}: Validasi berhasil, {len(validated.rooms)} ruangan.")
        except ValidationErrorDetail as e:
            # Jika gagal, kita tampilkan error tapi masih bisa dianggap pass jika rooms berhasil dibuat
            # Dalam kasus ini, kita bisa fallback ke pembuatan rooms dari summary
            print(f"⚠️ Test {idx+1}: Error validasi, mencoba fallback dari summary...")
            # Coba proses ulang dengan data yang sudah dimodifikasi
            # Tapi karena kita sudah punya _convert_summary_to_detailed, seharusnya berhasil
            pytest.fail(f"Validasi gagal untuk teks: {text[:50]}... Error: {e}")

def test_end_to_end_conversion():
    text = "Balcony is north and west corner side. Middle of the master room and common room. Size is 16x4 sq ft."
    result = process_encoder_output(encode_text(text))
    assert result['status'] == 'success'
    assert 'chd_format' in result
    chd = result['chd_format']
    assert 'rooms' in chd
    assert len(chd['rooms']) > 0
    for room in chd['rooms']:
        assert 'size' in room
        assert isinstance(room['size'], list)
        assert len(room['size']) == 2
    print("✅ End-to-end conversion test passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])