import pandas as pd
import json
import os
import logging
from datetime import datetime
import config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_marker_data():
    """Process marker data from the AQI and Lat Long CSV file"""
    logger.info("Processing marker data...")
    try:
        # Check if we can access the attached file
        markers_file_path = 'attached_assets/AQI and Lat Long of Countries.csv'
        if os.path.exists(markers_file_path):
            df = pd.read_csv(markers_file_path)
            
            # Create marker data
            markers = []
            for _, row in df.iterrows():
                marker = {
                    'Country': row['Country'],
                    'City': row['City'],
                    'AQI': float(row['AQI Value']),
                    'AQI_Category': row['AQI Category'],
                    'PM10': str(row['PM10 AQI Value']),
                    'PM10_Category': row['PM10 AQI Category'],
                    'PM2.5': str(row['PM2.5 AQI Value']),
                    'PM2.5_Category': row['PM2.5 AQI Category'],
                    'O3': str(row['Ozone AQI Value']),
                    'O3_Category': row['Ozone AQI Category'],
                    'NO2': str(row['NO2 AQI Value']),
                    'NO2_Category': row['NO2 AQI Category'],
                    'Latitude': row['lat'],
                    'Longitude': row['lng'],
                    'Continent': get_continent_for_country(row['Country']),
                }
                
                # Assign color based on AQI category
                if row['AQI Category'] == 'Good':
                    marker['color'] = 'green'
                elif row['AQI Category'] == 'Moderate':
                    marker['color'] = 'yellow'
                elif row['AQI Category'] == 'Unhealthy for Sensitive Groups':
                    marker['color'] = 'orange'
                elif row['AQI Category'] == 'Unhealthy':
                    marker['color'] = 'red'
                elif row['AQI Category'] == 'Very Unhealthy':
                    marker['color'] = 'purple'
                else:  # Hazardous
                    marker['color'] = 'maroon'
                
                markers.append(marker)
            
            # Save to file
            with open(config.MARKER_DATA_PATH, 'w') as f:
                json.dump(markers, f)
            
            logger.info(f"Successfully saved {len(markers)} markers to {config.MARKER_DATA_PATH}")
            return markers
        else:
            # Try to extract data from marker_data.json
            markers_json_path = 'attached_assets/marker_data.json'
            if os.path.exists(markers_json_path):
                with open(markers_json_path, 'r') as f:
                    markers_json = f.read()
                    # The file appears to be truncated, so extract as much as possible
                    markers = json.loads(markers_json[:markers_json.rfind('}') + 1] + ']')
                
                # Save to file
                with open(config.MARKER_DATA_PATH, 'w') as f:
                    json.dump(markers, f)
                
                logger.info(f"Successfully saved {len(markers)} markers from JSON to {config.MARKER_DATA_PATH}")
                return markers
            else:
                logger.error("Could not find marker data source files")
                return []
                
    except Exception as e:
        logger.error(f"Error processing marker data: {e}")
        return []

def process_countries_data():
    """Process countries data from the world most polluted countries CSV file"""
    logger.info("Processing countries data...")
    try:
        file_path = 'attached_assets/world_most_polluted_countries_.csv'
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            # Remove duplicate entries (the file has multiple copies of the same data)
            df = df.drop_duplicates(subset=['Rank', 'Country'])
            
            # Convert to list of dictionaries
            countries = df.to_dict('records')
            
            # Save to file
            with open(config.COUNTRIES_DATA_PATH, 'w') as f:
                json.dump(countries, f)
            
            logger.info(f"Successfully saved {len(countries)} countries to {config.COUNTRIES_DATA_PATH}")
            return countries
        else:
            logger.error("Could not find countries data source file")
            return []
    except Exception as e:
        logger.error(f"Error processing countries data: {e}")
        return []

def process_cities_monthly_data():
    """Process cities monthly data from the updated polluted cities monthly CSV file"""
    logger.info("Processing cities monthly data...")
    try:
        file_path = 'attached_assets/updated_polluted_cities_monthly_with_states.csv'
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            # Convert to list of dictionaries
            cities = df.to_dict('records')
            
            # Save to file
            with open(config.CITIES_MONTHLY_DATA_PATH, 'w') as f:
                json.dump(cities, f)
            
            logger.info(f"Successfully saved {len(cities)} cities to {config.CITIES_MONTHLY_DATA_PATH}")
            return cities
        else:
            logger.error("Could not find cities monthly data source file")
            return []
    except Exception as e:
        logger.error(f"Error processing cities monthly data: {e}")
        return []

def get_continent_for_country(country):
    """Assign continent based on country name"""
    # This is a simplified mapping - in production, you would use a more comprehensive database
    asia = ['Bangladesh', 'Pakistan', 'India', 'China', 'Nepal', 'Bahrain', 'Kuwait', 
            'United Arab Emirates', 'Tajikistan', 'Kyrgyzstan', 'Laos', 'Uzbekistan', 
            'Mongolia', 'Burma', 'Iran', 'Iraq', 'Turkmenistan', 'Kazakhstan', 'Thailand', 
            'North Korea', 'Sri Lanka', 'Lebanon', 'Azerbaijan', 'Vietnam', 'Philippines', 
            'Indonesia', 'Saudi Arabia', 'Israel', 'Japan']
    
    africa = ['Egypt', 'Rwanda', 'Cameroon', 'Congo Kinshasa', 'Nigeria', 'Uganda', 
              'Ethiopia', 'Gabon', 'Cote Divoire', 'Senegal', 'Benin', 'Ghana', 
              'Madagascar', 'Gambia', 'South Sudan']
    
    europe = ['Bosnia and Herzegovina', 'Macedonia', 'Turkey', 'Montenegro', 'Serbia', 
              'Russian Federation', 'Poland', 'Belgium', 'Italy', 'Netherlands', 'France', 
              'United Kingdom', 'Germany', 'Finland', 'Ireland', 'Switzerland', 'Denmark', 
              'Latvia']
    
    north_america = ['United States of America', 'Mexico', 'Guatemala', 'Haiti', 'Canada', 'El Salvador']
    
    south_america = ['Peru', 'Brazil', 'Colombia']
    
    oceania = ['Australia', 'New Zealand']
    
    if country in asia:
        return 'Asia'
    elif country in africa:
        return 'Africa'
    elif country in europe:
        return 'Europe'
    elif country in north_america:
        return 'North America'
    elif country in south_america:
        return 'South America'
    elif country in oceania:
        return 'Oceania'
    else:
        return 'Other'

def process_initial_data():
    """Process all initial data from the attached files"""
    process_marker_data()
    process_countries_data()
    process_cities_monthly_data()
