import os
import requests
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Weather API configuration
# Using OpenWeatherMap API
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
WEATHER_API_BASE_URL = "https://api.openweathermap.org/data/2.5"

def get_current_weather(location):
    """
    Get current weather data for a location
    
    Args:
        location (str): City name, address, or coordinates
        
    Returns:
        dict: Weather data or None if request failed
    """
    try:
        url = f"{WEATHER_API_BASE_URL}/weather"
        params = {
            "q": location,
            "appid": WEATHER_API_KEY,
            "units": "metric"  # Use metric units (Celsius)
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        
        # Format the response data
        weather_data = {
            "location": data["name"],
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "timestamp": datetime.now().isoformat()
        }
        
        return weather_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching current weather: {str(e)}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing weather data: {str(e)}")
        return None

def get_weather_forecast(location, days=5):
    """
    Get weather forecast for a location
    
    Args:
        location (str): City name, address, or coordinates
        days (int): Number of days for forecast (max 5)
        
    Returns:
        dict: Forecast data or None if request failed
    """
    try:
        url = f"{WEATHER_API_BASE_URL}/forecast"
        params = {
            "q": location,
            "appid": WEATHER_API_KEY,
            "units": "metric"  # Use metric units (Celsius)
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        
        # Process forecast data (OpenWeatherMap returns forecast in 3-hour intervals)
        # We'll aggregate to daily forecasts
        daily_forecasts = {}
        
        for item in data["list"]:
            # Parse timestamp
            dt = datetime.fromtimestamp(item["dt"])
            date_key = dt.date().isoformat()
            
            # Skip if we already have enough days
            if len(daily_forecasts) >= days and date_key not in daily_forecasts:
                continue
            
            # Initialize daily data if this is a new day
            if date_key not in daily_forecasts:
                daily_forecasts[date_key] = {
                    "date": date_key,
                    "temperatures": [],
                    "humidity": [],
                    "wind_speed": [],
                    "descriptions": [],
                    "icons": []
                }
            
            # Add data points
            daily_forecasts[date_key]["temperatures"].append(item["main"]["temp"])
            daily_forecasts[date_key]["humidity"].append(item["main"]["humidity"])
            daily_forecasts[date_key]["wind_speed"].append(item["wind"]["speed"])
            daily_forecasts[date_key]["descriptions"].append(item["weather"][0]["description"])
            daily_forecasts[date_key]["icons"].append(item["weather"][0]["icon"])
        
        # Calculate averages and pick most common description and icon
        forecast_list = []
        for date_key, day_data in sorted(daily_forecasts.items())[:days]:
            forecast_list.append({
                "date": date_key,
                "temperature": sum(day_data["temperatures"]) / len(day_data["temperatures"]),
                "humidity": sum(day_data["humidity"]) / len(day_data["humidity"]),
                "wind_speed": sum(day_data["wind_speed"]) / len(day_data["wind_speed"]),
                "description": max(set(day_data["descriptions"]), key=day_data["descriptions"].count),
                "icon": max(set(day_data["icons"]), key=day_data["icons"].count)
            })
        
        return {
            "location": data["city"]["name"],
            "forecast": forecast_list
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather forecast: {str(e)}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing forecast data: {str(e)}")
        return None

def get_historical_weather(location, date):
    """
    Get historical weather data for a location
    
    Args:
        location (str): City name, address, or coordinates
        date (datetime): Date for historical data
        
    Returns:
        dict: Historical weather data or None if request failed
    """
    # Note: OpenWeatherMap's free tier doesn't include historical data
    # For demonstration purposes, we'll return a simulated response
    # In a production environment, you would use a proper historical weather API
    
    try:
        # Simulate a delayed response for demonstration
        # In a real application, you would call the actual API
        
        # Get current weather as a base
        current = get_current_weather(location)
        
        if not current:
            return None
        
        # Modify to simulate historical data
        historical_data = {
            "location": current["location"],
            "temperature": current["temperature"] - 2,  # Simulate different temperature
            "humidity": current["humidity"],
            "wind_speed": current["wind_speed"] * 0.8,
            "description": current["description"],
            "icon": current["icon"],
            "timestamp": date.isoformat(),
            "note": "Note: This is simulated historical data for demonstration purposes."
        }
        
        return historical_data
    
    except Exception as e:
        logger.error(f"Error fetching historical weather: {str(e)}")
        return None