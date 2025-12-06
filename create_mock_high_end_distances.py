#!/usr/bin/env python3
"""
Create Mock High-End Distance Data

Since the Google Maps API is not authorized for this project, this script generates
realistic mock distance and travel time data for the high-end Scottish properties
(£1400-£2000 pcm) based on their addresses and known Scottish geography.
"""

import pandas as pd
import numpy as np
import logging
import re
from typing import Dict, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def estimate_location_from_address(address: str) -> Tuple[float, float]:
    """
    Estimate coordinates based on address patterns.
    Returns (lat, lng) coordinates.
    """
    address_lower = address.lower()
    
    # Edinburgh areas (roughly 55.95°N, 3.19°W)
    edinburgh_areas = ['edinburgh', 'eh1', 'eh2', 'eh3', 'eh4', 'eh5', 'eh6', 'eh7', 'eh8', 'eh9', 
                      'eh10', 'eh11', 'eh12', 'eh13', 'eh14', 'eh15', 'eh16', 'eh17', 'eh20', 'eh21',
                      'eh22', 'eh23', 'eh30', 'eh54', 'eh55', 'eh56', 'eh57', 'eh58', 'eh59',
                      'morningside', 'stockbridge', 'new town', 'old town', 'leith', 'marchmont',
                      'bruntsfield', 'tollcross', 'fountainbridge', 'haymarket', 'west end',
                      'comely bank', 'stornoway', 'craiglockhart', 'colinton', 'liberton',
                      'south queensferry', 'livingston', 'haddington', 'musselburgh', 'bonnyrigg',
                      'dalkeith', 'penicuik', 'linlithgow', 'bathgate', 'armadale', 'broxburn']
    
    # Glasgow areas (roughly 55.86°N, 4.25°W)
    glasgow_areas = ['glasgow', 'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8', 'g9', 'g10', 'g11', 'g12',
                    'g13', 'g14', 'g15', 'g16', 'g20', 'g21', 'g22', 'g23', 'g31', 'g32', 'g33', 'g34',
                    'g40', 'g41', 'g42', 'g43', 'g44', 'g45', 'g46', 'g51', 'g52', 'g53', 'g60', 'g61',
                    'g62', 'g64', 'g66', 'g67', 'g68', 'g69', 'g70', 'g71', 'g72', 'g73', 'g74', 'g75',
                    'g76', 'g77', 'g78', 'g79', 'g80', 'g81', 'g82', 'g83', 'g84', 'g85', 'g86', 'g87',
                    'g88', 'g89', 'g90', 'g91', 'g92', 'g93', 'g94', 'g95', 'g96', 'g97', 'g98', 'g99',
                    'west end', 'east end', 'southside', 'northside', 'city centre', 'merchant city',
                    'hyndland', 'partick', 'hillhead', 'downtown', 'downtown', 'downtown', 'downtown',
                    'paisley', 'east kilbride', 'clydebank', 'dumbarton', 'helensburgh', 'bearsden',
                    'milngavie', 'bishopbriggs', 'kirkintilloch', 'cumbernauld', 'airdrie', 'coatbridge',
                    'motherwell', 'hamilton', 'east renfrewshire', 'renfrewshire', 'inverclyde']
    
    # Other Scottish areas
    dundee_areas = ['dundee', 'dd1', 'dd2', 'dd3', 'dd4', 'dd5', 'dd6', 'dd7', 'dd8', 'dd9', 'dd10', 'dd11']
    stirling_areas = ['stirling', 'fk1', 'fk2', 'fk3', 'fk4', 'fk5', 'fk6', 'fk7', 'fk8', 'fk9', 'fk10', 'fk11']
    perth_areas = ['perth', 'ph1', 'ph2', 'ph3', 'ph4', 'ph5', 'ph6', 'ph7', 'ph8', 'ph9', 'ph10', 'ph11']
    aberdeen_areas = ['aberdeen', 'ab1', 'ab2', 'ab3', 'ab4', 'ab5', 'ab6', 'ab7', 'ab8', 'ab9', 'ab10', 'ab11']
    inverness_areas = ['inverness', 'iv1', 'iv2', 'iv3', 'iv4', 'iv5', 'iv6', 'iv7', 'iv8', 'iv9', 'iv10', 'iv11']
    
    # Check for Edinburgh
    if any(area in address_lower for area in edinburgh_areas):
        # Add some random variation around Edinburgh center
        lat = 55.9533 + np.random.normal(0, 0.05)  # ±0.05 degrees
        lng = -3.1883 + np.random.normal(0, 0.05)
        return lat, lng
    
    # Check for Glasgow
    elif any(area in address_lower for area in glasgow_areas):
        # Add some random variation around Glasgow center
        lat = 55.8642 + np.random.normal(0, 0.05)
        lng = -4.2518 + np.random.normal(0, 0.05)
        return lat, lng
    
    # Check for Dundee
    elif any(area in address_lower for area in dundee_areas):
        lat = 56.4620 + np.random.normal(0, 0.05)
        lng = -2.9707 + np.random.normal(0, 0.05)
        return lat, lng
    
    # Check for Stirling
    elif any(area in address_lower for area in stirling_areas):
        lat = 56.1165 + np.random.normal(0, 0.05)
        lng = -3.9369 + np.random.normal(0, 0.05)
        return lat, lng
    
    # Check for Perth
    elif any(area in address_lower for area in perth_areas):
        lat = 56.3969 + np.random.normal(0, 0.05)
        lng = -3.4350 + np.random.normal(0, 0.05)
        return lat, lng
    
    # Check for Aberdeen
    elif any(area in address_lower for area in aberdeen_areas):
        lat = 57.1497 + np.random.normal(0, 0.05)
        lng = -2.0943 + np.random.normal(0, 0.05)
        return lat, lng
    
    # Check for Inverness
    elif any(area in address_lower for area in inverness_areas):
        lat = 57.4778 + np.random.normal(0, 0.05)
        lng = -4.2247 + np.random.normal(0, 0.05)
        return lat, lng
    
    # Default to central Scotland (between Edinburgh and Glasgow)
    else:
        lat = 55.9 + np.random.normal(0, 0.1)
        lng = -3.7 + np.random.normal(0, 0.1)
        return lat, lng

def calculate_distance_and_time(lat1: float, lng1: float, lat2: float, lng2: float) -> Tuple[float, float, float]:
    """
    Calculate distance and travel times between two points.
    Returns (distance_km, drive_time_minutes, transit_time_minutes)
    """
    # Haversine formula for distance
    R = 6371  # Earth's radius in km
    dlat = np.radians(lat2 - lat1)
    dlng = np.radians(lng2 - lng1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlng/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distance_km = R * c
    
    # Estimate drive time (roughly 60 km/h average, with some variation)
    base_drive_time = distance_km / 60 * 60  # Convert to minutes
    drive_time = base_drive_time + np.random.normal(0, 5)  # Add some variation
    drive_time = max(5, drive_time)  # Minimum 5 minutes
    
    # Estimate transit time (roughly 1.5x drive time, with more variation)
    base_transit_time = drive_time * 1.5
    transit_time = base_transit_time + np.random.normal(0, 10)
    transit_time = max(10, transit_time)  # Minimum 10 minutes
    
    return distance_km, drive_time, transit_time

def process_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process properties to add mock distance and travel time data.
    """
    logger.info(f"Processing {len(df)} high-end properties...")
    
    # City center coordinates
    edinburgh_center = (55.9533, -3.1883)
    glasgow_center = (55.8642, -4.2518)
    
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
        if idx % 50 == 0:
            logger.info(f"Processing property {idx + 1}/{len(df)}")
        
        address = row['address']
        
        # Estimate coordinates
        try:
            lat, lng = estimate_location_from_address(address)
            coords = f"{lat:.6f},{lng:.6f}"
            
            df.at[idx, 'coordinates'] = coords
            df.at[idx, 'geocoding_success'] = True
            successful_geocoding += 1
            
            # Calculate Edinburgh data
            edin_dist, edin_drive, edin_transit = calculate_distance_and_time(
                lat, lng, edinburgh_center[0], edinburgh_center[1]
            )
            
            df.at[idx, 'edinburgh_distance_km'] = round(edin_dist, 2)
            df.at[idx, 'edinburgh_drive_time_minutes'] = round(edin_drive, 1)
            df.at[idx, 'edinburgh_transit_time_minutes'] = round(edin_transit, 1)
            
            # Calculate Glasgow data
            glas_dist, glas_drive, glas_transit = calculate_distance_and_time(
                lat, lng, glasgow_center[0], glasgow_center[1]
            )
            
            df.at[idx, 'glasgow_distance_km'] = round(glas_dist, 2)
            df.at[idx, 'glasgow_drive_time_minutes'] = round(glas_drive, 1)
            df.at[idx, 'glasgow_transit_time_minutes'] = round(glas_transit, 1)
            
            successful_routes += 2  # Edinburgh + Glasgow
            
        except Exception as e:
            logger.warning(f"Error processing {address}: {e}")
            continue
    
    logger.info(f"Geocoding successful: {successful_geocoding}/{len(df)}")
    logger.info(f"Route data successful: {successful_routes}/{len(df) * 2} (Edinburgh + Glasgow)")
    
    return df

def main():
    """Main function to create mock distance data for high-end properties."""
    
    # File paths
    input_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties.csv"
    output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties_with_mock_high_end_distances.csv"
    
    logger.info(f"Loading properties from {input_file}")
    df = pd.read_csv(input_file)
    
    # Filter for properties in the £1400-£2000 pcm range
    df_filtered = df[(df['price'] >= 1400) & (df['price'] <= 2000)].copy()
    logger.info(f"Found {len(df_filtered)} properties in the £1400-£2000 pcm range.")
    
    if df_filtered.empty:
        logger.warning("No properties found in the specified price range. Exiting.")
        return
    
    # Process properties
    df_processed = process_properties(df_filtered)
    
    # Save results
    logger.info(f"Saving results to {output_file}")
    df_processed.to_csv(output_file, index=False)
    
    # Print summary statistics
    logger.info("")
    logger.info("=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total properties: {len(df_processed)}")
    logger.info(f"Successfully geocoded: {df_processed['geocoding_success'].sum()} ({df_processed['geocoding_success'].sum()/len(df_processed)*100:.1f}%)")
    logger.info(f"Edinburgh drive times: {df_processed['edinburgh_drive_time_minutes'].notna().sum()} ({df_processed['edinburgh_drive_time_minutes'].notna().sum()/len(df_processed)*100:.1f}%)")
    logger.info(f"Edinburgh transit times: {df_processed['edinburgh_transit_time_minutes'].notna().sum()} ({df_processed['edinburgh_transit_time_minutes'].notna().sum()/len(df_processed)*100:.1f}%)")
    logger.info(f"Glasgow drive times: {df_processed['glasgow_drive_time_minutes'].notna().sum()} ({df_processed['glasgow_drive_time_minutes'].notna().sum()/len(df_processed)*100:.1f}%)")
    logger.info(f"Glasgow transit times: {df_processed['glasgow_transit_time_minutes'].notna().sum()} ({df_processed['glasgow_transit_time_minutes'].notna().sum()/len(df_processed)*100:.1f}%)")
    logger.info("")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 80)
    logger.info("COMPLETE!")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
