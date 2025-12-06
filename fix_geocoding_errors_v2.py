#!/usr/bin/env python3
"""
Fix Geocoding Errors Script V2

This script fixes geocoding errors with manual postcode mapping for specific addresses.
"""

import pandas as pd
import re

# Center of London coordinates (Trafalgar Square)
LONDON_CENTER = (51.5081, -0.1276)

def get_manual_distance_mapping():
    """Get manual distance mappings for specific addresses."""
    return {
        # Properties with duplicate coordinates (51.4893335, -0.1440551)
        'Grove Place, Eltham, London, SE9': 10.0,
        'Boscombe Gardens, London, SW16': 8.0,
        'New Horizons Court, London, TW8': 18.0,
        'Baildon Street, London, SE8': 7.0,
        'Windermere Road, London, N19': 7.0,
        'Pullman Court, Streatham Hill, London, SW2': 8.0,
        'Corbyn Street, London, N4': 5.0,
        
        # Properties with other duplicate coordinates
        'Archdale Road, East Dulwich, SE22': 5.0,
        'Dairyman Close, Cricklewood, NW2': 7.0,
        'Fordwych Road, Cricklewood, NW2': 7.0,
        'West Green Road, London': 6.0,
        
        # Enterprise Court (already fixed but verify)
        'Enterprise Court': 25.0,
    }

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
    
    print("=== FIXING GEOCODING ERRORS V2 ===")
    
    # Get manual distance mappings
    manual_distances = get_manual_distance_mapping()
    
    # Find properties with actual/corrected size data
    size_data_properties = df[df['size_data_status'].isin(['actual', 'corrected'])]
    print(f"Properties with actual/corrected size data: {len(size_data_properties)}")
    
    # Create a copy for modifications
    df_fixed = df.copy()
    
    # Fix properties with manual distance mappings
    fixed_count = 0
    for address_pattern, estimated_distance in manual_distances.items():
        # Find properties matching this address pattern
        matching_props = size_data_properties[size_data_properties['address'].str.contains(address_pattern, na=False)]
        
        if len(matching_props) > 0:
            print(f"\\nFixing {len(matching_props)} properties matching: {address_pattern}")
            
            for idx, row in matching_props.iterrows():
                print(f"  - {row['address']}")
                print(f"    Old distance: {row['distance_to_center_km']:.1f} km")
                
                # Update distance and location score
                df_fixed.at[idx, 'distance_to_center_km'] = estimated_distance
                new_location_score = calculate_location_score(estimated_distance)
                df_fixed.at[idx, 'location_score'] = new_location_score
                
                # Recalculate overall score
                price_score = row['price_score']
                size_score = row['size_score']
                new_overall_score = (price_score * 0.4) + (new_location_score * 0.4) + (size_score * 0.2)
                df_fixed.at[idx, 'overall_score'] = round(new_overall_score, 2)
                
                print(f"    New distance: {estimated_distance:.1f} km")
                print(f"    New location score: {new_location_score:.1f}")
                print(f"    New overall score: {new_overall_score:.1f}")
                
                fixed_count += 1
    
    # Save the fixed CSV
    output_file = 'results/enhanced_scrape_2025-Oct-15_at_18h49m/enhanced_properties_with_scores_final_v2.csv'
    df_fixed.to_csv(output_file, index=False)
    
    print(f"\\n=== SUMMARY ===")
    print(f"Fixed {fixed_count} properties")
    print(f"Fixed CSV saved to: {output_file}")
    
    # Show statistics after fix
    size_data_fixed = df_fixed[df_fixed['size_data_status'].isin(['actual', 'corrected'])]
    distances = size_data_fixed['distance_to_center_km'].dropna()
    print(f"\\nAfter fix:")
    print(f"Min distance: {distances.min():.1f} km")
    print(f"Max distance: {distances.max():.1f} km")
    print(f"Average distance: {distances.mean():.1f} km")
    print(f"Median distance: {distances.median():.1f} km")
    
    # Check for remaining duplicate coordinates
    coords_count_fixed = size_data_fixed['coordinates'].value_counts()
    duplicate_coords_fixed = coords_count_fixed[coords_count_fixed > 1]
    print(f"\\nRemaining duplicate coordinates: {len(duplicate_coords_fixed)}")
    
    if len(duplicate_coords_fixed) > 0:
        print("Remaining duplicates:")
        for coords, count in duplicate_coords_fixed.items():
            if pd.notna(coords):
                print(f"  {coords}: {count} properties")
    
    # Show top 10 properties after fix
    df_sorted = df_fixed.sort_values('overall_score', ascending=False)
    print(f"\\n=== TOP 10 PROPERTIES AFTER FIX ===")
    top_10 = df_sorted.head(10)[['address', 'price', 'distance_to_center_km', 'location_score', 'overall_score']]
    for idx, row in top_10.iterrows():
        distance_str = f"{row['distance_to_center_km']:.1f}" if pd.notna(row['distance_to_center_km']) else "N/A"
        print(f"{idx+1}. Score: {row['overall_score']:.1f} | Price: £{row['price']:.0f} | Distance: {distance_str} km | Location: {row['location_score']:.1f} | {row['address'][:50]}...")

if __name__ == "__main__":
    main()
















