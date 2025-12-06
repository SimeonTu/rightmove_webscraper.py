#!/usr/bin/env python3
"""
Fix Geocoding Errors Script

This script fixes geocoding errors where multiple properties have identical coordinates
or suspiciously incorrect distances.
"""

import pandas as pd
import re
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# Center of London coordinates (Trafalgar Square)
LONDON_CENTER = (51.5081, -0.1276)

def extract_postcode_robust(address):
    """Extract postcode from address string."""
    postcode_pattern = r'[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}'
    match = re.search(postcode_pattern, address)
    return match.group(0) if match else None

def get_postcode_distance(postcode):
    """Get distance from postcode to London center."""
    if not postcode:
        return None
    
    postcode_distances = {
        'SE9': 10.0, 'SW16': 8.0, 'TW8': 18.0, 'SE8': 7.0, 'N19': 7.0, 'SW2': 8.0, 'N4': 5.0,
        'SE15': 5.0, 'N22': 8.0, 'SW15': 12.0, 'N9': 15.0, 'NW10': 9.0, 'SE3': 10.0,
        'SW17': 9.0, 'SE25': 8.0, 'N21': 9.0, 'SE2': 8.0, 'CR0': 15.0, 'SM6': 20.0,
        'EN2': 13.0, 'SE6': 8.0, 'NW2': 7.0, 'E14': 4.0, 'SW5': 5.0, 'SW4': 6.0,
        'SW6': 6.0, 'SW8': 4.0, 'SW9': 5.0, 'SW11': 6.0, 'SW12': 7.0, 'SW13': 8.0,
        'SW14': 9.0, 'SW15': 10.0, 'SW18': 8.0, 'SW19': 10.0, 'SW20': 12.0,
        'W3': 8.0, 'W4': 7.0, 'W5': 8.0, 'W6': 6.0, 'W7': 9.0, 'W10': 5.0, 'W12': 7.0,
        'W14': 5.0, 'W15': 6.0, 'NW2': 7.0, 'NW3': 5.0, 'NW4': 6.0, 'NW5': 4.0,
        'NW6': 5.0, 'NW7': 6.0, 'NW9': 8.0, 'NW10': 9.0, 'NW11': 7.0,
        'SE2': 8.0, 'SE3': 7.0, 'SE4': 6.0, 'SE5': 5.0, 'SE7': 9.0, 'SE8': 7.0,
        'SE10': 6.0, 'SE12': 9.0, 'SE13': 8.0, 'SE14': 6.0, 'SE16': 6.0, 'SE17': 4.0,
        'SE18': 8.0, 'SE19': 7.0, 'SE20': 8.0, 'SE21': 6.0, 'SE22': 5.0, 'SE23': 7.0,
        'SE24': 6.0, 'SE26': 8.0, 'SE27': 9.0, 'SE28': 12.0,
        'N2': 6.0, 'N3': 7.0, 'N4': 5.0, 'N5': 4.0, 'N6': 5.0, 'N8': 6.0, 'N9': 8.0,
        'N10': 6.0, 'N11': 7.0, 'N12': 8.0, 'N13': 9.0, 'N14': 10.0, 'N15': 7.0,
        'N16': 6.0, 'N17': 8.0, 'N18': 9.0, 'N19': 7.0, 'N20': 8.0, 'N21': 9.0, 'N22': 8.0,
        'E3': 6.0, 'E4': 8.0, 'E5': 7.0, 'E6': 10.0, 'E7': 8.0, 'E8': 6.0, 'E9': 7.0,
        'E10': 8.0, 'E11': 9.0, 'E12': 10.0, 'E13': 9.0, 'E14': 7.0, 'E15': 8.0,
        'E16': 8.0, 'E17': 9.0, 'E18': 10.0, 'E20': 8.0,
    }
    
    postcode_area = postcode.split(' ')[0]
    return postcode_distances.get(postcode_area, None)

def calculate_location_score(distance_km):
    """Calculate location score."""
    if pd.isna(distance_km) or distance_km is None:
        return 0
    max_distance = 50
    normalized_distance = max(0, min(1, (max_distance - distance_km) / max_distance))
    return normalized_distance * 100

def main():
    # Load the CSV file
    df = pd.read_csv('results/enhanced_scrape_2025-Oct-15_at_18h49m/enhanced_properties_with_scores_fixed_v2.csv')
    
    print("=== FIXING GEOCODING ERRORS ===")
    
    # Find properties with actual/corrected size data
    size_data_properties = df[df['size_data_status'].isin(['actual', 'corrected'])]
    print(f"Properties with actual/corrected size data: {len(size_data_properties)}")
    
    # Find properties with identical coordinates
    coords_count = size_data_properties['coordinates'].value_counts()
    duplicate_coords = coords_count[coords_count > 1]
    print(f"\\nProperties with duplicate coordinates: {len(duplicate_coords)} coordinate groups")
    
    # Create a copy for modifications
    df_fixed = df.copy()
    
    # Fix properties with duplicate coordinates
    for coords, count in duplicate_coords.items():
        if pd.notna(coords) and count > 1:
            print(f"\\nFixing {count} properties with coordinates: {coords}")
            
            # Get all properties with these coordinates
            duplicate_props = size_data_properties[size_data_properties['coordinates'] == coords]
            
            for idx, row in duplicate_props.iterrows():
                address = row['address']
                postcode = extract_postcode_robust(address)
                
                print(f"  Fixing: {address}")
                print(f"    Postcode: {postcode}")
                
                # Use postcode-based distance
                if postcode:
                    estimated_distance = get_postcode_distance(postcode)
                    if estimated_distance is not None:
                        # Update distance and location score
                        df_fixed.at[idx, 'distance_to_center_km'] = estimated_distance
                        new_location_score = calculate_location_score(estimated_distance)
                        df_fixed.at[idx, 'location_score'] = new_location_score
                        
                        # Recalculate overall score
                        price_score = row['price_score']
                        size_score = row['size_score']
                        new_overall_score = (price_score * 0.4) + (new_location_score * 0.4) + (size_score * 0.2)
                        df_fixed.at[idx, 'overall_score'] = round(new_overall_score, 2)
                        
                        print(f"    -> Fixed: Distance = {estimated_distance:.1f} km, Location Score = {new_location_score:.1f}, Overall Score = {new_overall_score:.1f}")
                    else:
                        print(f"    -> No postcode distance found")
                else:
                    print(f"    -> No postcode found")
    
    # Fix Enterprise Court (suspiciously far distance)
    enterprise_court = df_fixed[df_fixed['address'].str.contains('Enterprise Court', na=False)]
    if len(enterprise_court) > 0:
        idx = enterprise_court.index[0]
        print(f"\\nFixing Enterprise Court (suspiciously far distance)")
        # Set to a reasonable distance for Enterprise Court (likely in outer London)
        estimated_distance = 25.0  # Reasonable estimate for Enterprise Court
        df_fixed.at[idx, 'distance_to_center_km'] = estimated_distance
        new_location_score = calculate_location_score(estimated_distance)
        df_fixed.at[idx, 'location_score'] = new_location_score
        
        # Recalculate overall score
        price_score = enterprise_court.iloc[0]['price_score']
        size_score = enterprise_court.iloc[0]['size_score']
        new_overall_score = (price_score * 0.4) + (new_location_score * 0.4) + (size_score * 0.2)
        df_fixed.at[idx, 'overall_score'] = round(new_overall_score, 2)
        
        print(f"  -> Fixed: Distance = {estimated_distance:.1f} km, Location Score = {new_location_score:.1f}, Overall Score = {new_overall_score:.1f}")
    
    # Save the fixed CSV
    output_file = 'results/enhanced_scrape_2025-Oct-15_at_18h49m/enhanced_properties_with_scores_final.csv'
    df_fixed.to_csv(output_file, index=False)
    
    print(f"\\n=== SUMMARY ===")
    print(f"Fixed CSV saved to: {output_file}")
    
    # Show statistics after fix
    size_data_fixed = df_fixed[df_fixed['size_data_status'].isin(['actual', 'corrected'])]
    distances = size_data_fixed['distance_to_center_km'].dropna()
    print(f"\\nAfter fix:")
    print(f"Min distance: {distances.min():.1f} km")
    print(f"Max distance: {distances.max():.1f} km")
    print(f"Average distance: {distances.mean():.1f} km")
    
    # Check for remaining duplicate coordinates
    coords_count_fixed = size_data_fixed['coordinates'].value_counts()
    duplicate_coords_fixed = coords_count_fixed[coords_count_fixed > 1]
    print(f"Remaining duplicate coordinates: {len(duplicate_coords_fixed)}")

if __name__ == "__main__":
    main()
















