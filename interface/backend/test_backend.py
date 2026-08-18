# test_backend.py
import requests
import json

url = "http://localhost:8000/api/v1/generate"
payload = {
    "user_text": "Saya mau rumah 3 kamar tidur, 2 kamar mandi, luas 120m²",
    "weights": [0.25, 0.25, 0.25, 0.25],
    "location": {"lat": -6.2, "lng": 106.8}
}

response = requests.post(url, json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response JSON: {json.dumps(response.json(), indent=2)}")

# Assertions
assert response.status_code == 200, "Gagal: Status code bukan 200"
data = response.json()
assert "status" in data, "Gagal: Key 'status' tidak ada"
assert data["status"] == "success", "Gagal: Status bukan 'success'"
assert "data" in data, "Gagal: Key 'data' tidak ada"
assert len(data["data"]) == 5, f"Gagal: Jumlah data harus 5, tapi dapat {len(data['data'])}"
print("\n✅ Semua test PASS! Backend berfungsi dengan benar.")