#!/usr/bin/env python3
"""
Add distance and travel time data to Scotland properties (£1400-£2000) for Edinburgh and Glasgow.
Uses Google Routes API to get driving and transit times/distances.
"""

import pandas as pd
import requests
import time
import logging
from typing import Dict, Tuple, Optional
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google Routes API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")

# City coordinates
EDINBURGH_COORDS = "55.9533,-3.1883"  # Edinburgh city center
GLASGOW_COORDS = "55.8642,-4.2518"    # Glasgow city center

def get_route_data(origin: str, destination: str, travel_mode: str = "DRIVE") -> Optional[Dict]:
    """
    Get route data from Google Distance Matrix API (same as working script).
    
    Args:
        origin: Origin coordinates as "lat,lng"
        destination: Destination coordinates as "lat,lng"
        travel_mode: "DRIVE" or "TRANSIT"
    
    Returns:
        Dictionary with distance and duration data, or None if failed
    """
    url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "originIndex,destinationIndex,distanceMeters,duration,status"
    }
    
    # Prepare request body (same structure as working script)
    body = {
        "origins": [
            {
                "waypoint": {
                    "location": {
                        "latLng": {
                            "latitude": float(origin.split(',')[0]),
                            "longitude": float(origin.split(',')[1])
                        }
                    }
                }
            }
        ],
        "destinations": [
            {
                "waypoint": {
                    "location": {
                        "latLng": {
                            "latitude": float(destination.split(',')[0]),
                            "longitude": float(destination.split(',')[1])
                        }
                    }
                }
            }
        ],
        "travelMode": travel_mode
    }
    
    # Only add routing preference for DRIVE mode
    if travel_mode == "DRIVE":
        body["routingPreference"] = "TRAFFIC_AWARE"
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'routeMatrix' in data and len(data['routeMatrix']) > 0:
            route = data['routeMatrix'][0]
            if route.get('status') == 'OK':
                distance_meters = route.get('distanceMeters', 0)
                duration_str = route.get('duration', '0s')
                duration_seconds = int(duration_str.replace('s', ''))
                
                return {
                    'distance_meters': distance_meters,
                    'duration_seconds': duration_seconds,
                    'distance_km': distance_meters / 1000,
                    'duration_minutes': duration_seconds / 60
                }
            else:
                logger.warning(f"Route status not OK for {origin} to {destination} ({travel_mode}): {route.get('status')}")
                return None
        else:
            logger.warning(f"No route matrix found for {origin} to {destination} ({travel_mode})")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {origin} to {destination} ({travel_mode}): {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {origin} to {destination} ({travel_mode}): {e}")
        return None

def geocode_address(address: str) -> Optional[str]:
    """
    Geocode an address to get coordinates using Google Geocoding API.
    
    Args:
        address: Address string to geocode
    
    Returns:
        Coordinates as "lat,lng" string, or None if failed
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    params = {
        'address': address,
        'key': GOOGLE_API_KEY,
        'region': 'uk'  # Bias results to UK
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            location = data['results'][0]['geometry']['location']
            return f"{location['lat']},{location['lng']}"
        else:
            logger.warning(f"Geocoding failed for address: {address} - Status: {data['status']}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding API request failed for {address}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error geocoding {address}: {e}")
        return None

def process_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process properties to add distance and travel time data.
    
    Args:
        df: DataFrame with property data
    
    Returns:
        DataFrame with added distance and travel time columns
    """
    logger.info(f"Processing {len(df)} properties...")
    
    # Initialize new columns
    df['edinburgh_distance_km'] = None
    df['edinburgh_drive_time_minutes'] = None
    df['edinburgh_transit_time_minutes'] = None
    df['glasgow_distance_km'] = None
    df['glasgow_drive_time_minutes'] = None
    df['glasgow_transit_time_minutes'] = None
    df['coordinates'] = None
    df['geocoding_success'] = False
    
    successful_geocoding = 0
    successful_routes = 0
    
    for idx, row in df.iterrows():
        if idx % 10 == 0:
            logger.info(f"Processing property {idx + 1}/{len(df)}")
        
        address = row['address']
        logger.info(f"Processing: {address}")
        
        # Geocode address
        coords = geocode_address(address)
        if not coords:
            logger.warning(f"Failed to geocode: {address}")
            continue
        
        df.at[idx, 'coordinates'] = coords
        df.at[idx, 'geocoding_success'] = True
        successful_geocoding += 1
        
        # Get Edinburgh data
        logger.info(f"Getting Edinburgh data for: {address}")
        edinburgh_drive = get_route_data(coords, EDINBURGH_COORDS, "DRIVE")
        if edinburgh_drive:
            df.at[idx, 'edinburgh_distance_km'] = round(edinburgh_drive['distance_km'], 2)
            df.at[idx, 'edinburgh_drive_time_minutes'] = round(edinburgh_drive['duration_minutes'], 1)
            successful_routes += 1
        
        time.sleep(0.1)  # Rate limiting
        
        edinburgh_transit = get_route_data(coords, EDINBURGH_COORDS, "TRANSIT")
        if edinburgh_transit:
            df.at[idx, 'edinburgh_transit_time_minutes'] = round(edinburgh_transit['duration_minutes'], 1)
        
        time.sleep(0.1)  # Rate limiting
        
        # Get Glasgow data
        logger.info(f"Getting Glasgow data for: {address}")
        glasgow_drive = get_route_data(coords, GLASGOW_COORDS, "DRIVE")
        if glasgow_drive:
            df.at[idx, 'glasgow_distance_km'] = round(glasgow_drive['distance_km'], 2)
            df.at[idx, 'glasgow_drive_time_minutes'] = round(glasgow_drive['duration_minutes'], 1)
            successful_routes += 1
        
        time.sleep(0.1)  # Rate limiting
        
        glasgow_transit = get_route_data(coords, GLASGOW_COORDS, "TRANSIT")
        if glasgow_transit:
            df.at[idx, 'glasgow_transit_time_minutes'] = round(glasgow_transit['duration_minutes'], 1)
        
        time.sleep(0.1)  # Rate limiting
        
        logger.info(f"Completed: {address}")
    
    logger.info(f"Geocoding successful: {successful_geocoding}/{len(df)}")
    logger.info(f"Route data successful: {successful_routes}/{len(df) * 2} (Edinburgh + Glasgow)")
    
    return df

def main():
    """Main function to process the dataset."""
    logger.info("=" * 80)
    logger.info("SCOTLAND HIGH-END PROPERTIES DISTANCE DATA FETCHER")
    logger.info("=" * 80)
    
    # Load the dataset
    input_file = "results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties.csv"
    logger.info(f"Loading dataset from: {input_file}")
    
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} properties")
    
    # Process properties
    df_processed = process_properties(df)
    
    # Save results
    timestamp = datetime.now().strftime("%Y-%b-%d_at_%Hh%Mm")
    output_file = f"results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties_with_city_distances_{timestamp}.csv"
    
    logger.info(f"Saving results to: {output_file}")
    df_processed.to_csv(output_file, index=False)
    
    # Print summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)
    
    total_properties = len(df_processed)
    geocoded = df_processed['geocoding_success'].sum()
    edinburgh_drive = df_processed['edinburgh_drive_time_minutes'].notna().sum()
    edinburgh_transit = df_processed['edinburgh_transit_time_minutes'].notna().sum()
    glasgow_drive = df_processed['glasgow_drive_time_minutes'].notna().sum()
    glasgow_transit = df_processed['glasgow_transit_time_minutes'].notna().sum()
    
    logger.info(f"Total properties: {total_properties}")
    logger.info(f"Successfully geocoded: {geocoded} ({geocoded/total_properties*100:.1f}%)")
    logger.info(f"Edinburgh drive times: {edinburgh_drive} ({edinburgh_drive/total_properties*100:.1f}%)")
    logger.info(f"Edinburgh transit times: {edinburgh_transit} ({edinburgh_transit/total_properties*100:.1f}%)")
    logger.info(f"Glasgow drive times: {glasgow_drive} ({glasgow_drive/total_properties*100:.1f}%)")
    logger.info(f"Glasgow transit times: {glasgow_transit} ({glasgow_transit/total_properties*100:.1f}%)")
    
    if edinburgh_drive > 0:
        logger.info(f"Edinburgh distance range: {df_processed['edinburgh_distance_km'].min():.1f} - {df_processed['edinburgh_distance_km'].max():.1f} km")
        logger.info(f"Edinburgh drive time range: {df_processed['edinburgh_drive_time_minutes'].min():.1f} - {df_processed['edinburgh_drive_time_minutes'].max():.1f} min")
    
    if glasgow_drive > 0:
        logger.info(f"Glasgow distance range: {df_processed['glasgow_distance_km'].min():.1f} - {df_processed['glasgow_distance_km'].max():.1f} km")
        logger.info(f"Glasgow drive time range: {df_processed['glasgow_drive_time_minutes'].min():.1f} - {df_processed['glasgow_drive_time_minutes'].max():.1f} min")
    
    logger.info(f"\nOutput file: {output_file}")
    logger.info("=" * 80)
    logger.info("COMPLETE!")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
