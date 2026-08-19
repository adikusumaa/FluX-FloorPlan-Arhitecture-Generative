# test_encoder.py
import sys
import os
# Naik satu level ke root proyek
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.client.encoder_client import encode_text
import json

if __name__ == "__main__":
    # Test cases in English
    test_inputs = [
        "Balcony is north and west  corner side. Middle of the master room and common room. Size is 16x4 sq ft. Bathroom is middle of the east side. Room is middle of the kitchen and common room. Size is 10x4 sq ft. The common room is located in north and east side. Middle of the bathroom and master room. Size is 14x14 sq ft. kitchen is south and east corner site. In between of storage and bathroom. Size is 10 x 4 sq ft. The living room is south east corner side and South facing. Related to all over rooms without balcony. Size is 20 x 18 sq ft. The master room is located in middle of the west side. Room is in between of living room and balcony. Size is16 x16 sq ft. Storage is south and east corner side. Middle of the living and kitchen room. Size is 4x4 sq ft. ",
        "balcony at south direction downside of living room size 10*3 feet bathroom1 at east direction upside of master room size 6*6 feet bathroom2 at north direction right side of kitchen size 6*6 feet common room1 at north east corner upside of bathroom1 size 10*10 feet common room 2 at north direction right side of bathroom 2 size 10*10 feet kitchen at north east corner upside of living room size 10*5 feet living room at south west corner  left side of master room and bathroom1 size 20*15 feet master room at south east corner downside of  batroom1 size 6*6 feet",
        "bathroom is located at center of east side. It is between the master room and common room-1. It has the square size of 5 feet side. common room-1 is located at south east corner and it is in front of bathroom. It has the size of 10 feet width and 12 feet length. common room-2 is located at north west corner and adjacent to living room. It has the size of 7 feet width and 10 feet length. common room-3 is located at the center of south side. It is between the kitchen and common room-1. It has the size of 12 feet length and 8 feet width. kitchen is located at south west corner. It is near the common room-3.  It has the size of 12 feet length and 5 feet width. Living room is occupied the center area of north side. It is between the common room-2 and master room. It has the area of  around 380 sqr. feet. master room is located at north east corner and adjacent to living room. It has the square size of 14 feet side. "
    ]
    
    print("="*60)
    print("🧪 Testing Encoder Server")
    print("="*60)
    
    for i, text in enumerate(test_inputs, 1):
        print(f"\n📝 Test {i}: {text[:60]}...")
        try:
            result = encode_text(text)
            print("✅ JSON Output:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Optional: show reduction (approximate)
            input_chars = len(text)
            output_chars = len(json.dumps(result, ensure_ascii=False))
            reduction = (1 - output_chars / input_chars) * 100
            print(f"📊 Character reduction: {reduction:.1f}%")
        except Exception as e:
            print(f"❌ Error: {e}")