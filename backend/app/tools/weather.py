import requests


def get_weather(city: str, unit: str = "celsius") -> dict:
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
    ).json()

    if not geo.get("results"):
        return {"error": f"city '{city}' not found"}

    loc = geo["results"][0]
    w = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current_weather": True,
            "temperature_unit": unit,
        },
    ).json()
    cw = w["current_weather"]
    return {
        "city": loc["name"],
        "temperature": cw["temperature"],
        "unit": unit,
        "windspeed": cw["windspeed"],
    }
