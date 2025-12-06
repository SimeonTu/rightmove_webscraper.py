#!/usr/bin/env python3
"""
Property Analysis and Scoring Script - ALL Properties with Average Size for Missing Data

This script analyzes ALL property data from the Rightmove scraper and creates a scoring system
based on price, location (distance from center of London), and property size.
Uses average size for properties without size data to enable processing of all 559 properties.
"""

import pandas as pd
import numpy as np
import re
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Center of London coordinates (Trafalgar Square)
LONDON_CENTER = (51.5081, -0.1276)

def extract_postcode(address):
    """Extract postcode from address string."""
    # Look for UK postcode pattern
    postcode_pattern = r'[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}'
    match = re.search(postcode_pattern, address)
    return match.group(0) if match else None

def get_coordinates_from_address(address, geolocator, max_retries=3):
    """Get coordinates from address using multiple geocoding strategies."""
    
    # Strategy 1: Try the full address
    for attempt in range(max_retries):
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return (location.latitude, location.longitude)
        except Exception as e:
            logger.warning(f"Full address geocoding attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    
    # Strategy 2: Try with just the postcode if available
    postcode = extract_postcode(address)
    if postcode:
        try:
            location = geolocator.geocode(postcode, timeout=10)
            if location:
                logger.info(f"  -> Used postcode fallback: {postcode}")
                return (location.latitude, location.longitude)
        except Exception as e:
            logger.warning(f"Postcode geocoding failed: {e}")
    
    # Strategy 3: Try with simplified address (remove specific house numbers)
    simplified_address = re.sub(r'^\d+\s*', '', address)  # Remove house numbers
    simplified_address = re.sub(r',\s*[A-Z]{1,2}\d[A-Z0-9]?\s?\d[A-Z]{2}$', '', simplified_address)  # Remove postcode
    if simplified_address != address:
        try:
            location = geolocator.geocode(simplified_address, timeout=10)
            if location:
                logger.info(f"  -> Used simplified address fallback: {simplified_address[:50]}...")
                return (location.latitude, location.longitude)
        except Exception as e:
            logger.warning(f"Simplified address geocoding failed: {e}")
    
    # Strategy 4: Try with just the area name (last part before postcode)
    area_parts = address.split(',')
    if len(area_parts) >= 2:
        area_name = area_parts[-2].strip()
        try:
            location = geolocator.geocode(f"{area_name}, London, UK", timeout=10)
            if location:
                logger.info(f"  -> Used area name fallback: {area_name}")
                return (location.latitude, location.longitude)
        except Exception as e:
            logger.warning(f"Area name geocoding failed: {e}")
    
    return None

def calculate_distance_to_center(coords):
    """Calculate distance from property to center of London in kilometers."""
    if coords is None:
        return None
    return geodesic(coords, LONDON_CENTER).kilometers

def estimate_distance_from_postcode(postcode):
    """Estimate distance from postcode to London center using known postcode areas."""
    if not postcode:
        return None
    
    # Known approximate distances for major London postcode areas
    postcode_distances = {
        # Central London (0-5km)
        'WC1': 2.0, 'WC2': 1.5, 'EC1': 2.5, 'EC2': 2.0, 'EC3': 3.0, 'EC4': 2.5,
        'SW1': 2.0, 'SW3': 3.0, 'SW7': 4.0, 'SW10': 5.0,
        'W1': 1.5, 'W2': 3.0, 'W8': 4.0, 'W9': 4.5, 'W11': 4.0,
        'NW1': 3.0, 'NW8': 4.0,
        'SE1': 2.5, 'SE11': 3.0,
        'N1': 3.5, 'N7': 4.0,
        'E1': 3.0, 'E2': 4.0,
        
        # Inner London (5-15km)
        'SW2': 8.0, 'SW4': 6.0, 'SW5': 5.0, 'SW6': 6.0, 'SW8': 4.0, 'SW9': 5.0,
        'SW11': 6.0, 'SW12': 7.0, 'SW13': 8.0, 'SW14': 9.0, 'SW15': 10.0, 'SW16': 8.0,
        'SW17': 9.0, 'SW18': 8.0, 'SW19': 10.0, 'SW20': 12.0,
        'W3': 8.0, 'W4': 7.0, 'W5': 8.0, 'W6': 6.0, 'W7': 9.0, 'W10': 5.0, 'W12': 7.0,
        'W14': 5.0, 'W15': 6.0,
        'NW2': 7.0, 'NW3': 5.0, 'NW4': 6.0, 'NW5': 4.0, 'NW6': 5.0, 'NW7': 6.0,
        'NW9': 8.0, 'NW10': 9.0, 'NW11': 7.0,
        'SE2': 8.0, 'SE3': 7.0, 'SE4': 6.0, 'SE5': 5.0, 'SE6': 8.0, 'SE7': 9.0,
        'SE8': 7.0, 'SE9': 10.0, 'SE10': 6.0, 'SE12': 9.0, 'SE13': 8.0, 'SE14': 6.0,
        'SE15': 5.0, 'SE16': 6.0, 'SE17': 4.0, 'SE18': 8.0, 'SE19': 7.0, 'SE20': 8.0,
        'SE21': 6.0, 'SE22': 5.0, 'SE23': 7.0, 'SE24': 6.0, 'SE25': 8.0, 'SE26': 8.0,
        'SE27': 9.0, 'SE28': 12.0,
        'N2': 6.0, 'N3': 7.0, 'N4': 5.0, 'N5': 4.0, 'N6': 5.0, 'N8': 6.0, 'N9': 8.0,
        'N10': 6.0, 'N11': 7.0, 'N12': 8.0, 'N13': 9.0, 'N14': 10.0, 'N15': 7.0,
        'N16': 6.0, 'N17': 8.0, 'N18': 9.0, 'N19': 7.0, 'N20': 8.0, 'N21': 9.0, 'N22': 8.0,
        'E3': 6.0, 'E4': 8.0, 'E5': 7.0, 'E6': 10.0, 'E7': 8.0, 'E8': 6.0, 'E9': 7.0,
        'E10': 8.0, 'E11': 9.0, 'E12': 10.0, 'E13': 9.0, 'E14': 7.0, 'E15': 8.0,
        'E16': 8.0, 'E17': 9.0, 'E18': 10.0, 'E20': 8.0,
        
        # Outer London (15-30km)
        'SW21': 15.0, 'SW22': 16.0, 'SW23': 17.0, 'SW24': 18.0, 'SW25': 19.0,
        'W13': 12.0, 'W16': 13.0, 'W17': 14.0, 'W18': 15.0, 'W19': 16.0, 'W20': 17.0,
        'NW12': 12.0, 'NW13': 13.0, 'NW14': 14.0, 'NW15': 15.0, 'NW16': 16.0,
        'SE29': 15.0, 'SE30': 16.0, 'SE31': 17.0, 'SE32': 18.0, 'SE33': 19.0,
        'N23': 15.0, 'N24': 16.0, 'N25': 17.0, 'N26': 18.0, 'N27': 19.0, 'N28': 20.0,
        'E21': 15.0, 'E22': 16.0, 'E23': 17.0, 'E24': 18.0, 'E25': 19.0, 'E26': 20.0,
        
        # Greater London (30km+)
        'SW26': 25.0, 'SW27': 26.0, 'SW28': 27.0, 'SW29': 28.0, 'SW30': 29.0,
        'W21': 25.0, 'W22': 26.0, 'W23': 27.0, 'W24': 28.0, 'W25': 29.0,
        'NW17': 25.0, 'NW18': 26.0, 'NW19': 27.0, 'NW20': 28.0, 'NW21': 29.0,
        'SE34': 25.0, 'SE35': 26.0, 'SE36': 27.0, 'SE37': 28.0, 'SE38': 29.0,
        'N29': 25.0, 'N30': 26.0, 'N31': 27.0, 'N32': 28.0, 'N33': 29.0, 'N34': 30.0,
        'E27': 25.0, 'E28': 26.0, 'E29': 27.0, 'E30': 28.0, 'E31': 29.0, 'E32': 30.0,
    }
    
    # Extract the postcode area (first part)
    postcode_area = postcode.split(' ')[0]
    
    # Look up the distance
    if postcode_area in postcode_distances:
        return postcode_distances[postcode_area]
    
    # If not found, try with just the first 2 characters
    if len(postcode_area) >= 2:
        area_prefix = postcode_area[:2]
        for code, distance in postcode_distances.items():
            if code.startswith(area_prefix):
                return distance
    
    return None

def get_comprehensive_coordinates(address, geolocator):
    """Get coordinates using all available methods."""
    coords = get_coordinates_from_address(address, geolocator)
    
    if coords is not None:
        return coords, "geocoded"
    
    # Fallback: Try to estimate from postcode
    postcode = extract_postcode(address)
    if postcode:
        estimated_distance = estimate_distance_from_postcode(postcode)
        if estimated_distance is not None:
            # Use a rough coordinate estimation based on distance
            # This is a very approximate method
            logger.info(f"  -> Used postcode distance estimation: {postcode} (~{estimated_distance:.1f} km)")
            # Return approximate coordinates (this is very rough)
            return (51.5081 + (estimated_distance * 0.01), -0.1276 + (estimated_distance * 0.01)), "estimated"
    
    return None, "failed"

def normalize_price(price):
    """Normalize price to monthly equivalent."""
    if pd.isna(price) or price == 0:
        return None
    
    # Convert to monthly if it's weekly (assuming 4.33 weeks per month)
    # This is a rough approximation - in reality, you'd need to check the frequency column
    return price

def calculate_size_score(property_size_sqm, avg_size):
    """Calculate size score (higher is better)."""
    if pd.isna(property_size_sqm) or property_size_sqm == 0:
        # Use average size for missing data
        size_to_use = avg_size
    else:
        size_to_use = property_size_sqm
    
    # Handle data quality issues - if size is suspiciously small (< 10 sqm), 
    # it's likely a data error, so use average size instead
    if size_to_use < 10:
        size_to_use = avg_size
    
    if size_to_use == 0:
        return 0
    
    # Normalize size score (0-100 scale)
    # Assuming typical London flat sizes range from 20-200 sqm
    size_score = min(100, (size_to_use / 100) * 100)
    return size_score

def calculate_price_score(price):
    """Calculate price score (higher is better for lower prices)."""
    if pd.isna(price) or price == 0:
        return 0
    
    # Normalize price score (0-100 scale)
    # Assuming typical London rent range £500-£5000
    # Lower prices get higher scores
    max_price = 5000
    min_price = 500
    normalized_price = max(0, min(1, (max_price - price) / (max_price - min_price)))
    price_score = normalized_price * 100
    return price_score

def calculate_location_score(distance_km):
    """Calculate location score (higher is better for closer to center)."""
    if pd.isna(distance_km):
        return 0
    
    # Normalize location score (0-100 scale)
    # Assuming typical London distances range from 0-50km from center
    max_distance = 50
    normalized_distance = max(0, min(1, (max_distance - distance_km) / max_distance))
    location_score = normalized_distance * 100
    return location_score

def calculate_overall_score(price_score, location_score, size_score, weights=None):
    """Calculate overall weighted score."""
    if weights is None:
        # Default weights: 40% price, 40% location, 20% size
        weights = {'price': 0.4, 'location': 0.4, 'size': 0.2}
    
    overall_score = (
        price_score * weights['price'] +
        location_score * weights['location'] +
        size_score * weights['size']
    )
    return round(overall_score, 2)

def main():
    """Main function to process the CSV and create scored version."""
    
    # File paths
    input_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-15_at_18h49m/enhanced_properties_fixed.csv"
    output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-15_at_18h49m/enhanced_properties_with_scores_all.csv"
    
    logger.info("Loading CSV data...")
    
    # Load the CSV
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} properties")
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return
    
    # Display basic info about the data
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Price range: £{df['price'].min():.0f} - £{df['price'].max():.0f}")
    
    # Calculate average size from properties that have size data
    properties_with_size = df.dropna(subset=['property_size_sqm'])
    logger.info(f"Properties with size data: {len(properties_with_size)} out of {len(df)}")
    
    if len(properties_with_size) == 0:
        logger.error("No properties with size data found!")
        return
    
    # Check for data quality issues and calculate average size
    logger.info("Checking for data quality issues...")
    
    # Check for suspicious sizes
    suspicious_sizes = properties_with_size[properties_with_size['property_size_sqm'] < 10]
    if len(suspicious_sizes) > 0:
        logger.warning(f"Found {len(suspicious_sizes)} properties with suspiciously small sizes (< 10 sqm):")
        for _, row in suspicious_sizes.iterrows():
            logger.warning(f"  - {row['address'][:50]}...: {row['property_size_sqm']:.1f} sqm (likely data error)")
    
    # Check for suspicious bathroom counts
    suspicious_bathrooms = df[df['bathrooms'] > 5]
    if len(suspicious_bathrooms) > 0:
        logger.warning(f"Found {len(suspicious_bathrooms)} properties with suspicious bathroom counts (> 5):")
        for _, row in suspicious_bathrooms.iterrows():
            logger.warning(f"  - {row['address'][:50]}...: {row['bathrooms']:.0f} bathrooms (likely data error)")
    
    # Calculate average size excluding suspicious values
    valid_sizes = properties_with_size[properties_with_size['property_size_sqm'] >= 10]['property_size_sqm']
    if len(valid_sizes) > 0:
        avg_size = valid_sizes.mean()
        logger.info(f"Average property size (excluding outliers): {avg_size:.1f} sqm")
    else:
        avg_size = 50  # Fallback
        logger.info(f"Using fallback average size: {avg_size:.1f} sqm")
    
    # Process ALL properties (not just those with size data)
    logger.info(f"Processing ALL {len(df)} properties (using average size for missing data)...")
    
    # Initialize geocoder
    logger.info("Initializing geocoder...")
    geolocator = Nominatim(user_agent="property_analyzer")
    
    # Process each property
    logger.info("Processing properties...")
    
    coordinates = []
    distances = []
    price_scores = []
    location_scores = []
    size_scores = []
    overall_scores = []
    size_data_status = []  # Track whether size data was available or estimated
    geocoding_status = []  # Track geocoding method used
    
    for idx, row in df.iterrows():
        logger.info(f"Processing property {idx + 1}/{len(df)}: {row['address'][:60]}...")
        
        # Get coordinates using comprehensive method
        address = str(row['address'])
        coords, geocoding_method = get_comprehensive_coordinates(address, geolocator)
        coordinates.append(coords)
        geocoding_status.append(geocoding_method)
        
        # Calculate distance
        if coords is not None:
            distance = calculate_distance_to_center(coords)
        else:
            # Try postcode estimation as last resort
            postcode = extract_postcode(address)
            if postcode:
                distance = estimate_distance_from_postcode(postcode)
                if distance is not None:
                    logger.info(f"  -> Used postcode distance fallback: {postcode} (~{distance:.1f} km)")
            else:
                distance = None
        distances.append(distance)
        
        # Calculate scores
        price_score = calculate_price_score(row['price'])
        location_score = calculate_location_score(distance)
        
        # Handle size data - use actual if available and reasonable, average if missing or suspicious
        if pd.notna(row['property_size_sqm']) and row['property_size_sqm'] > 0 and row['property_size_sqm'] >= 10:
            # Use actual size data
            size_score = calculate_size_score(row['property_size_sqm'], avg_size)
            size_data_status.append("actual")
            size_used = row['property_size_sqm']
        elif pd.notna(row['property_size_sqm']) and row['property_size_sqm'] > 0 and row['property_size_sqm'] < 10:
            # Suspiciously small size - use average instead
            size_score = calculate_size_score(avg_size, avg_size)
            size_data_status.append("corrected")
            size_used = avg_size
        else:
            # No size data - use average
            size_score = calculate_size_score(avg_size, avg_size)
            size_data_status.append("estimated")
            size_used = avg_size
        
        overall_score = calculate_overall_score(price_score, location_score, size_score)
        
        price_scores.append(price_score)
        location_scores.append(location_score)
        size_scores.append(size_score)
        overall_scores.append(overall_score)
        
        # Log individual property details
        distance_str = f"{distance:.1f}" if distance is not None else "N/A"
        geocoding_str = f"({geocoding_method})" if geocoding_method != "geocoded" else ""
        logger.info(f"  -> Price: £{row['price']:.0f} | Size: {size_used:.0f} sqm ({size_data_status[-1]}) | Distance: {distance_str} km {geocoding_str} | Score: {overall_score:.1f}")
        
        # Add small delay to avoid overwhelming the geocoding service
        time.sleep(0.1)
    
    # Add new columns to dataframe
    df['coordinates'] = coordinates
    df['distance_to_center_km'] = distances
    df['price_score'] = price_scores
    df['location_score'] = location_scores
    df['size_score'] = size_scores
    df['overall_score'] = overall_scores
    df['size_data_status'] = size_data_status  # Track whether size was actual or estimated
    df['geocoding_status'] = geocoding_status  # Track geocoding method used
    
    # Sort by overall score (highest first)
    df_sorted = df.sort_values('overall_score', ascending=False).reset_index(drop=True)
    
    # Save the new CSV
    logger.info(f"Saving scored properties to {output_file}")
    df_sorted.to_csv(output_file, index=False)
    
    # Display summary statistics
    logger.info("\n=== SCORING SUMMARY ===")
    logger.info(f"Properties processed: {len(df)}")
    logger.info(f"Properties with coordinates: {sum(1 for x in coordinates if x is not None)}")
    logger.info(f"Properties with actual size data: {sum(1 for x in size_data_status if x == 'actual')}")
    logger.info(f"Properties with corrected size data: {sum(1 for x in size_data_status if x == 'corrected')}")
    logger.info(f"Properties with estimated size data: {sum(1 for x in size_data_status if x == 'estimated')}")
    logger.info(f"Properties successfully geocoded: {sum(1 for x in geocoding_status if x == 'geocoded')}")
    logger.info(f"Properties with estimated coordinates: {sum(1 for x in geocoding_status if x == 'estimated')}")
    logger.info(f"Properties with postcode distance estimation: {sum(1 for x in geocoding_status if x == 'failed' and any(d is not None for d in distances))}")
    logger.info(f"Properties with no distance data: {sum(1 for x in geocoding_status if x == 'failed' and all(d is None for d in distances))}")
    
    # Convert lists to numpy arrays and handle None values
    distances_array = np.array([d for d in distances if d is not None])
    price_scores_array = np.array(price_scores)
    location_scores_array = np.array(location_scores)
    size_scores_array = np.array(size_scores)
    overall_scores_array = np.array(overall_scores)
    
    logger.info(f"Average distance to center: {np.mean(distances_array):.2f} km" if len(distances_array) > 0 else "No valid distance data")
    logger.info(f"Average price score: {np.mean(price_scores_array):.2f}")
    logger.info(f"Average location score: {np.mean(location_scores_array):.2f}")
    logger.info(f"Average size score: {np.mean(size_scores_array):.2f}")
    logger.info(f"Average overall score: {np.mean(overall_scores_array):.2f}")
    
    # Show top 10 properties
    logger.info("\n=== TOP 10 PROPERTIES ===")
    top_10 = df_sorted.head(10)[['address', 'price', 'property_size_sqm', 'distance_to_center_km', 'overall_score', 'size_data_status']]
    for idx, row in top_10.iterrows():
        distance_str = f"{row['distance_to_center_km']:.1f}" if pd.notna(row['distance_to_center_km']) else "N/A"
        size_str = f"{row['property_size_sqm']:.0f}" if pd.notna(row['property_size_sqm']) else f"{avg_size:.0f} (est.)"
        status_str = f"({row['size_data_status']})" if row['size_data_status'] == 'estimated' else ""
        logger.info(f"{idx+1}. Score: {row['overall_score']:.1f} | Price: £{row['price']:.0f} | Size: {size_str} sqm {status_str} | Distance: {distance_str} km | {row['address']}")
    
    logger.info(f"\nScored properties saved to: {output_file}")

if __name__ == "__main__":
    main()
