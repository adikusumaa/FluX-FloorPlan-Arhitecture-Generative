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
        "阳台位于西北角，介于主卧和公共房间之间，尺寸为16x4平方英尺。浴室位于东侧中部，介于厨房和公共房间之间，尺寸为10x4平方英尺。公共房间位于东北侧，介于浴室和主卧之间，尺寸为14x14平方英尺。厨房位于东南角，介于储物间和浴室之间，尺寸为10x4平方英尺。客厅位于东南角，朝南，与除阳台外的所有房间相连，尺寸为20x18平方英尺。主卧位于西侧中部，介于客厅和阳台之间，尺寸为16x16平方英尺。储物间位于东南角，介于客厅和厨房之间，尺寸为4x4平方英尺。"
    ]
    
    print("="*60)
    print("[TESTING] Testing Encoder Server")
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