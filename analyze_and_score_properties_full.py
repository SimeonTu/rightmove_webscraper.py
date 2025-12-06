#!/usr/bin/env python3
"""
Property Analysis and Scoring Script - Full Dataset with Data Quality Checks

This script analyzes property data from the Rightmove scraper and creates a scoring system
based on price, location (distance from center of London), and property size.
Includes comprehensive data quality checks and error handling.
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
    """Get coordinates from address using geocoding."""
    for attempt in range(max_retries):
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return (location.latitude, location.longitude)
        except Exception as e:
            logger.warning(f"Geocoding attempt {attempt + 1} failed: {e}")
            time.sleep(1)  # Wait before retry
    return None

def calculate_distance_to_center(coords):
    """Calculate distance from property to center of London in kilometers."""
    if coords is None:
        return None
    return geodesic(coords, LONDON_CENTER).kilometers

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
    output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-15_at_18h49m/enhanced_properties_with_scores_full.csv"
    
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
    
    # Filter to only properties with size data
    df_with_size = df.dropna(subset=['property_size_sqm'])
    logger.info(f"Properties with size data: {len(df_with_size)} out of {len(df)}")
    
    if len(df_with_size) == 0:
        logger.error("No properties with size data found!")
        return
    
    # Check for data quality issues and fix obvious errors
    logger.info("Checking for data quality issues...")
    
    # Check for suspicious sizes
    suspicious_sizes = df_with_size[df_with_size['property_size_sqm'] < 10]
    if len(suspicious_sizes) > 0:
        logger.warning(f"Found {len(suspicious_sizes)} properties with suspiciously small sizes (< 10 sqm):")
        for _, row in suspicious_sizes.iterrows():
            logger.warning(f"  - {row['address'][:50]}...: {row['property_size_sqm']:.1f} sqm (likely data error)")
    
    # Check for suspicious bathroom counts
    suspicious_bathrooms = df_with_size[df_with_size['bathrooms'] > 5]
    if len(suspicious_bathrooms) > 0:
        logger.warning(f"Found {len(suspicious_bathrooms)} properties with suspicious bathroom counts (> 5):")
        for _, row in suspicious_bathrooms.iterrows():
            logger.warning(f"  - {row['address'][:50]}...: {row['bathrooms']:.0f} bathrooms (likely data error)")
    
    # Calculate average size excluding suspicious values
    valid_sizes = df_with_size[df_with_size['property_size_sqm'] >= 10]['property_size_sqm']
    if len(valid_sizes) > 0:
        avg_size = valid_sizes.mean()
        logger.info(f"Average property size (excluding outliers): {avg_size:.1f} sqm")
    else:
        avg_size = 50  # Fallback
        logger.info(f"Using fallback average size: {avg_size:.1f} sqm")
    
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
    
    for idx, row in df_with_size.iterrows():
        if idx % 10 == 0:
            logger.info(f"Processing property {idx + 1}/{len(df_with_size)}")
        
        # Get coordinates
        address = str(row['address'])
        coords = get_coordinates_from_address(address, geolocator)
        coordinates.append(coords)
        
        # Calculate distance
        distance = calculate_distance_to_center(coords)
        distances.append(distance)
        
        # Calculate scores
        price_score = calculate_price_score(row['price'])
        location_score = calculate_location_score(distance)
        size_score = calculate_size_score(row['property_size_sqm'], avg_size)
        overall_score = calculate_overall_score(price_score, location_score, size_score)
        
        price_scores.append(price_score)
        location_scores.append(location_score)
        size_scores.append(size_score)
        overall_scores.append(overall_score)
        
        # Add small delay to avoid overwhelming the geocoding service
        time.sleep(0.1)
    
    # Add new columns to dataframe
    df_with_size['coordinates'] = coordinates
    df_with_size['distance_to_center_km'] = distances
    df_with_size['price_score'] = price_scores
    df_with_size['location_score'] = location_scores
    df_with_size['size_score'] = size_scores
    df_with_size['overall_score'] = overall_scores
    
    # Sort by overall score (highest first)
    df_sorted = df_with_size.sort_values('overall_score', ascending=False).reset_index(drop=True)
    
    # Save the new CSV
    logger.info(f"Saving scored properties to {output_file}")
    df_sorted.to_csv(output_file, index=False)
    
    # Display summary statistics
    logger.info("\n=== SCORING SUMMARY ===")
    logger.info(f"Properties processed: {len(df_with_size)}")
    logger.info(f"Properties with coordinates: {sum(1 for x in coordinates if x is not None)}")
    
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
    top_10 = df_sorted.head(10)[['address', 'price', 'property_size_sqm', 'distance_to_center_km', 'overall_score']]
    for idx, row in top_10.iterrows():
        distance_str = f"{row['distance_to_center_km']:.1f}" if pd.notna(row['distance_to_center_km']) else "N/A"
        logger.info(f"{idx+1}. Score: {row['overall_score']:.1f} | Price: £{row['price']:.0f} | Size: {row['property_size_sqm']:.0f} sqm | Distance: {distance_str} km | {row['address']}")
    
    logger.info(f"\nScored properties saved to: {output_file}")

if __name__ == "__main__":
    main()
















