import json
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import certifi
from mcp.server.fastmcp import FastMCP

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 15
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

WEATHER_CODE_LABELS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

CURRENT_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "is_day",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
]

mcp = FastMCP(
    name="simple-weather",
    instructions=(
        "Use this server to get the current weather for a single location using "
        "latitude and longitude, with optional elevation tuning."
    ),
)


def _fetch_weather(latitude: float, longitude: float, elevation: float | None) -> dict[str, Any]:
    params: dict[str, str | float] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(CURRENT_VARIABLES),
        "timezone": "auto",
    }
    if elevation is not None:
        params["elevation"] = elevation

    url = f"{WEATHER_API_URL}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS, context=SSL_CONTEXT) as response:
            payload = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Weather API returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach weather API: {exc.reason}") from exc

    current = payload.get("current")
    current_units = payload.get("current_units")
    if not current or not current_units:
        raise RuntimeError(f"Unexpected weather API response: {payload}")

    weather_code = current.get("weather_code")

    return {
        "source": "Open-Meteo",
        "requested_location": {
            "latitude": latitude,
            "longitude": longitude,
            "elevation": elevation,
        },
        "resolved_location": {
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "elevation": payload.get("elevation"),
            "timezone": payload.get("timezone"),
            "timezone_abbreviation": payload.get("timezone_abbreviation"),
        },
        "current_weather": {
            "time": current.get("time"),
            "temperature": {
                "value": current.get("temperature_2m"),
                "unit": current_units.get("temperature_2m"),
            },
            "apparent_temperature": {
                "value": current.get("apparent_temperature"),
                "unit": current_units.get("apparent_temperature"),
            },
            "relative_humidity": {
                "value": current.get("relative_humidity_2m"),
                "unit": current_units.get("relative_humidity_2m"),
            },
            "precipitation": {
                "value": current.get("precipitation"),
                "unit": current_units.get("precipitation"),
            },
            "cloud_cover": {
                "value": current.get("cloud_cover"),
                "unit": current_units.get("cloud_cover"),
            },
            "wind_speed": {
                "value": current.get("wind_speed_10m"),
                "unit": current_units.get("wind_speed_10m"),
            },
            "wind_gusts": {
                "value": current.get("wind_gusts_10m"),
                "unit": current_units.get("wind_gusts_10m"),
            },
            "wind_direction_degrees": current.get("wind_direction_10m"),
            "is_day": bool(current.get("is_day")),
            "weather_code": weather_code,
            "weather_description": WEATHER_CODE_LABELS.get(weather_code, "Unknown"),
        },
    }


@mcp.tool(
    name="get_weather",
    description="Get the current weather for one location using latitude and longitude.",
)
def get_weather(
    latitude: float,
    longitude: float,
    elevation: float | None = None,
) -> dict[str, Any]:
    """Return current weather for a single location."""
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")

    return _fetch_weather(latitude=latitude, longitude=longitude, elevation=elevation)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
