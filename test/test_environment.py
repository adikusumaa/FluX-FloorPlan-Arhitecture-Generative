"""
tests/test_environment.py
Unit test untuk Environment Analysis (D).
"""
import sys
import os

# ============================================================
# 1. Tambahkan root proyek dan folder src ke sys.path
# ============================================================
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(root_dir, "src")

print(f"DEBUG: root_dir = {root_dir}")
print(f"DEBUG: src_dir = {src_dir}")
print(f"DEBUG: sys.path before = {sys.path[:2]}")

# Masukkan root dan src ke depan path
sys.path.insert(0, root_dir)
sys.path.insert(0, src_dir)

print(f"DEBUG: sys.path after = {sys.path[:2]}")

# ============================================================
# 2. Sekarang import dari src
# ============================================================
import pytest
import json
from unittest.mock import patch, MagicMock

from src.environment.analyzer import (
    haversine_distance,
    calculate_solar_declination,
    reverse_geocode,
    get_weather,
    estimate_noise,
    analyze_environment
)

# ============================================================
# 3. Test functions (sama seperti sebelumnya)
# ============================================================
def test_haversine():
    dist = haversine_distance(-6.2088, 106.8456, -6.9175, 107.6191)
    assert 100 < dist < 150
    dist_same = haversine_distance(-6.2, 106.8, -6.2, 106.8)
    assert dist_same == 0.0

def test_solar_declination():
    result = calculate_solar_declination(-6.2)
    assert "solar_declination" in result
    assert "optimal_orientation" in result
    assert "hemisphere" in result
    assert result["hemisphere"] == "Selatan"

    result_north = calculate_solar_declination(50.0)
    assert result_north["hemisphere"] == "Utara"

@patch('src.environment.analyzer.requests.get')
def test_reverse_geocode_mock(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "display_name": "Jakarta, Indonesia",
        "address": {"city": "Jakarta", "country": "Indonesia"}
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = reverse_geocode(-6.2, 106.8)
    assert result.city == "Jakarta"
    assert result.country == "Indonesia"

@patch('src.environment.analyzer.requests.get')
def test_weather_mock(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "current": {
            "temperature_2m": 28.5,
            "relative_humidity_2m": 75.0,
            "wind_speed_10m": 4.2,
            "wind_direction_10m": 200.0,
            "time": "2025-01-01T12:00"
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = get_weather(-6.2, 106.8)
    assert result.temperature == 28.5
    assert result.humidity == 75.0

def test_analyze_environment_fallback():
    report = analyze_environment(-6.2, 106.8)
    assert report.location is not None
    assert report.weather is not None
    assert report.sun_path is not None
    assert report.noise is not None
    assert report.timestamp is not None

    assert isinstance(report.location.city, str)
    assert isinstance(report.weather.temperature, float)
    assert isinstance(report.sun_path.solar_declination, float)
    assert isinstance(report.noise.estimated_db, float)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])