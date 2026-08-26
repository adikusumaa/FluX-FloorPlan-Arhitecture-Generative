"""
src/environment/analyzer.py
Environment Analysis: Geocoding, Weather, Sun Path, Noise Estimation, Solar Radiation.
Caching, rate limiting, and fallback.
"""
import math
import time
import requests
from functools import lru_cache
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

# ============================================================
# Data Classes
# ============================================================
@dataclass
class LocationInfo:
    display_name: str
    city: str
    country: str
    lat: float
    lon: float

@dataclass
class WeatherInfo:
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: float
    timestamp: str

@dataclass
class SunPathInfo:
    solar_declination: float
    optimal_orientation: str
    hemisphere: str
    solar_radiation: float
    sunrise: str
    sunset: str

@dataclass
class NoiseInfo:
    nearest_road_distance_km: float
    estimated_db: float

@dataclass
class EnvironmentReport:
    location: LocationInfo
    weather: WeatherInfo
    sun_path: SunPathInfo
    noise: NoiseInfo
    timestamp: str

# ============================================================
# Core Functions
# ============================================================
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_solar_declination(lat: float) -> dict:
    now = datetime.now()
    day_of_year = now.timetuple().tm_yday
    declination = 23.44 * math.sin(math.radians((360/365)*(284+day_of_year)))
    if lat > 0:
        orientation = "North-facing"
        hemisphere = "Northern"
    elif lat < 0:
        orientation = "South-facing"
        hemisphere = "Southern"
    else:
        orientation = "East/West - equatorial"
        hemisphere = "Equatorial"
    return {
        "solar_declination": round(declination, 2),
        "optimal_orientation": orientation,
        "hemisphere": hemisphere
    }

# ============================================================
# API Integrations
# ============================================================
@lru_cache(maxsize=128)
def reverse_geocode(lat: float, lon: float) -> LocationInfo:
    time.sleep(1)
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10}
    headers = {"User-Agent": "FluxAI-Environment/1.0"}
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
            return LocationInfo("Unknown", "Unknown", "Unknown", lat, lon)
    except Exception as e:
        print(f"[REVERSE_GEOCODE] Error: {e}")
        return LocationInfo("Unknown (fallback)", "Unknown", "Unknown", lat, lon)

@lru_cache(maxsize=128)
def get_weather(lat: float, lon: float) -> WeatherInfo:
    time.sleep(0.5)
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
            cur = data["current"]
            return WeatherInfo(
                cur.get("temperature_2m", 25.0),
                cur.get("relative_humidity_2m", 60.0),
                cur.get("wind_speed_10m", 3.0),
                cur.get("wind_direction_10m", 180.0),
                cur.get("time", datetime.now().isoformat())
            )
        else:
            return WeatherInfo(25.0, 60.0, 3.0, 180.0, datetime.now().isoformat())
    except Exception as e:
        print(f"[WEATHER] Error: {e}")
        return WeatherInfo(25.0, 60.0, 3.0, 180.0, datetime.now().isoformat())

@lru_cache(maxsize=128)
def get_solar_radiation(lat: float, lon: float) -> dict:
    time.sleep(0.5)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "sunrise,sunset",
        "current": "shortwave_radiation",
        "timezone": "auto",
        "forecast_days": 1
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        ghi = data.get("current", {}).get("shortwave_radiation", 0.0)
        sunrise = data.get("daily", {}).get("sunrise", [""])[0] if data.get("daily", {}).get("sunrise") else ""
        sunset = data.get("daily", {}).get("sunset", [""])[0] if data.get("daily", {}).get("sunset") else ""
        return {"ghi": ghi, "sunrise": sunrise, "sunset": sunset}
    except Exception as e:
        print(f"[SOLAR_RADIATION] Error: {e}")
        return {"ghi": 0.0, "sunrise": "", "sunset": ""}

# ============================================================
# Overpass API – dengan filter highway type
# ============================================================
def query_overpass(lat: float, lon: float, endpoint: str, timeout: int = 20) -> Optional[dict]:
    """
    Kirim query POST ke Overpass, ambil jalan dengan kelas utama dalam radius 500m.
    """
    radius = 500
    # Filter highway: primary, secondary, tertiary, trunk, motorway
    # Abaikan residential, service, unclassified untuk menghindari gang kecil
    query = f"""
    [out:json];
    way["highway"~"^(primary|secondary|tertiary|trunk|motorway)"](around:{radius},{lat},{lon});
    out center;
    """
    headers = {
        "Accept": "application/json",
        "User-Agent": "FluxAI-Environment/1.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        response = requests.post(
            endpoint,
            data={"data": query},
            headers=headers,
            timeout=timeout
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[OVERPASS] {endpoint} status {response.status_code}")
            return None
    except Exception as e:
        print(f"[OVERPASS] {endpoint} error: {e}")
        return None

def estimate_noise(lat: float, lon: float) -> NoiseInfo:
    """
    Estimasi kebisingan dari OpenStreetMap, hanya jalan utama.
    """
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.fr/api/interpreter",
    ]

    data = None
    for ep in endpoints:
        print(f"[NOISE] Trying {ep} ...")
        data = query_overpass(lat, lon, ep, timeout=20)
        if data is not None:
            print(f"[NOISE] Success from {ep}")
            break

    if data is None:
        print("[NOISE] All endpoints failed, using fallback 45 dB")
        return NoiseInfo(nearest_road_distance_km=0.5, estimated_db=45.0)

    min_dist_km = float('inf')
    if "elements" in data:
        for elem in data["elements"]:
            if "center" in elem:
                c = elem["center"]
                rlat = c.get("lat")
                rlon = c.get("lon")
            elif "lat" in elem and "lon" in elem:
                rlat = elem["lat"]
                rlon = elem["lon"]
            else:
                continue
            if rlat is not None and rlon is not None:
                d = haversine_distance(lat, lon, rlat, rlon)
                if d < min_dist_km:
                    min_dist_km = d

    if min_dist_km == float('inf'):
        # Tidak ada jalan utama dalam radius 500m
        return NoiseInfo(nearest_road_distance_km=5.0, estimated_db=25.0)

    dist_m = min_dist_km * 1000
    if dist_m < 10:
        db = 70.0
    else:
        db = max(25.0, 70.0 - 20 * math.log10(dist_m + 1))

    return NoiseInfo(
        nearest_road_distance_km=round(min_dist_km, 4),
        estimated_db=round(db, 1)
    )

# ============================================================
# Main Analyzer
# ============================================================
def analyze_environment(lat: float, lon: float) -> EnvironmentReport:
    location = reverse_geocode(lat, lon)
    weather = get_weather(lat, lon)
    sun_calc = calculate_solar_declination(lat)
    solar_data = get_solar_radiation(lat, lon)
    noise = estimate_noise(lat, lon)

    return EnvironmentReport(
        location=location,
        weather=weather,
        sun_path=SunPathInfo(
            solar_declination=sun_calc["solar_declination"],
            optimal_orientation=sun_calc["optimal_orientation"],
            hemisphere=sun_calc["hemisphere"],
            solar_radiation=solar_data.get("ghi", 0.0),
            sunrise=solar_data.get("sunrise", ""),
            sunset=solar_data.get("sunset", "")
        ),
        noise=noise,
        timestamp=datetime.now().isoformat()
    )

# ============================================================
# Testing
# ============================================================
if __name__ == "__main__":
    test_lat, test_lon = -6.2088, 106.8456
    report = analyze_environment(test_lat, test_lon)
    print("="*60)
    print("Environment Report")
    print("="*60)
    print(f"Location: {report.location.city}, {report.location.country}")
    print(f"Temperature: {report.weather.temperature} C, Humidity: {report.weather.humidity}%")
    print(f"Wind: {report.weather.wind_speed} m/s, direction {report.weather.wind_direction} deg")
    print(f"Solar declination: {report.sun_path.solar_declination} deg -> {report.sun_path.optimal_orientation}")
    print(f"Solar radiation: {report.sun_path.solar_radiation} W/m2")
    print(f"Sunrise: {report.sun_path.sunrise}, Sunset: {report.sun_path.sunset}")
    print(f"Noise: {report.noise.estimated_db} dB (nearest road distance: {report.noise.nearest_road_distance_km} km)")
    print("="*60)