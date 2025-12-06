#!/usr/bin/env python3
"""
Add Distance to Chinatown Script

This script adds a new column to the properties CSV file showing the distance
from each property to Chinatown, London (using Gerrard Street, Chinatown as reference).
Uses Google's Routes API (Compute Route Matrix) - the modern replacement for Distance Matrix API.
"""

import pandas as pd
import logging
import time
import os
import sys
import requests
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chinatown, London coordinates (Gerrard Street, Chinatown - the heart of London's Chinatown)
CHINATOWN_COORDS = {"latitude": 51.5115, "longitude": -0.1313}

# Routes API endpoint
ROUTES_API_ENDPOINT = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"


def get_distances_from_routes_api(origin_addresses, api_key, batch_size=25):
    """
    Get distances from multiple origins to Chinatown using Google Routes API (Compute Route Matrix).

    The Routes API allows up to 100 origins per request, but we'll batch at 25 for reliability.

    Args:
        origin_addresses: List of origin addresses
        api_key: Google Maps API key
        batch_size: Number of addresses to process per API call (max 100)

    Returns:
        List of tuples: (distance_km, duration_minutes) or (None, None) for failed addresses
    """
    if not origin_addresses:
        return []

    all_results = []

    # Process in batches
    for i in range(0, len(origin_addresses), batch_size):
        batch = origin_addresses[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} addresses)...")

        # Build the request payload
        origins = []
        for address in batch:
            origins.append({
                "waypoint": {
                    "address": address
                }
            })

        payload = {
            "origins": origins,
            "destinations": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": CHINATOWN_COORDS
                        }
                    }
                }
            ],
            "travelMode": "DRIVE",  # Can also be WALK, BICYCLE, TRANSIT
            "routingPreference": "TRAFFIC_AWARE"
        }

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "originIndex,destinationIndex,distanceMeters,duration,status"
        }

        try:
            logger.debug(f"Making Routes API request...")
            response = requests.post(
                ROUTES_API_ENDPOINT,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )

            # Check if request was successful
            if response.status_code != 200:
                logger.error(f"API returned status code {response.status_code}: {response.text}")
                # Add None for all addresses in this batch
                all_results.extend([(None, None)] * len(batch))
                time.sleep(2)
                continue

            data = response.json()

            # Process each result in the batch
            # Initialize results for this batch with None
            batch_results = [(None, None)] * len(batch)

            # Check if we have results
            if data:
                # The API returns a stream of results, each with originIndex
                for idx, result in enumerate(data):
                    origin_idx = result.get('originIndex', idx)

                    if result.get('status') == 'OK' or 'distanceMeters' in result:
                        distance_meters = result.get('distanceMeters')
                        duration_str = result.get('duration', '0s')

                        if distance_meters:
                            distance_km = round(distance_meters / 1000.0, 2)

                            # Parse duration (format: "123s")
                            duration_seconds = int(duration_str.rstrip('s')) if duration_str else 0
                            duration_minutes = round(duration_seconds / 60.0, 1)

                            batch_results[origin_idx] = (distance_km, duration_minutes)
                            logger.debug(f"  Address {origin_idx + 1}: {distance_km} km, {duration_minutes} min")
                        else:
                            logger.warning(f"  Address {origin_idx + 1}: No distance data")
                    else:
                        status = result.get('status', 'UNKNOWN')
                        logger.warning(f"  Address {origin_idx + 1}: Status {status}")

            all_results.extend(batch_results)

            # Respect API rate limits
            time.sleep(0.2)

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            # Add None for all addresses in this batch
            all_results.extend([(None, None)] * len(batch))
            time.sleep(2)
        except Exception as e:
            logger.error(f"Unexpected error processing API response: {e}")
            # Add None for all addresses in this batch
            all_results.extend([(None, None)] * len(batch))
            time.sleep(2)

    return all_results


def main():
    """Main function to add distance column to CSV."""

    # File paths
    input_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_17h42m/enhanced_properties.csv"
    output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_17h42m/enhanced_properties_with_chinatown_distance.csv"

    logger.info("=" * 80)
    logger.info("ADD DISTANCE TO CHINATOWN SCRIPT")
    logger.info("Using Google Routes API (Compute Route Matrix)")
    logger.info("=" * 80)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Reference point: Chinatown, London (Gerrard Street)")
    logger.info(f"Coordinates: {CHINATOWN_COORDS['latitude']}, {CHINATOWN_COORDS['longitude']}")
    logger.info("=" * 80)

    # Check for API key
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        logger.error("\nERROR: GOOGLE_MAPS_API_KEY environment variable not set!")
        logger.error("Please set your Google Maps API key:")
        logger.error("  export GOOGLE_MAPS_API_KEY='your-api-key-here'")
        logger.error("\nYou can get an API key from: https://console.cloud.google.com/")
        return 1

    logger.info(f"\n✓ API key found (ends with: ...{api_key[-4:]})")

    # Load the CSV
    try:
        df = pd.read_csv(input_file)
        logger.info(f"✓ Loaded {len(df)} properties")
    except Exception as e:
        logger.error(f"✗ Error loading CSV: {e}")
        return 1

    # Check if address column exists
    if 'address' not in df.columns:
        logger.error("✗ Error: 'address' column not found in CSV")
        return 1

    has_postcode = 'postcode' in df.columns
    logger.info(f"{'✓' if has_postcode else '✗'} Postcode column {'available' if has_postcode else 'not available'}")

    # Prepare addresses for API - prefer postcode if available for better accuracy
    logger.info("\nPreparing addresses for geocoding...")
    addresses = []
    for idx, row in df.iterrows():
        address = str(row['address']) if pd.notna(row['address']) else ""
        postcode = str(row['postcode']) if has_postcode and pd.notna(row['postcode']) else ""

        # Use postcode if available, otherwise full address
        if postcode and postcode.strip():
            search_address = f"{postcode}, UK"
        elif address and address.strip():
            search_address = f"{address}, UK"
        else:
            search_address = None

        addresses.append(search_address)

    valid_addresses = [a for a in addresses if a is not None]
    logger.info(f"✓ Prepared {len(valid_addresses)}/{len(df)} valid addresses")

    # Process addresses and get distances
    logger.info("\n" + "=" * 80)
    logger.info("CALCULATING DISTANCES USING GOOGLE ROUTES API")
    logger.info("=" * 80)

    results = get_distances_from_routes_api(addresses, api_key)

    # Add new columns to dataframe
    logger.info("\nAdding new columns to dataframe...")
    distances = [r[0] if r else None for r in results]
    durations = [r[1] if r else None for r in results]

    df['distance_to_chinatown_km'] = distances
    df['drive_time_to_chinatown_minutes'] = durations

    # Save the updated CSV
    logger.info(f"\nSaving updated CSV to {output_file}")
    try:
        df.to_csv(output_file, index=False)
        logger.info("✓ CSV saved successfully!")
    except Exception as e:
        logger.error(f"✗ Error saving CSV: {e}")
        return 1

    # Display summary statistics
    successful_geocodes = sum(1 for d in distances if d is not None)
    failed_geocodes = len(distances) - successful_geocodes

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total properties processed: {len(df)}")
    logger.info(f"Successful geocodes: {successful_geocodes} ({successful_geocodes/len(df)*100:.1f}%)")
    logger.info(f"Failed geocodes: {failed_geocodes} ({failed_geocodes/len(df)*100:.1f}%)")

    # Distance statistics
    distances_valid = [d for d in distances if d is not None]
    if distances_valid:
        logger.info(f"\nDistance Statistics:")
        logger.info(f"  Properties with distance data: {len(distances_valid)}")
        logger.info(f"  Closest property: {min(distances_valid):.2f} km")
        logger.info(f"  Furthest property: {max(distances_valid):.2f} km")
        logger.info(f"  Average distance: {sum(distances_valid)/len(distances_valid):.2f} km")
        logger.info(f"  Median distance: {sorted(distances_valid)[len(distances_valid)//2]:.2f} km")

        # Show properties within 5km, 10km, 15km
        within_5km = sum(1 for d in distances_valid if d <= 5)
        within_10km = sum(1 for d in distances_valid if d <= 10)
        within_15km = sum(1 for d in distances_valid if d <= 15)

        logger.info(f"\nDistance Distribution:")
        logger.info(f"  Within 5 km: {within_5km} properties ({within_5km/len(df)*100:.1f}%)")
        logger.info(f"  Within 10 km: {within_10km} properties ({within_10km/len(df)*100:.1f}%)")
        logger.info(f"  Within 15 km: {within_15km} properties ({within_15km/len(df)*100:.1f}%)")

    # Show closest properties
    logger.info("\n" + "=" * 80)
    logger.info("TOP 10 CLOSEST PROPERTIES TO CHINATOWN")
    logger.info("=" * 80)

    # Sort by distance and show top 10
    df_sorted = df.dropna(subset=['distance_to_chinatown_km']).sort_values('distance_to_chinatown_km')
    top_10 = df_sorted.head(10)[['address', 'price', 'bedrooms', 'distance_to_chinatown_km', 'drive_time_to_chinatown_minutes']]

    for i, (idx, row) in enumerate(top_10.iterrows(), 1):
        price_str = f"£{row['price']:.0f}" if pd.notna(row['price']) else "N/A"
        beds_str = f"{row['bedrooms']:.0f}" if pd.notna(row['bedrooms']) else "N/A"
        time_str = f"{row['drive_time_to_chinatown_minutes']:.0f} min" if pd.notna(row['drive_time_to_chinatown_minutes']) else "N/A"
        logger.info(f"{i}. {row['distance_to_chinatown_km']:.2f} km ({time_str}) | {price_str} pcm | {beds_str} beds | {row['address'][:60]}...")

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
