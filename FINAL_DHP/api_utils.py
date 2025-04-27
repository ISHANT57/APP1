import os
import json
import logging
import requests
from datetime import datetime
from config import IQAIR_API_KEY, IQAIR_API_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
AQICN_API_KEY = os.environ.get('AQICN_API_KEY')
AQICN_BASE_URL = "https://api.waqi.info"

# India boundaries for map view
INDIA_BOUNDS = {
    "south": 6.7,  # Southern-most point of India
    "west": 68.1,  # Western-most point of India
    "north": 35.1, # Northern-most point of India
    "east": 97.4   # Eastern-most point of India
}

def get_city_air_quality(city_name):
    """
    Get air quality data for a specific city
    
    Args:
        city_name (str): Name of the city
        
    Returns:
        dict: Air quality data for the city
    """
    try:
        url = f"{AQICN_BASE_URL}/feed/{city_name}/?token={AQICN_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'ok':
            return data['data']
        else:
            logger.warning(f"Failed to fetch air quality data for {city_name}: {data.get('data')}")
            return None
    except Exception as e:
        logger.error(f"Error fetching air quality data for {city_name}: {e}")
        return None

def get_india_air_quality_map_data():
    """
    Get air quality data for all stations in India
    
    Returns:
        list: List of air quality stations with coordinates and AQI values
    """
    try:
        bounds = f"{INDIA_BOUNDS['south']},{INDIA_BOUNDS['west']},{INDIA_BOUNDS['north']},{INDIA_BOUNDS['east']}"
        url = f"{AQICN_BASE_URL}/map/bounds/?latlng={bounds}&token={AQICN_API_KEY}"
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'ok':
            # Transform the data to match our expected format
            markers = []
            for station in data['data']:
                aqi_value = float(station['aqi']) if station['aqi'] not in ['-', '', None] else 0
                
                # Determine AQI category and color
                category, color = get_aqi_category_and_color(aqi_value)
                
                # Get weather data for this station
                weather = {}
                station_uid = station.get('uid')
                if station_uid:
                    weather = get_station_weather_data(station_uid)
                
                marker = {
                    "Country": "India",
                    "City": station['station']['name'].split(',')[0].strip(),
                    "AQI": aqi_value,
                    "AQI_Category": category,
                    "Latitude": station['lat'],
                    "Longitude": station['lon'],
                    "Continent": "Asia",
                    "color": color,
                    "time": station['station']['time'],
                    "wind_speed": weather.get('wind_speed', "3.5"),
                    "wind_direction": weather.get('wind_direction', "120"),
                    "temperature": weather.get('temperature', "28")
                }
                markers.append(marker)
            
            # Cache the data
            save_map_data_to_cache(markers)
            
            return markers
        else:
            logger.warning(f"Failed to fetch air quality map data: {data.get('data')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching air quality map data: {e}")
        return []

def get_global_air_quality_map_data():
    """
    Get global air quality data
    """
    try:
        url = f"{AQICN_BASE_URL}/map/bounds/?latlng=-90,-180,90,180&token={AQICN_API_KEY}"
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'ok':
            # Transform the data to match our expected format
            markers = []
            for station in data['data']:
                try:
                    aqi_value = float(station['aqi']) if station['aqi'] not in ['-', '', None] else 0
                    
                    # Determine AQI category and color
                    category, color = get_aqi_category_and_color(aqi_value)
                    
                    # Parse location
                    location_parts = station['station']['name'].split(',')
                    city = location_parts[0].strip()
                    country = location_parts[-1].strip() if len(location_parts) > 1 else "Unknown"
                    
                    # Simplify country names
                    if country.lower().startswith("united states"):
                        country = "USA"
                    elif country.lower() == "united kingdom":
                        country = "UK"
                    
                    # Get weather data for this station
                    weather = {}
                    station_uid = station.get('uid')
                    if station_uid:
                        weather = get_station_weather_data(station_uid)
                        
                    marker = {
                        "Country": country,
                        "City": city,
                        "AQI": aqi_value,
                        "AQI_Category": category,
                        "Latitude": station['lat'],
                        "Longitude": station['lon'],
                        "color": color,
                        "time": station['station']['time'],
                        "wind_speed": weather.get('wind_speed', "3.5"),
                        "wind_direction": weather.get('wind_direction', "120"),
                        "temperature": weather.get('temperature', "28")
                    }
                    markers.append(marker)
                except Exception as e:
                    # Skip invalid entries
                    logger.debug(f"Skipping invalid entry: {e}")
                    continue
            
            return markers
        else:
            logger.warning(f"Failed to fetch global air quality map data: {data.get('data')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching global air quality map data: {e}")
        return []

def get_aqi_category_and_color(aqi_value):
    """
    Determine AQI category and color based on AQI value
    
    Args:
        aqi_value (float): AQI value
        
    Returns:
        tuple: (category, color)
    """
    if aqi_value <= 50:
        return "Good", "green"
    elif aqi_value <= 100:
        return "Moderate", "yellow"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups", "orange"
    elif aqi_value <= 200:
        return "Unhealthy", "red"
    elif aqi_value <= 300:
        return "Very Unhealthy", "purple"
    else:
        return "Hazardous", "maroon"

def save_map_data_to_cache(data):
    """
    Save map data to a cache file
    
    Args:
        data (list): List of marker data
    """
    try:
        cache_dir = 'static/data/cache'
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, 'india_aqi_data.json')
        with open(cache_file, 'w') as f:
            json.dump(data, f)
            
        logger.info(f"Saved map data to cache: {len(data)} stations")
    except Exception as e:
        logger.error(f"Error saving map data to cache: {e}")

def get_cached_map_data():
    """
    Get cached map data
    
    Returns:
        list: List of marker data
    """
    try:
        cache_file = 'static/data/cache/india_aqi_data.json'
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded cached map data: {len(data)} stations")
            return data
        else:
            logger.info("No cached map data found")
            return []
    except Exception as e:
        logger.error(f"Error loading cached map data: {e}")
        return []

def get_station_weather_data(station_id):
    """
    Get weather data for a station
    
    Args:
        station_id (str): Station ID
        
    Returns:
        dict: Weather data including wind speed, direction, and temperature
    """
    try:
        url = f"{AQICN_BASE_URL}/feed/@{station_id}/?token={AQICN_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'ok':
            weather_data = {}
            
            # Extract weather data from AQICN API response
            iaqi = data['data'].get('iaqi', {})
            
            # Get wind speed
            if 'w' in iaqi and 'v' in iaqi['w']:
                weather_data['wind_speed'] = iaqi['w']['v']
            elif 'wind' in iaqi and 'v' in iaqi['wind']:
                weather_data['wind_speed'] = iaqi['wind']['v']
            else:
                # Default wind speed
                weather_data['wind_speed'] = "3.5"
                
            # Get wind direction
            if 'wd' in iaqi and 'v' in iaqi['wd']:
                weather_data['wind_direction'] = iaqi['wd']['v']
            elif 'wg' in iaqi and 'v' in iaqi['wg']:
                weather_data['wind_direction'] = iaqi['wg']['v']
            else:
                # Default wind direction
                weather_data['wind_direction'] = "120"
                
            # Get temperature
            if 't' in iaqi and 'v' in iaqi['t']:
                weather_data['temperature'] = iaqi['t']['v']
            elif 'temp' in iaqi and 'v' in iaqi['temp']:
                weather_data['temperature'] = iaqi['temp']['v']
            else:
                # Default temperature
                weather_data['temperature'] = "28"
                
            return weather_data
        else:
            logger.warning(f"Failed to fetch weather data for station {station_id}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching weather data for station {station_id}: {e}")
        return {}


# IQAir API Functions

def get_iqair_countries():
    """
    Get list of countries supported by IQAir API
    
    Returns:
        list: List of countries
    """
    try:
        url = f"{IQAIR_API_URL}/countries?key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            return data['data']
        else:
            logger.warning(f"Failed to fetch countries from IQAir: {data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching countries from IQAir: {e}")
        return []
        
def get_iqair_states(country):
    """
    Get list of states/regions for a country supported by IQAir API
    
    Args:
        country (str): Country name
        
    Returns:
        list: List of states/regions
    """
    try:
        url = f"{IQAIR_API_URL}/states?country={country}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            return data['data']
        else:
            logger.warning(f"Failed to fetch states from IQAir: {data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching states from IQAir: {e}")
        return []
        
def get_iqair_cities(country, state):
    """
    Get list of cities for a state/region supported by IQAir API
    
    Args:
        country (str): Country name
        state (str): State/region name
        
    Returns:
        list: List of cities
    """
    try:
        url = f"{IQAIR_API_URL}/cities?country={country}&state={state}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            return data['data']
        else:
            logger.warning(f"Failed to fetch cities from IQAir: {data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching cities from IQAir: {e}")
        return []
        
def get_iqair_city_data(country, state, city):
    """
    Get air quality data for a specific city using IQAir API
    
    Args:
        country (str): Country name
        state (str): State/region name
        city (str): City name
        
    Returns:
        dict: Air quality data for the city
    """
    try:
        url = f"{IQAIR_API_URL}/city?country={country}&state={state}&city={city}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            return data['data']
        else:
            logger.warning(f"Failed to fetch city data from IQAir: {data.get('message')}")
            return None
    except Exception as e:
        logger.error(f"Error fetching city data from IQAir: {e}")
        return None
        
def get_iqair_nearest_city(lat, lon):
    """
    Get air quality data for the nearest city using IQAir API
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Air quality data for the nearest city
    """
    try:
        url = f"{IQAIR_API_URL}/nearest_city?lat={lat}&lon={lon}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            return data['data']
        else:
            logger.warning(f"Failed to fetch nearest city data from IQAir: {data.get('message')}")
            return None
    except Exception as e:
        logger.error(f"Error fetching nearest city data from IQAir: {e}")
        return None
        
def get_iqair_nearest_station(lat, lon):
    """
    Get air quality data for the nearest station using IQAir API
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Air quality data for the nearest station
    """
    try:
        url = f"{IQAIR_API_URL}/nearest_station?lat={lat}&lon={lon}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            return data['data']
        else:
            logger.warning(f"Failed to fetch nearest station data from IQAir: {data.get('message')}")
            return None
    except Exception as e:
        logger.error(f"Error fetching nearest station data from IQAir: {e}")
        return None