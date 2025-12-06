#!/usr/bin/env python3
"""
Fix Location Scores Script V2

This script manually updates location scores for properties that have location_score = 0
by using postcode-based distance estimation and manual corrections with better postcode extraction.
"""

import pandas as pd
import re

def extract_postcode_robust(address):
    """Extract postcode from address string with multiple patterns."""
    # Pattern 1: Standard UK postcode format
    postcode_pattern1 = r'[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}'
    match1 = re.search(postcode_pattern1, address)
    if match1:
        return match1.group(0)
    
    # Pattern 2: Look for postcode areas at the end
    postcode_pattern2 = r'\b([A-Z]{1,2}[0-9][A-Z0-9]?)\s*$'
    match2 = re.search(postcode_pattern2, address)
    if match2:
        return match2.group(1)
    
    # Pattern 3: Look for postcode areas anywhere in the string
    postcode_pattern3 = r'\b([A-Z]{1,2}[0-9][A-Z0-9]?)\b'
    match3 = re.search(postcode_pattern3, address)
    if match3:
        return match3.group(1)
    
    return None

def get_postcode_distance(postcode):
    """Get distance from postcode to London center."""
    if not postcode:
        return None
    
    # Known distances for London postcode areas
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
        
        # Additional areas
        'EN1': 12.0, 'EN2': 13.0, 'EN3': 14.0, 'EN4': 15.0, 'EN5': 16.0, 'EN6': 17.0,
        'EN7': 18.0, 'EN8': 19.0, 'EN9': 20.0, 'EN10': 21.0, 'EN11': 22.0,
        'SM1': 15.0, 'SM2': 16.0, 'SM3': 17.0, 'SM4': 18.0, 'SM5': 19.0, 'SM6': 20.0,
        'SM7': 21.0, 'SM8': 22.0, 'SM9': 23.0,
        'CR0': 15.0, 'CR1': 16.0, 'CR2': 17.0, 'CR3': 18.0, 'CR4': 19.0, 'CR5': 20.0,
        'CR6': 21.0, 'CR7': 22.0, 'CR8': 23.0, 'CR9': 24.0,
        'BR1': 12.0, 'BR2': 13.0, 'BR3': 14.0, 'BR4': 15.0, 'BR5': 16.0, 'BR6': 17.0,
        'BR7': 18.0, 'BR8': 19.0,
        'DA1': 20.0, 'DA2': 21.0, 'DA3': 22.0, 'DA4': 23.0, 'DA5': 24.0, 'DA6': 25.0,
        'DA7': 26.0, 'DA8': 27.0, 'DA9': 28.0, 'DA10': 29.0, 'DA11': 30.0, 'DA12': 31.0,
        'DA13': 32.0, 'DA14': 33.0, 'DA15': 34.0, 'DA16': 35.0, 'DA17': 36.0,
        'KT1': 15.0, 'KT2': 16.0, 'KT3': 17.0, 'KT4': 18.0, 'KT5': 19.0, 'KT6': 20.0,
        'KT7': 21.0, 'KT8': 22.0, 'KT9': 23.0, 'KT10': 24.0, 'KT11': 25.0, 'KT12': 26.0,
        'KT13': 27.0, 'KT14': 28.0, 'KT15': 29.0, 'KT16': 30.0, 'KT17': 31.0, 'KT18': 32.0,
        'KT19': 33.0, 'KT20': 34.0, 'KT21': 35.0, 'KT22': 36.0, 'KT23': 37.0, 'KT24': 38.0,
        'UB1': 15.0, 'UB2': 16.0, 'UB3': 17.0, 'UB4': 18.0, 'UB5': 19.0, 'UB6': 20.0,
        'UB7': 21.0, 'UB8': 22.0, 'UB9': 23.0, 'UB10': 24.0, 'UB11': 25.0,
        'HA0': 12.0, 'HA1': 13.0, 'HA2': 14.0, 'HA3': 15.0, 'HA4': 16.0, 'HA5': 17.0,
        'HA6': 18.0, 'HA7': 19.0, 'HA8': 20.0, 'HA9': 21.0,
        'TW1': 12.0, 'TW2': 13.0, 'TW3': 14.0, 'TW4': 15.0, 'TW5': 16.0, 'TW6': 17.0,
        'TW7': 18.0, 'TW8': 19.0, 'TW9': 20.0, 'TW10': 21.0, 'TW11': 22.0, 'TW12': 23.0,
        'TW13': 24.0, 'TW14': 25.0, 'TW15': 26.0, 'TW16': 27.0, 'TW17': 28.0, 'TW18': 29.0,
        'TW19': 30.0, 'TW20': 31.0,
        'IG1': 15.0, 'IG2': 16.0, 'IG3': 17.0, 'IG4': 18.0, 'IG5': 19.0, 'IG6': 20.0,
        'IG7': 21.0, 'IG8': 22.0, 'IG9': 23.0, 'IG10': 24.0, 'IG11': 25.0,
        'RM1': 20.0, 'RM2': 21.0, 'RM3': 22.0, 'RM4': 23.0, 'RM5': 24.0, 'RM6': 25.0,
        'RM7': 26.0, 'RM8': 27.0, 'RM9': 28.0, 'RM10': 29.0, 'RM11': 30.0, 'RM12': 31.0,
        'RM13': 32.0, 'RM14': 33.0, 'RM15': 34.0, 'RM16': 35.0, 'RM17': 36.0, 'RM18': 37.0,
        'RM19': 38.0, 'RM20': 39.0,
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

def get_manual_distance_estimate(address):
    """Get manual distance estimates for specific addresses."""
    address_lower = address.lower()
    
    # Manual mappings for specific addresses
    manual_distances = {
        'trinity street, en2': 13.0,
        'hanno cl sm6': 20.0,
        'ravensbourne road, se6': 8.0,
        'norbury': 8.0,
        'gloucester road, cr0': 15.0,
        'thamesmeade': 12.0,
        'gloucester road, sw5': 5.0,
        'primrose place': 8.0,
        'chapter road, london': 6.0,
        'london road, sw17': 9.0,
        'croydon': 15.0,
        'landfield court': 8.0,
        'station road, se25': 8.0,
        'n21': 9.0,
        'abbeywood, se2': 8.0,
        'brentford': 12.0,
        'argyle road': 6.0,
        'wood green': 7.0,
    }
    
    for key, distance in manual_distances.items():
        if key in address_lower:
            return distance
    
    return None

def calculate_location_score(distance_km):
    """Calculate location score (higher is better for closer to center)."""
    if pd.isna(distance_km) or distance_km is None:
        return 0
    
    # Normalize location score (0-100 scale)
    # Assuming typical London distances range from 0-50km from center
    max_distance = 50
    normalized_distance = max(0, min(1, (max_distance - distance_km) / max_distance))
    location_score = normalized_distance * 100
    return location_score

def main():
    # Load the CSV file
    df = pd.read_csv('results/enhanced_scrape_2025-Oct-15_at_18h49m/enhanced_properties_with_scores_all.csv')
    
    print("=== FIXING LOCATION SCORES V2 ===")
    
    # Find properties with location score 0
    zero_location = df[df['location_score'] == 0]
    print(f"Found {len(zero_location)} properties with location score 0")
    
    # Create a copy for modifications
    df_fixed = df.copy()
    
    # Process each property with location score 0
    for idx, row in zero_location.iterrows():
        address = row['address']
        postcode = extract_postcode_robust(address)
        
        print(f"\\nProcessing: {address}")
        print(f"  Extracted postcode: {postcode}")
        
        estimated_distance = None
        
        # Try postcode-based estimation first
        if postcode:
            estimated_distance = get_postcode_distance(postcode)
            if estimated_distance is not None:
                print(f"  -> Postcode distance: {estimated_distance:.1f} km")
        
        # Try manual estimation if postcode failed
        if estimated_distance is None:
            estimated_distance = get_manual_distance_estimate(address)
            if estimated_distance is not None:
                print(f"  -> Manual distance: {estimated_distance:.1f} km")
        
        # Update if we found a distance
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
            
            print(f"  -> Fixed: Distance = {estimated_distance:.1f} km, Location Score = {new_location_score:.1f}, Overall Score = {new_overall_score:.1f}")
        else:
            print(f"  -> No distance estimate found")
    
    # Save the fixed CSV
    output_file = 'results/enhanced_scrape_2025-Oct-15_at_18h49m/enhanced_properties_with_scores_fixed_v2.csv'
    df_fixed.to_csv(output_file, index=False)
    
    print(f"\\n=== SUMMARY ===")
    print(f"Fixed CSV saved to: {output_file}")
    
    # Show statistics
    fixed_zero = df_fixed[df_fixed['location_score'] == 0]
    print(f"Properties still with location score 0: {len(fixed_zero)}")
    print(f"Properties with location score > 0: {len(df_fixed) - len(fixed_zero)}")
    
    # Show top 10 properties after fix
    df_sorted = df_fixed.sort_values('overall_score', ascending=False)
    print(f"\\n=== TOP 10 PROPERTIES AFTER FIX ===")
    top_10 = df_sorted.head(10)[['address', 'price', 'distance_to_center_km', 'location_score', 'overall_score']]
    for idx, row in top_10.iterrows():
        distance_str = f"{row['distance_to_center_km']:.1f}" if pd.notna(row['distance_to_center_km']) else "N/A"
        print(f"{idx+1}. Score: {row['overall_score']:.1f} | Price: £{row['price']:.0f} | Distance: {distance_str} km | Location: {row['location_score']:.1f} | {row['address'][:50]}...")

if __name__ == "__main__":
    main()
















