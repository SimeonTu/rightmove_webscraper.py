#!/usr/bin/env python3
"""
Add Scotland City Distances Script

This script adds distance and travel time data to Scottish properties for BOTH:
- Edinburgh (city center - Princes Street)
- Glasgow (city center - George Square)

For each city, it calculates:
- Distance (km)
- Drive time (minutes)
- Transit time (minutes)

Uses Google Routes API.
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

# City center coordinates
EDINBURGH_CENTER = {"latitude": 55.9533, "longitude": -3.1883}  # Princes Street
GLASGOW_CENTER = {"latitude": 55.8642, "longitude": -4.2518}    # George Square

# Routes API endpoint
ROUTES_API_ENDPOINT = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"


def get_distances_from_routes_api(origin_addresses, destination_coords, destination_name, api_key, travel_mode="DRIVE", batch_size=25):
    """
    Get distances and times using Google Routes API.

    Args:
        origin_addresses: List of origin addresses
        destination_coords: Dict with 'latitude' and 'longitude' keys
        destination_name: Name of destination (for logging)
        api_key: Google Maps API key
        travel_mode: "DRIVE" or "TRANSIT"
        batch_size: Number of addresses to process per API call

    Returns:
        List of tuples: (distance_km, duration_minutes) or (None, None) for failed addresses
    """
    if not origin_addresses:
        return []

    all_results = []
    mode_display = "driving" if travel_mode == "DRIVE" else "transit"

    # Process in batches
    for i in range(0, len(origin_addresses), batch_size):
        batch = origin_addresses[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} addresses) - {destination_name} ({mode_display})...")

        # Build the request payload
        origins = []
        for address in batch:
            if address:
                origins.append({
                    "waypoint": {
                        "address": address
                    }
                })

        if not origins:
            all_results.extend([(None, None)] * len(batch))
            continue

        # Build payload - don't include routingPreference for TRANSIT
        payload = {
            "origins": origins,
            "destinations": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": destination_coords
                        }
                    }
                }
            ],
            "travelMode": travel_mode
        }

        # Only add routing preference for DRIVE mode
        if travel_mode == "DRIVE":
            payload["routingPreference"] = "TRAFFIC_AWARE"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "originIndex,destinationIndex,distanceMeters,duration,status"
        }

        try:
            response = requests.post(
                ROUTES_API_ENDPOINT,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"API returned status code {response.status_code}: {response.text}")
                all_results.extend([(None, None)] * len(batch))
                time.sleep(2)
                continue

            data = response.json()
            batch_results = [(None, None)] * len(batch)

            if data:
                for idx, result in enumerate(data):
                    origin_idx = result.get('originIndex', idx)

                    if result.get('status') == 'OK' or 'distanceMeters' in result:
                        distance_meters = result.get('distanceMeters')
                        duration_str = result.get('duration', '0s')

                        if distance_meters:
                            distance_km = round(distance_meters / 1000.0, 2)
                            duration_seconds = int(duration_str.rstrip('s')) if duration_str else 0
                            duration_minutes = round(duration_seconds / 60.0, 1)
                            batch_results[origin_idx] = (distance_km, duration_minutes)

            all_results.extend(batch_results)
            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            logger.error(f"API request failed: {e}")
            all_results.extend([(None, None)] * len(batch))
            time.sleep(2)

    return all_results


def main():
    """Main function to add city distance data to Scottish properties CSV."""

    # File paths
    input_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_21h28m/enhanced_properties.csv"
    output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_21h28m/enhanced_properties_with_city_distances.csv"

    logger.info("=" * 80)
    logger.info("ADD SCOTLAND CITY DISTANCES SCRIPT")
    logger.info("=" * 80)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info("\nDestinations:")
    logger.info(f"  Edinburgh: Princes Street ({EDINBURGH_CENTER['latitude']}, {EDINBURGH_CENTER['longitude']})")
    logger.info(f"  Glasgow:   George Square ({GLASGOW_CENTER['latitude']}, {GLASGOW_CENTER['longitude']})")
    logger.info("=" * 80)

    # Check for API key
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        logger.error("\nERROR: GOOGLE_MAPS_API_KEY environment variable not set!")
        logger.error("Please set your Google Maps API key:")
        logger.error("  export GOOGLE_MAPS_API_KEY='your-api-key-here'")
        return 1

    logger.info(f"\n✓ API key found (ends with: ...{api_key[-4:]})")

    # Load the CSV
    try:
        df = pd.read_csv(input_file)
        logger.info(f"✓ Loaded {len(df)} properties")
    except Exception as e:
        logger.error(f"✗ Error loading CSV: {e}")
        return 1

    # Prepare addresses
    has_postcode = 'postcode' in df.columns
    logger.info(f"{'✓' if has_postcode else '✗'} Postcode column {'available' if has_postcode else 'not available'}")

    addresses = []
    for idx, row in df.iterrows():
        address = str(row['address']) if pd.notna(row['address']) else ""
        postcode = str(row['postcode']) if has_postcode and pd.notna(row['postcode']) else ""

        # Prefer postcode
        if postcode and postcode.strip():
            search_address = f"{postcode}, Scotland, UK"
        elif address and address.strip():
            search_address = f"{address}, Scotland, UK"
        else:
            search_address = None

        addresses.append(search_address)

    valid_count = sum(1 for a in addresses if a is not None)
    logger.info(f"✓ Prepared {valid_count}/{len(df)} valid addresses")

    # Calculate distances for Edinburgh
    logger.info("\n" + "=" * 80)
    logger.info("CALCULATING EDINBURGH DISTANCES")
    logger.info("=" * 80)

    logger.info("\n1/3: Edinburgh - Driving distances...")
    edin_drive_results = get_distances_from_routes_api(addresses, EDINBURGH_CENTER, "Edinburgh", api_key, "DRIVE")

    logger.info("\n2/3: Edinburgh - Transit distances...")
    edin_transit_results = get_distances_from_routes_api(addresses, EDINBURGH_CENTER, "Edinburgh", api_key, "TRANSIT")

    # Calculate distances for Glasgow
    logger.info("\n" + "=" * 80)
    logger.info("CALCULATING GLASGOW DISTANCES")
    logger.info("=" * 80)

    logger.info("\n1/2: Glasgow - Driving distances...")
    glas_drive_results = get_distances_from_routes_api(addresses, GLASGOW_CENTER, "Glasgow", api_key, "DRIVE")

    logger.info("\n2/2: Glasgow - Transit distances...")
    glas_transit_results = get_distances_from_routes_api(addresses, GLASGOW_CENTER, "Glasgow", api_key, "TRANSIT")

    # Add all new columns to dataframe
    logger.info("\n" + "=" * 80)
    logger.info("Adding columns to dataframe...")
    logger.info("=" * 80)

    # Edinburgh columns
    df['edinburgh_distance_km'] = [r[0] if r else None for r in edin_drive_results]
    df['edinburgh_drive_time_minutes'] = [r[1] if r else None for r in edin_drive_results]
    df['edinburgh_transit_time_minutes'] = [r[1] if r else None for r in edin_transit_results]

    # Glasgow columns
    df['glasgow_distance_km'] = [r[0] if r else None for r in glas_drive_results]
    df['glasgow_drive_time_minutes'] = [r[1] if r else None for r in glas_drive_results]
    df['glasgow_transit_time_minutes'] = [r[1] if r else None for r in glas_transit_results]

    logger.info("✓ Added 6 new columns (3 for Edinburgh, 3 for Glasgow)")

    # Save the updated CSV
    logger.info(f"\nSaving updated CSV to {output_file}")
    try:
        df.to_csv(output_file, index=False)
        logger.info("✓ CSV saved successfully!")
    except Exception as e:
        logger.error(f"✗ Error saving CSV: {e}")
        return 1

    # Display summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)

    edin_drive_success = sum(1 for d in df['edinburgh_drive_time_minutes'] if pd.notna(d))
    edin_transit_success = sum(1 for d in df['edinburgh_transit_time_minutes'] if pd.notna(d))
    glas_drive_success = sum(1 for d in df['glasgow_drive_time_minutes'] if pd.notna(d))
    glas_transit_success = sum(1 for d in df['glasgow_transit_time_minutes'] if pd.notna(d))

    logger.info(f"\nEdinburgh:")
    logger.info(f"  Drive data:   {edin_drive_success}/{len(df)} ({edin_drive_success/len(df)*100:.1f}%)")
    logger.info(f"  Transit data: {edin_transit_success}/{len(df)} ({edin_transit_success/len(df)*100:.1f}%)")

    logger.info(f"\nGlasgow:")
    logger.info(f"  Drive data:   {glas_drive_success}/{len(df)} ({glas_drive_success/len(df)*100:.1f}%)")
    logger.info(f"  Transit data: {glas_transit_success}/{len(df)} ({glas_transit_success/len(df)*100:.1f}%)")

    # Show average times
    if edin_drive_success > 0:
        avg_edin_drive = df['edinburgh_drive_time_minutes'].mean()
        avg_edin_transit = df['edinburgh_transit_time_minutes'].mean()
        logger.info(f"\nEdinburgh Average Times:")
        logger.info(f"  Drive:   {avg_edin_drive:.1f} minutes")
        logger.info(f"  Transit: {avg_edin_transit:.1f} minutes")

    if glas_drive_success > 0:
        avg_glas_drive = df['glasgow_drive_time_minutes'].mean()
        avg_glas_transit = df['glasgow_transit_time_minutes'].mean()
        logger.info(f"\nGlasgow Average Times:")
        logger.info(f"  Drive:   {avg_glas_drive:.1f} minutes")
        logger.info(f"  Transit: {avg_glas_transit:.1f} minutes")

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
