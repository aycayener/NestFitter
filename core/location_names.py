import requests

def reverse_geocode(lat, lon):
    """
    Nominatim (OpenStreetMap) reverse geocoding
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "json",
        "lat": lat,
        "lon": lon,
        "zoom": 14,
        "addressdetails": 1
    }

    headers = {
        "User-Agent": "ev-yasam-oneri-sistemi"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()

        address = data.get("address", {})
        district = address.get("district") or address.get("county")
        neighbourhood = address.get("neighbourhood") or address.get("suburb")

        parts = [p for p in [neighbourhood, district] if p]
        return ", ".join(parts) if parts else "Bölge adı bulunamadı"

    except Exception:
        return "Bölge adı bulunamadı"
