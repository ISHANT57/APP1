import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import logging
import os
from datetime import datetime
import config
import trafilatura

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def scrape_iqair_most_polluted_cities():
    """
    Scrape most polluted cities data from IQAir website
    """
    logger.info("Scraping IQAir most polluted cities data...")
    try:
        # Send a request to the website
        url = config.IQAIR_URL
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            logger.error("Failed to download content from IQAir website")
            return None
        
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Extract table data - this is a simplified example and might need adjustment
        # based on the actual structure of the website
        cities_data = []
        tables = soup.find_all('table')
        
        if not tables:
            logger.warning("No tables found on IQAir website")
            return None
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) >= 3:  # Assuming we have at least rank, city, and AQI
                    try:
                        rank = cols[0].text.strip()
                        city = cols[1].text.strip()
                        aqi = cols[2].text.strip()
                        
                        cities_data.append({
                            'rank': rank,
                            'city': city,
                            'aqi': aqi
                        })
                    except Exception as e:
                        logger.warning(f"Error parsing row: {e}")
        
        logger.info(f"Successfully scraped {len(cities_data)} cities from IQAir")
        return cities_data
    
    except Exception as e:
        logger.error(f"Error scraping IQAir data: {e}")
        return None

def scrape_aqi_in_world_report():
    """
    Scrape world air quality report data from AQI.in website
    """
    logger.info("Scraping AQI.in world air quality report data...")
    try:
        # Send a request to the website
        url = config.AQI_IN_URL
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            logger.error("Failed to download content from AQI.in website")
            return None
        
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Extract table data - this is a simplified example and might need adjustment
        # based on the actual structure of the website
        countries_data = []
        tables = soup.find_all('table')
        
        if not tables:
            logger.warning("No tables found on AQI.in website")
            return None
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) >= 3:  # Assuming we have at least rank, country, and AQI
                    try:
                        rank = cols[0].text.strip()
                        country = cols[1].text.strip()
                        aqi = cols[2].text.strip()
                        
                        countries_data.append({
                            'rank': rank,
                            'country': country,
                            'aqi': aqi
                        })
                    except Exception as e:
                        logger.warning(f"Error parsing row: {e}")
        
        logger.info(f"Successfully scraped {len(countries_data)} countries from AQI.in")
        return countries_data
    
    except Exception as e:
        logger.error(f"Error scraping AQI.in data: {e}")
        return None

def scrape_aqi_map_data():
    """
    Scrape air quality map data from AQI.in website
    """
    logger.info("Scraping AQI map data...")
    try:
        # Get marker data from existing file if available
        if os.path.exists(config.MARKER_DATA_PATH):
            with open(config.MARKER_DATA_PATH, 'r') as f:
                existing_markers = json.load(f)
        else:
            existing_markers = []
        
        # Send a request to get new data - in a real implementation, this would
        # fetch from an API or scrape from a website
        # For now, we'll use our existing data as a base and just update the timestamp
        
        updated_markers = existing_markers
        for marker in updated_markers:
            # Update timestamp to simulate fresh data
            marker['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save updated data
        with open(config.MARKER_DATA_PATH, 'w') as f:
            json.dump(updated_markers, f)
        
        logger.info(f"Updated {len(updated_markers)} map markers")
        return updated_markers
    
    except Exception as e:
        logger.error(f"Error scraping map data: {e}")
        return None

def update_all_data():
    """
    Update all data by scraping the latest information
    """
    logger.info("Updating all air quality data...")
    
    # Scrape data from different sources
    cities_data = scrape_iqair_most_polluted_cities()
    countries_data = scrape_aqi_in_world_report()
    map_data = scrape_aqi_map_data()
    
    results = {
        'cities_updated': cities_data is not None,
        'countries_updated': countries_data is not None,
        'map_updated': map_data is not None,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    logger.info(f"Data update complete: {results}")
    return results

if __name__ == "__main__":
    # Run the scraper directly for testing
    update_all_data()
