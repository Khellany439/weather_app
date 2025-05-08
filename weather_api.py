import os
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional, List

# API key for external weather service
API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5"

async def get_current_weather(location: str) -> Optional[Dict[str, Any]]:
    """Get current weather data for a location"""
    try:
        url = f"{BASE_URL}/weather"
        params = {
            "q": location,
            "appid": API_KEY,
            "units": "metric"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Format the response
                    return {
                        "location": data["name"],
                        "temperature": data["main"]["temp"],
                        "humidity": data["main"]["humidity"],
                        "wind_speed": data["wind"]["speed"],
                        "description": data["weather"][0]["description"],
                        "icon": data["weather"][0]["icon"],
                        "timestamp": datetime.utcfromtimestamp(data["dt"])
                    }
                else:
                    error_data = await response.json()
                    logging.error(f"Weather API error: {error_data}")
                    return None
    
    except Exception as e:
        logging.error(f"Error getting current weather: {str(e)}")
        return None

async def get_weather_forecast(location: str, days: int = 5) -> Optional[Dict[str, Any]]:
    """Get weather forecast for a location"""
    try:
        url = f"{BASE_URL}/forecast"
        params = {
            "q": location,
            "appid": API_KEY,
            "units": "metric",
            "cnt": days * 8  # 8 forecasts per day (3-hour steps)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Format the response
                    forecast_items = []
                    
                    # Get one forecast per day (noon)
                    for i in range(0, min(days * 8, len(data["list"])), 8):
                        item = data["list"][i]
                        forecast_items.append({
                            "date": datetime.utcfromtimestamp(item["dt"]),
                            "temperature": item["main"]["temp"],
                            "humidity": item["main"]["humidity"],
                            "wind_speed": item["wind"]["speed"],
                            "description": item["weather"][0]["description"],
                            "icon": item["weather"][0]["icon"]
                        })
                    
                    return {
                        "location": data["city"]["name"],
                        "forecast": forecast_items
                    }
                else:
                    error_data = await response.json()
                    logging.error(f"Weather API error: {error_data}")
                    return None
    
    except Exception as e:
        logging.error(f"Error getting weather forecast: {str(e)}")
        return None

async def get_historical_weather(location: str, date: datetime) -> Optional[Dict[str, Any]]:
    """Get historical weather data for a location"""
    # Note: This would require a different API endpoint and possibly a premium account
    # For this demo, we'll just return a placeholder response
    
    logging.warning("Historical weather data is not implemented")
    return {
        "location": location,
        "temperature": 15.0,
        "humidity": 70.0,
        "wind_speed": 5.0,
        "description": "Historical data placeholder",
        "icon": "01d",
        "timestamp": date
    }
