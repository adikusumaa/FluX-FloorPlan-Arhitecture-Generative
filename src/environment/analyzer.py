"""
src/environment/analyzer.py
Environment Analysis: Geocoding, Weather, Sun Path, Noise Estimation.
Optimized with caching, rate limiting, and fallback.
"""
import math
import time
import requests
import json
from functools import lru_cache
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# ============================================================
# Data Classes untuk Output
# ============================================================
@dataclass
class LocationInfo:
    """Hasil reverse geocoding"""
    display_name: str
    city: str
    country: str
    lat: float
    lon: float

@dataclass
class WeatherInfo:
    """Hasil Open-Meteo"""
    temperature: float      # °C
    humidity: float         # %
    wind_speed: float       # m/s
    wind_direction: float   # degrees
    timestamp: str

@dataclass
class SunPathInfo:
    """Hasil kalkulasi matahari"""
    solar_declination: float  # derajat
    optimal_orientation: str  # Rekomendasi arah jendela
    hemisphere: str

@dataclass
class NoiseInfo:
    """Hasil estimasi kebisingan"""
    nearest_road_distance_km: float
    estimated_db: float  # estimasi desibel (A-weighting sederhana)

@dataclass
class EnvironmentReport:
    """Laporan lengkap lingkungan"""
    location: LocationInfo
    weather: WeatherInfo
    sun_path: SunPathInfo
    noise: NoiseInfo
    timestamp: str

# ============================================================
# Core Functions
# ============================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Menghitung jarak antara dua titik koordinat dalam KILOMETER.
    """
    R = 6371.0  # Radius bumi dalam km
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def calculate_solar_declination(lat: float) -> dict:
    """
    Menghitung deklinasi matahari berdasarkan hari dalam setahun dan latitude.
    Rekomendasi orientasi jendela berdasarkan posisi matahari.
    """
    now = datetime.now()
    day_of_year = now.timetuple().tm_yday

    # Deklinasi matahari (dalam derajat)
    declination = 23.44 * math.sin(math.radians((360 / 365) * (284 + day_of_year)))

    # Rekomendasi orientasi
    if lat > 0:
        # Belahan bumi utara: jendela menghadap selatan untuk cahaya maksimal
        orientation = "Selatan (South-facing)"
        hemisphere = "Utara"
    elif lat < 0:
        # Belahan bumi selatan: jendela menghadap utara
        orientation = "Utara (North-facing)"
        hemisphere = "Selatan"
    else:
        orientation = "Timur/Barat (East/West) - dekat khatulistiwa"
        hemisphere = "Khatulistiwa"

    return {
        "solar_declination": round(declination, 2),
        "optimal_orientation": orientation,
        "hemisphere": hemisphere
    }


# ============================================================
# API Integrations (with Caching & Rate Limiting)
# ============================================================

@lru_cache(maxsize=128)
def reverse_geocode(lat: float, lon: float) -> Optional[LocationInfo]:
    """
    Reverse geocoding via Nominatim.
    Cache: menyimpan hasil untuk koordinat yang sama.
    Rate Limit: sleep 1 detik untuk mematuhi kebijakan Nominatim.
    """
    time.sleep(1)  # Rate limit: 1 request per second

    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 10
    }
    headers = {
        "User-Agent": "FluxAI-Environment/1.0 (your_email@example.com)"  # Ganti dengan email Anda
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "address" in data:
            address = data["address"]
            city = address.get("city") or address.get("town") or address.get("village") or address.get("county", "Unknown")
            country = address.get("country", "Unknown")
            return LocationInfo(
                display_name=data.get("display_name", ""),
                city=city,
                country=country,
                lat=lat,
                lon=lon
            )
        else:
            return LocationInfo(
                display_name="Unknown Location",
                city="Unknown",
                country="Unknown",
                lat=lat,
                lon=lon
            )
    except Exception as e:
        print(f"⚠️ Reverse geocoding gagal: {e}")
        # Fallback
        return LocationInfo(
            display_name="Unknown (Fallback)",
            city="Unknown",
            country="Unknown",
            lat=lat,
            lon=lon
        )


@lru_cache(maxsize=128)
def get_weather(lat: float, lon: float) -> Optional[WeatherInfo]:
    """
    Mendapatkan data cuaca dari Open-Meteo.
    Cache: menyimpan hasil untuk koordinat yang sama.
    Rate Limit: tidak ada batasan ketat, tapi tetap beri jeda.
    """
    time.sleep(0.5)  # Jeda kecil untuk menghindari spam

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m",
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "current" in data:
            current = data["current"]
            return WeatherInfo(
                temperature=current.get("temperature_2m", 25.0),
                humidity=current.get("relative_humidity_2m", 60.0),
                wind_speed=current.get("wind_speed_10m", 3.0),
                wind_direction=current.get("wind_direction_10m", 180.0),
                timestamp=current.get("time", datetime.now().isoformat())
            )
        else:
            # Fallback
            return WeatherInfo(
                temperature=25.0,
                humidity=60.0,
                wind_speed=3.0,
                wind_direction=180.0,
                timestamp=datetime.now().isoformat()
            )
    except Exception as e:
        print(f"⚠️ Weather API gagal: {e}")
        # Fallback safe
        return WeatherInfo(
            temperature=25.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction=180.0,
            timestamp=datetime.now().isoformat()
        )


def estimate_noise(lat: float, lon: float) -> NoiseInfo:
    """
    Estimasi kebisingan dengan mencari jalan terdekat dari OSM (Overpass API).
    Menggunakan Haversine untuk menghitung jarak.
    """
    time.sleep(1)  # Rate limit

    # Overpass query: cari way dengan highway dalam radius 1 km
    radius = 1000  # meter
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      way["highway"](around:{radius},{lat},{lon});
    );
    out center;
    """

    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=15)
        response.raise_for_status()
        data = response.json()

        min_distance_km = float('inf')
        if "elements" in data:
            for element in data["elements"]:
                # 'center' biasanya ada untuk way jika out center
                if "center" in element:
                    center = element["center"]
                    road_lat = center.get("lat")
                    road_lon = center.get("lon")
                elif "lat" in element and "lon" in element:
                    road_lat = element["lat"]
                    road_lon = element["lon"]
                else:
                    continue

                if road_lat is not None and road_lon is not None:
                    dist = haversine_distance(lat, lon, road_lat, road_lon)
                    if dist < min_distance_km:
                        min_distance_km = dist

        # Estimasi dB berdasarkan jarak (logaritmik sederhana, hanya untuk ilustrasi)
        if min_distance_km == float('inf'):
            # Tidak ada jalan dalam radius 1 km, anggap sepi
            estimated_db = 30.0
            min_distance_km = 5.0
        else:
            # Formula sederhana: 70 dB di 0 km, turun ~6 dB setiap jarak lipat 2
            # dB = 70 - 20 * log10(distance_m + 1) (jeda aman)
            distance_m = min_distance_km * 1000
            if distance_m < 10:
                estimated_db = 70.0
            else:
                estimated_db = max(30.0, 70.0 - 20 * math.log10(distance_m + 1))

        return NoiseInfo(
            nearest_road_distance_km=round(min_distance_km, 4),
            estimated_db=round(estimated_db, 1)
        )

    except Exception as e:
        print(f"⚠️ Overpass API gagal: {e}")
        # Fallback: asumsikan noise standar perkotaan (50 dB)
        return NoiseInfo(
            nearest_road_distance_km=0.5,
            estimated_db=50.0
        )


# ============================================================
# Main Analyzer Function
# ============================================================
def analyze_environment(lat: float, lon: float) -> EnvironmentReport:
    """
    Fungsi utama untuk mengumpulkan semua data lingkungan.
    """
    location = reverse_geocode(lat, lon)
    weather = get_weather(lat, lon)
    sun_path = calculate_solar_declination(lat)
    noise = estimate_noise(lat, lon)

    return EnvironmentReport(
        location=location,
        weather=weather,
        sun_path=SunPathInfo(
            solar_declination=sun_path["solar_declination"],
            optimal_orientation=sun_path["optimal_orientation"],
            hemisphere=sun_path["hemisphere"]
        ),
        noise=noise,
        timestamp=datetime.now().isoformat()
    )


# ============================================================
# Jika dijalankan langsung (testing manual)
# ============================================================
if __name__ == "__main__":
    # Contoh: koordinat Jakarta
    test_lat, test_lon = -6.2088, 106.8456
    report = analyze_environment(test_lat, test_lon)

    print("="*60)
    print("🌍 Environment Report")
    print("="*60)
    print(f"📍 Lokasi: {report.location.city}, {report.location.country}")
    print(f"🌡️  Suhu: {report.weather.temperature}°C, Kelembaban: {report.weather.humidity}%")
    print(f"💨 Angin: {report.weather.wind_speed} m/s (arah {report.weather.wind_direction}°)")
    print(f"☀️ Deklinasi: {report.sun_path.solar_declination}° -> Rekomendasi: {report.sun_path.optimal_orientation}")
    print(f"🔊 Noise: {report.noise.estimated_db} dB (jarak ke jalan terdekat: {report.noise.nearest_road_distance_km} km)")
    print("="*60)