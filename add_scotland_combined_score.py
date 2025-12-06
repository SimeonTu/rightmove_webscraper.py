#!/usr/bin/env python3
"""
Add Scotland Combined Score Script

This script adds a combined score for Scottish properties based on:
- Price (lower is better)
- Property size (larger is better) - OPTIONAL
- Edinburgh distance (closer is better)
- Edinburgh drive time (shorter is better)
- Edinburgh transit time (shorter is better)
- Glasgow distance (closer is better)
- Glasgow drive time (shorter is better)
- Glasgow transit time (shorter is better)

Each factor is normalized to 0-100 scale and combined with customizable weights.
Use --no-size to run without property size requirements.

Usage:
    python3 add_scotland_combined_score.py              # With size requirement
    python3 add_scotland_combined_score.py --no-size    # Without size requirement
"""

import pandas as pd
import numpy as np
import logging
import argparse
import sys

# ============================================================================
# CUSTOMIZE YOUR WEIGHTS HERE (must add up to 1.0)
# ============================================================================

def get_weights(include_size=True, include_transit=True):
    """Get weights based on whether size and transit are included or not."""
    if include_size and include_transit:
        # With size and transit data (full mode) - REBALANCED WITH BEDROOM/BATHROOM
        return {
            'PRICE_WEIGHT': 0.08,                      # 8% - Price
            'EDINBURGH_DISTANCE_WEIGHT': 0.09,         # 9% - Edinburgh distance
            'EDINBURGH_DRIVE_TIME_WEIGHT': 0.07,       # 7% - Edinburgh drive time
            'EDINBURGH_TRANSIT_TIME_WEIGHT': 0.11,     # 11% - Edinburgh transit time
            'GLASGOW_DISTANCE_WEIGHT': 0.09,           # 9% - Glasgow distance
            'GLASGOW_DRIVE_TIME_WEIGHT': 0.07,         # 7% - Glasgow drive time
            'GLASGOW_TRANSIT_TIME_WEIGHT': 0.11,       # 11% - Glasgow transit time
            'SIZE_WEIGHT': 0.12,                       # 12% - Property size
            'BEDROOM_WEIGHT': 0.08,                    # 8% - Bedroom count
            'BATHROOM_WEIGHT': 0.05,                   # 5% - Bathroom count
            'BALANCE_WEIGHT': 0.13                     # 13% - Balance between cities
        }
    elif include_size and not include_transit:
        # With size data but no transit, no price - REBALANCED WITH BEDROOM/BATHROOM
        return {
            'PRICE_WEIGHT': 0.0,                       # 0% - Price (removed for testing)
            'EDINBURGH_DISTANCE_WEIGHT': 0.18,         # 18% - Edinburgh distance (increased from 14%)
            'EDINBURGH_DRIVE_TIME_WEIGHT': 0.18,       # 18% - Edinburgh drive time (increased from 14%)
            'EDINBURGH_TRANSIT_TIME_WEIGHT': 0.0,      # 0% - Edinburgh transit time (not used)
            'GLASGOW_DISTANCE_WEIGHT': 0.18,           # 18% - Glasgow distance (increased from 14%)
            'GLASGOW_DRIVE_TIME_WEIGHT': 0.18,         # 18% - Glasgow drive time (increased from 14%)
            'GLASGOW_TRANSIT_TIME_WEIGHT': 0.0,        # 0% - Glasgow transit time (not used)
            'SIZE_WEIGHT': 0.12,                       # 12% - Property size
            'BEDROOM_WEIGHT': 0.08,                    # 8% - Bedroom count
            'BATHROOM_WEIGHT': 0.05,                   # 5% - Bathroom count
            'BALANCE_WEIGHT': 0.03                     # 3% - Balance between cities (reduced from 11%)
        }
    elif not include_size and include_transit:
        # Without size data but with transit, no price - REBALANCED WITH BEDROOM/BATHROOM
        return {
            'PRICE_WEIGHT': 0.0,                       # 0% - Price (removed for testing)
            'EDINBURGH_DISTANCE_WEIGHT': 0.12,         # 12% - Edinburgh distance (increased from 9%)
            'EDINBURGH_DRIVE_TIME_WEIGHT': 0.12,       # 12% - Edinburgh drive time (increased from 9%)
            'EDINBURGH_TRANSIT_TIME_WEIGHT': 0.18,     # 18% - Edinburgh transit time (increased from 14%)
            'GLASGOW_DISTANCE_WEIGHT': 0.12,           # 12% - Glasgow distance (increased from 9%)
            'GLASGOW_DRIVE_TIME_WEIGHT': 0.12,         # 12% - Glasgow drive time (increased from 9%)
            'GLASGOW_TRANSIT_TIME_WEIGHT': 0.18,       # 18% - Glasgow transit time (increased from 14%)
            'SIZE_WEIGHT': 0.0,                        # 0% - Property size (not used)
            'BEDROOM_WEIGHT': 0.10,                    # 10% - Bedroom count
            'BATHROOM_WEIGHT': 0.05,                   # 5% - Bathroom count
            'BALANCE_WEIGHT': 0.01                     # 1% - Balance between cities (reduced from 11%)
        }
    else:
        # Minimal mode: no size, no transit, no price (only distance, drive time, bedrooms, bathrooms)
        # Rebalanced to favor truly between-city properties with improved bedroom scoring
        return {
            'PRICE_WEIGHT': 0.0,                       # 0% - Price (removed for testing)
            'EDINBURGH_DISTANCE_WEIGHT': 0.22,         # 22% - Edinburgh distance (increased from 20%)
            'EDINBURGH_DRIVE_TIME_WEIGHT': 0.18,       # 18% - Edinburgh drive time (increased from 15%)
            'EDINBURGH_TRANSIT_TIME_WEIGHT': 0.0,      # 0% - Edinburgh transit time (not used)
            'GLASGOW_DISTANCE_WEIGHT': 0.22,           # 22% - Glasgow distance (increased from 20%)
            'GLASGOW_DRIVE_TIME_WEIGHT': 0.18,         # 18% - Glasgow drive time (increased from 15%)
            'GLASGOW_TRANSIT_TIME_WEIGHT': 0.0,        # 0% - Glasgow transit time (not used)
            'SIZE_WEIGHT': 0.0,                        # 0% - Property size (not used)
            'BEDROOM_WEIGHT': 0.15,                    # 15% - Bedroom count
            'BATHROOM_WEIGHT': 0.05,                   # 5% - Bathroom count
            'BALANCE_WEIGHT': 0.0                      # 0% - Balance between cities (removed to redistribute)
        }

# Global weights (will be set in main)
WEIGHTS = {}
# ============================================================================

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_data(df):
    """Clean the data by removing outliers and non-Scottish properties."""
    original_count = len(df)
    logger.info(f"Starting data cleaning with {original_count} properties")
    
    # 1. Remove non-Scottish properties
    non_scottish_keywords = ['Manchester', 'England', 'Wales', 'London', 'Birmingham', 'Liverpool', 'Leeds', 'Sheffield']
    df_cleaned = df[~df['address'].str.contains('|'.join(non_scottish_keywords), case=False, na=False)]
    removed_non_scottish = original_count - len(df_cleaned)
    logger.info(f"Removed {removed_non_scottish} non-Scottish properties")
    
    # 2. Cap extreme drive times at 3 hours (180 minutes)
    df_cleaned['edinburgh_drive_time_minutes'] = df_cleaned['edinburgh_drive_time_minutes'].clip(upper=180)
    df_cleaned['glasgow_drive_time_minutes'] = df_cleaned['glasgow_drive_time_minutes'].clip(upper=180)
    
    # 3. Cap extreme distances at 200km from each city
    df_cleaned['edinburgh_distance_km'] = df_cleaned['edinburgh_distance_km'].clip(upper=200)
    df_cleaned['glasgow_distance_km'] = df_cleaned['glasgow_distance_km'].clip(upper=200)
    
    # 4. Remove properties that are too far from both cities (beyond 100km from both)
    too_far = (df_cleaned['edinburgh_distance_km'] > 100) & (df_cleaned['glasgow_distance_km'] > 100)
    df_cleaned = df_cleaned[~too_far]
    removed_too_far = len(df) - removed_non_scottish - len(df_cleaned)
    logger.info(f"Removed {removed_too_far} properties too far from both cities")
    
    # 5. Remove properties with unrealistic drive times (very short times to both cities)
    # These are likely data errors
    unrealistic_times = (df_cleaned['edinburgh_drive_time_minutes'] < 5) & (df_cleaned['glasgow_drive_time_minutes'] < 5)
    df_cleaned = df_cleaned[~unrealistic_times]
    removed_unrealistic = len(df) - removed_non_scottish - removed_too_far - len(df_cleaned)
    logger.info(f"Removed {removed_unrealistic} properties with unrealistic drive times")
    
    final_count = len(df_cleaned)
    total_removed = original_count - final_count
    logger.info(f"Data cleaning complete: {total_removed} properties removed, {final_count} properties remaining")
    
    return df_cleaned

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Add combined scores to Scottish properties CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 add_scotland_combined_score.py                    # Full data (size + transit)
  python3 add_scotland_combined_score.py --no-size          # Without size requirement
  python3 add_scotland_combined_score.py --no-transit       # Without transit requirement
  python3 add_scotland_combined_score.py --minimal          # Minimal data (price + distance + drive time only)
        """
    )
    
    parser.add_argument(
        '--no-size',
        action='store_true',
        help='Run without property size requirements (enables scoring 865+ properties)'
    )
    
    parser.add_argument(
        '--no-transit',
        action='store_true',
        help='Run without transit time requirements (enables scoring properties missing transit data)'
    )
    
    parser.add_argument(
        '--minimal',
        action='store_true',
        help='Minimal mode: only price, distance, and drive time (no size, no transit)'
    )
    
    return parser.parse_args()


def normalize_to_0_100(values, higher_is_better=True):
    """
    Normalize values to 0-100 scale.

    Args:
        values: Series of values to normalize
        higher_is_better: If True, higher values get higher scores. If False, lower values get higher scores.

    Returns:
        Series of normalized values (0-100)
    """
    min_val = values.min()
    max_val = values.max()

    if max_val == min_val:
        return pd.Series([50.0] * len(values), index=values.index)

    normalized = (values - min_val) / (max_val - min_val)

    if not higher_is_better:
        normalized = 1 - normalized

    return normalized * 100


def calculate_balance_score(edin_transit_time, glas_transit_time):
    """
    Calculate balance score that rewards properties accessible to both cities.

    Uses transit times to measure accessibility. The score is based on:
    - How close the transit times are to each other (balanced access)
    - Penalizes properties that are very far from either city

    Returns:
        Balance score (0-100)
    """
    # Calculate the worse (max) transit time - penalizes being far from either city
    max_time = max(edin_transit_time, glas_transit_time)

    # Calculate the difference between the two transit times
    time_diff = abs(edin_transit_time - glas_transit_time)

    # Ideal case: Both cities accessible in similar times (e.g., 40 min to each)
    # Worst case: One city very far (e.g., 30 min to one, 300 min to other)

    # Component 1: Penalize if worst time is too high (normalize 0-200 min range)
    max_time_penalty = max(0, 100 - (max_time / 2.0))  # 0 min = 100, 200 min = 0

    # Component 2: Penalize if times are very different (normalize 0-200 min difference)
    balance_penalty = max(0, 100 - (time_diff / 2.0))  # 0 diff = 100, 200 diff = 0

    # Combined score: 60% based on max time, 40% based on balance
    balance_score = (max_time_penalty * 0.6) + (balance_penalty * 0.4)

    return round(balance_score, 2)


def calculate_combined_score(row, price_scores, edin_dist_scores, edin_drive_scores, edin_transit_scores,
                             glas_dist_scores, glas_drive_scores, glas_transit_scores, size_scores, balance_scores,
                             bedroom_scores, bathroom_scores, include_size=True, include_transit=True, include_price=True):
    """
    Calculate combined score for a property using custom weights.

    Returns:
        Combined score (0-100) or None if data is missing
    """
    # Check if this property has all required data
    required_fields = ['edinburgh_distance_km', 'edinburgh_drive_time_minutes',
                       'glasgow_distance_km', 'glasgow_drive_time_minutes', 'bedrooms', 'bathrooms']

    if include_price:
        required_fields.append('price')

    if include_size:
        required_fields.append('property_size_sqm')

    if include_transit:
        required_fields.extend(['edinburgh_transit_time_minutes', 'glasgow_transit_time_minutes'])

    if any(pd.isna(row[field]) for field in required_fields):
        return None

    # Get individual scores
    price_score = price_scores.get(row.name, 0) if include_price else 0
    edin_dist_score = edin_dist_scores.get(row.name, 0)
    edin_drive_score = edin_drive_scores.get(row.name, 0)
    glas_dist_score = glas_dist_scores.get(row.name, 0)
    glas_drive_score = glas_drive_scores.get(row.name, 0)
    
    # Get transit scores if including transit
    if include_transit:
        edin_transit_score = edin_transit_scores.get(row.name, 0)
        glas_transit_score = glas_transit_scores.get(row.name, 0)
    else:
        edin_transit_score = 0
        glas_transit_score = 0
    
    # Get size score if including size
    size_score = size_scores.get(row.name, 0) if include_size else 0
    
    # Get bedroom and bathroom scores
    bedroom_score = bedroom_scores.get(row.name, 0)
    bathroom_score = bathroom_scores.get(row.name, 0)
    
    # Get balance score (only if we have transit data for balance calculation)
    if include_transit:
        balance_score = balance_scores.get(row.name, 0)
    else:
        # For no-transit mode, use a simple balance based on drive times
        edin_drive_time = row.get('edinburgh_drive_time_minutes', 0)
        glas_drive_time = row.get('glasgow_drive_time_minutes', 0)
        if pd.notna(edin_drive_time) and pd.notna(glas_drive_time):
            max_time = max(edin_drive_time, glas_drive_time)
            time_diff = abs(edin_drive_time - glas_drive_time)
            max_time_penalty = max(0, 100 - (max_time / 2.0))
            balance_penalty = max(0, 100 - (time_diff / 2.0))
            balance_score = (max_time_penalty * 0.6) + (balance_penalty * 0.4)
        else:
            balance_score = 0

    # Calculate penalties for unbalanced properties
    edin_drive_time = row.get('edinburgh_drive_time_minutes', 0)
    glas_drive_time = row.get('glasgow_drive_time_minutes', 0)
    edin_distance = row.get('edinburgh_distance_km', 0)
    glas_distance = row.get('glasgow_distance_km', 0)
    
    total_penalty = 0
    
    # 1. City center penalty (penalize properties very close to one city)
    if pd.notna(edin_drive_time) and pd.notna(glas_drive_time):
        # If drive time to one city is < 15 minutes, apply penalty
        if edin_drive_time < 15 or glas_drive_time < 15:
            # Calculate penalty based on how much shorter one time is than the other
            time_ratio = min(edin_drive_time, glas_drive_time) / max(edin_drive_time, glas_drive_time)
            city_center_penalty = (1 - time_ratio) * 30  # Up to 30 point penalty (increased)
            total_penalty += city_center_penalty
    
    # 2. Distance penalties (penalize properties too far from either city OR too close to one city)
    if pd.notna(edin_distance) and pd.notna(glas_distance):
        # Penalty for being too far from either city
        max_distance = max(edin_distance, glas_distance)
        if max_distance > 60:
            distance_penalty = (max_distance - 60) * 0.5  # 0.5 points per km over 60km
            total_penalty += min(distance_penalty, 25)  # Cap at 25 points
        
        # Penalty for being too close to one city (within 30km)
        min_distance = min(edin_distance, glas_distance)
        if min_distance < 30:
            close_city_penalty = (30 - min_distance) * 0.8  # 0.8 points per km under 30km
            total_penalty += min(close_city_penalty, 20)  # Cap at 20 points
    
    # 3. Extreme imbalance penalty (penalize properties with very different distances)
    if pd.notna(edin_distance) and pd.notna(glas_distance):
        distance_ratio = min(edin_distance, glas_distance) / max(edin_distance, glas_distance)
        if distance_ratio < 0.5:  # If one distance is less than 50% of the other (increased from 30%)
            imbalance_penalty = (0.5 - distance_ratio) * 50  # Up to 25 point penalty (increased)
            total_penalty += imbalance_penalty

    # Weighted combination using global weights
    combined = (price_score * WEIGHTS['PRICE_WEIGHT'] +
                edin_dist_score * WEIGHTS['EDINBURGH_DISTANCE_WEIGHT'] +
                edin_drive_score * WEIGHTS['EDINBURGH_DRIVE_TIME_WEIGHT'] +
                edin_transit_score * WEIGHTS['EDINBURGH_TRANSIT_TIME_WEIGHT'] +
                glas_dist_score * WEIGHTS['GLASGOW_DISTANCE_WEIGHT'] +
                glas_drive_score * WEIGHTS['GLASGOW_DRIVE_TIME_WEIGHT'] +
                glas_transit_score * WEIGHTS['GLASGOW_TRANSIT_TIME_WEIGHT'] +
                size_score * WEIGHTS['SIZE_WEIGHT'] +
                bedroom_score * WEIGHTS['BEDROOM_WEIGHT'] +
                bathroom_score * WEIGHTS['BATHROOM_WEIGHT'] +
                balance_score * WEIGHTS['BALANCE_WEIGHT'])

    # Apply total penalties
    combined = max(0, combined - total_penalty)

    return round(combined, 2)


def main():
    """Main function to add combined score to CSV."""
    global WEIGHTS
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Determine mode based on arguments
    if args.minimal:
        include_size = False
        include_transit = False
        mode_name = "MINIMAL (price + distance + drive time only)"
    elif args.no_size and args.no_transit:
        include_size = False
        include_transit = False
        mode_name = "NO SIZE, NO TRANSIT"
    elif args.no_size:
        include_size = False
        include_transit = True
        mode_name = "NO SIZE REQUIREMENT"
    elif args.no_transit:
        include_size = True
        include_transit = False
        mode_name = "NO TRANSIT REQUIREMENT"
    else:
        include_size = True
        include_transit = True
        mode_name = "FULL DATA (size + transit)"
    
    # Set up weights based on arguments
    WEIGHTS = get_weights(include_size, include_transit)
    
    # Validate weights add up to 1.0 (100%)
    total_weight = sum(WEIGHTS.values())
    assert abs(total_weight - 1.0) < 0.001, f"Weights must add up to 1.0 (100%), currently: {total_weight}"

    # File paths
    input_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties_full_range_merged.csv"
    
    # Generate output filename based on mode (with "rebalanced" suffix)
    if args.minimal:
        output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties_with_scotland_scores_minimal_rebalanced_real.csv"
    elif args.no_size and args.no_transit:
        output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties_with_scotland_scores_no_size_no_transit_rebalanced_real.csv"
    elif args.no_size:
        output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties_with_scotland_scores_no_size_rebalanced_real.csv"
    elif args.no_transit:
        output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties_with_scotland_scores_no_transit_rebalanced_real.csv"
    else:
        output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties_with_scotland_scores_rebalanced_real.csv"

    logger.info("=" * 80)
    logger.info(f"ADD SCOTLAND COMBINED SCORE SCRIPT ({mode_name})")
    logger.info("=" * 80)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info("\nWeighting Configuration:")
    logger.info(f"  Price:                      {WEIGHTS['PRICE_WEIGHT']*100:.1f}%")
    logger.info(f"  Edinburgh Distance:         {WEIGHTS['EDINBURGH_DISTANCE_WEIGHT']*100:.1f}%")
    logger.info(f"  Edinburgh Drive Time:       {WEIGHTS['EDINBURGH_DRIVE_TIME_WEIGHT']*100:.1f}%")
    if include_transit:
        logger.info(f"  Edinburgh Transit Time:     {WEIGHTS['EDINBURGH_TRANSIT_TIME_WEIGHT']*100:.1f}%")
    else:
        logger.info(f"  Edinburgh Transit Time:     {WEIGHTS['EDINBURGH_TRANSIT_TIME_WEIGHT']*100:.1f}% (NOT USED)")
    logger.info(f"  Glasgow Distance:           {WEIGHTS['GLASGOW_DISTANCE_WEIGHT']*100:.1f}%")
    logger.info(f"  Glasgow Drive Time:         {WEIGHTS['GLASGOW_DRIVE_TIME_WEIGHT']*100:.1f}%")
    if include_transit:
        logger.info(f"  Glasgow Transit Time:       {WEIGHTS['GLASGOW_TRANSIT_TIME_WEIGHT']*100:.1f}%")
    else:
        logger.info(f"  Glasgow Transit Time:       {WEIGHTS['GLASGOW_TRANSIT_TIME_WEIGHT']*100:.1f}% (NOT USED)")
    if include_size:
        logger.info(f"  Size:                       {WEIGHTS['SIZE_WEIGHT']*100:.1f}%")
    else:
        logger.info(f"  Size:                       {WEIGHTS['SIZE_WEIGHT']*100:.1f}% (NOT USED)")
    logger.info(f"  Bedrooms:                   {WEIGHTS['BEDROOM_WEIGHT']*100:.1f}%")
    logger.info(f"  Bathrooms:                  {WEIGHTS['BATHROOM_WEIGHT']*100:.1f}%")
    logger.info(f"  Balance:                    {WEIGHTS['BALANCE_WEIGHT']*100:.1f}% (penalizes single-city properties)")
    logger.info(f"\n  Total Edinburgh Weight:     {(WEIGHTS['EDINBURGH_DISTANCE_WEIGHT'] + WEIGHTS['EDINBURGH_DRIVE_TIME_WEIGHT'] + WEIGHTS['EDINBURGH_TRANSIT_TIME_WEIGHT'])*100:.1f}%")
    logger.info(f"  Total Glasgow Weight:       {(WEIGHTS['GLASGOW_DISTANCE_WEIGHT'] + WEIGHTS['GLASGOW_DRIVE_TIME_WEIGHT'] + WEIGHTS['GLASGOW_TRANSIT_TIME_WEIGHT'])*100:.1f}%")
    logger.info("=" * 80)

    # Load the CSV
    try:
        df = pd.read_csv(input_file)
        logger.info(f"✓ Loaded {len(df)} properties")
    except Exception as e:
        logger.error(f"✗ Error loading CSV: {e}")
        return 1

    # Clean the data to remove outliers and non-Scottish properties
    df = clean_data(df)

    # Check required columns exist
    required_columns = ['price', 'edinburgh_distance_km', 'edinburgh_drive_time_minutes',
                        'glasgow_distance_km', 'glasgow_drive_time_minutes']
    
    if include_size:
        required_columns.append('property_size_sqm')
    
    if include_transit:
        required_columns.extend(['edinburgh_transit_time_minutes', 'glasgow_transit_time_minutes'])
    
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        logger.error(f"✗ Missing required columns: {missing_columns}")
        return 1

    logger.info("✓ All required columns present")

    # Filter to properties with all required data
    filter_conditions = [
        df['price'].notna(),
        df['edinburgh_distance_km'].notna(),
        df['edinburgh_drive_time_minutes'].notna(),
        df['glasgow_distance_km'].notna(),
        df['glasgow_drive_time_minutes'].notna()
    ]
    
    if include_size:
        filter_conditions.append(df['property_size_sqm'].notna())
    
    if include_transit:
        filter_conditions.extend([
            df['edinburgh_transit_time_minutes'].notna(),
            df['glasgow_transit_time_minutes'].notna()
        ])
    
    df_complete = df[np.logical_and.reduce(filter_conditions)].copy()

    logger.info(f"\n✓ Found {len(df_complete)} properties with complete data")
    logger.info(f"  ({len(df_complete)/len(df)*100:.1f}% of total properties)")

    if len(df_complete) == 0:
        logger.error("✗ No properties with complete data found!")
        return 1

    # Display data ranges
    logger.info("\nData Ranges:")
    logger.info(f"  Price: £{df_complete['price'].min():.0f} - £{df_complete['price'].max():.0f}")
    if include_size:
        logger.info(f"  Size: {df_complete['property_size_sqm'].min():.1f} - {df_complete['property_size_sqm'].max():.1f} sqm")
    else:
        logger.info(f"  Size: NOT USED (no size requirement)")
    logger.info(f"\nEdinburgh:")
    logger.info(f"  Distance: {df_complete['edinburgh_distance_km'].min():.2f} - {df_complete['edinburgh_distance_km'].max():.2f} km")
    logger.info(f"  Drive Time: {df_complete['edinburgh_drive_time_minutes'].min():.1f} - {df_complete['edinburgh_drive_time_minutes'].max():.1f} min")
    if include_transit:
        logger.info(f"  Transit Time: {df_complete['edinburgh_transit_time_minutes'].min():.1f} - {df_complete['edinburgh_transit_time_minutes'].max():.1f} min")
    else:
        logger.info(f"  Transit Time: NOT USED (no transit requirement)")
    logger.info(f"\nGlasgow:")
    logger.info(f"  Distance: {df_complete['glasgow_distance_km'].min():.2f} - {df_complete['glasgow_distance_km'].max():.2f} km")
    logger.info(f"  Drive Time: {df_complete['glasgow_drive_time_minutes'].min():.1f} - {df_complete['glasgow_drive_time_minutes'].max():.1f} min")
    if include_transit:
        logger.info(f"  Transit Time: {df_complete['glasgow_transit_time_minutes'].min():.1f} - {df_complete['glasgow_transit_time_minutes'].max():.1f} min")
    else:
        logger.info(f"  Transit Time: NOT USED (no transit requirement)")

    # Calculate normalized scores
    logger.info("\nCalculating normalized scores...")

    # Calculate price scores (only if price is included)
    if WEIGHTS['PRICE_WEIGHT'] > 0:
        price_scores = normalize_to_0_100(df_complete['price'], higher_is_better=False)
        logger.info("✓ Price scores calculated")
    else:
        price_scores = {}  # Empty dict for no-price mode
        logger.info("✓ Price scores skipped (no price requirement)")

    edin_dist_scores = normalize_to_0_100(df_complete['edinburgh_distance_km'], higher_is_better=False)
    edin_drive_scores = normalize_to_0_100(df_complete['edinburgh_drive_time_minutes'], higher_is_better=False)
    logger.info("✓ Edinburgh distance and drive scores calculated")

    glas_dist_scores = normalize_to_0_100(df_complete['glasgow_distance_km'], higher_is_better=False)
    glas_drive_scores = normalize_to_0_100(df_complete['glasgow_drive_time_minutes'], higher_is_better=False)
    logger.info("✓ Glasgow distance and drive scores calculated")

    # Calculate transit scores only if including transit
    if include_transit:
        edin_transit_scores = normalize_to_0_100(df_complete['edinburgh_transit_time_minutes'], higher_is_better=False)
        glas_transit_scores = normalize_to_0_100(df_complete['glasgow_transit_time_minutes'], higher_is_better=False)
        logger.info("✓ Transit scores calculated")
    else:
        edin_transit_scores = {}  # Empty dict for no-transit mode
        glas_transit_scores = {}  # Empty dict for no-transit mode
        logger.info("✓ Transit scores skipped (no transit requirement)")

    # Calculate size scores only if including size
    if include_size:
        size_scores = normalize_to_0_100(df_complete['property_size_sqm'], higher_is_better=True)
        logger.info("✓ Size scores calculated")
    else:
        size_scores = {}  # Empty dict for no-size mode
        logger.info("✓ Size scores skipped (no size requirement)")

    # Calculate bedroom and bathroom scores
    # Improved bedroom scoring: distribute points evenly across 1-6 bedrooms
    def calculate_bedroom_score(bedrooms):
        if pd.isna(bedrooms):
            return 0
        # Map 1-6 bedrooms to 0-100 points more evenly
        bedroom_mapping = {1: 10, 2: 30, 3: 50, 4: 70, 5: 85, 6: 100}
        return bedroom_mapping.get(int(bedrooms), 0)
    
    bedroom_scores = df_complete['bedrooms'].apply(calculate_bedroom_score)
    
    # Improved bathroom scoring: custom logic instead of simple normalization
    def calculate_bathroom_score(bathrooms):
        if pd.isna(bathrooms):
            return 0
        # Map 0-4 bathrooms to 0-100 points
        bathroom_mapping = {0: 0, 1: 25, 2: 60, 3: 85, 4: 100}
        return bathroom_mapping.get(int(bathrooms), 0)
    
    bathroom_scores = df_complete['bathrooms'].apply(calculate_bathroom_score)
    logger.info("✓ Bedroom and bathroom scores calculated (improved balanced scoring)")

    # Calculate balance scores
    balance_scores = {}
    for idx, row in df_complete.iterrows():
        if include_transit:
            balance_score = calculate_balance_score(row['edinburgh_transit_time_minutes'], row['glasgow_transit_time_minutes'])
        else:
            # For no-transit mode, use drive times for balance calculation
            edin_drive_time = row.get('edinburgh_drive_time_minutes', 0)
            glas_drive_time = row.get('glasgow_drive_time_minutes', 0)
            if pd.notna(edin_drive_time) and pd.notna(glas_drive_time):
                max_time = max(edin_drive_time, glas_drive_time)
                time_diff = abs(edin_drive_time - glas_drive_time)
                max_time_penalty = max(0, 100 - (max_time / 2.0))
                balance_penalty = max(0, 100 - (time_diff / 2.0))
                balance_score = (max_time_penalty * 0.6) + (balance_penalty * 0.4)
            else:
                balance_score = 0
        balance_scores[idx] = balance_score
    logger.info("✓ Balance scores calculated")

    # Initialize score columns
    if WEIGHTS['PRICE_WEIGHT'] > 0:
        df['price_score'] = None
    df['edinburgh_distance_score'] = None
    df['edinburgh_drive_score'] = None
    df['glasgow_distance_score'] = None
    df['glasgow_drive_score'] = None
    df['balance_score'] = None
    df['combined_score'] = None
    
    if include_size:
        df['size_score'] = None
    
    if include_transit:
        df['edinburgh_transit_score'] = None
        df['glasgow_transit_score'] = None

    # Add individual scores
    if WEIGHTS['PRICE_WEIGHT'] > 0:
        df.loc[df_complete.index, 'price_score'] = price_scores.round(2)
    df.loc[df_complete.index, 'edinburgh_distance_score'] = edin_dist_scores.round(2)
    df.loc[df_complete.index, 'edinburgh_drive_score'] = edin_drive_scores.round(2)
    df.loc[df_complete.index, 'glasgow_distance_score'] = glas_dist_scores.round(2)
    df.loc[df_complete.index, 'glasgow_drive_score'] = glas_drive_scores.round(2)
    df.loc[df_complete.index, 'bedroom_score'] = bedroom_scores.round(2)
    df.loc[df_complete.index, 'bathroom_score'] = bathroom_scores.round(2)
    df.loc[df_complete.index, 'balance_score'] = pd.Series(balance_scores).round(2)
    
    if include_size:
        df.loc[df_complete.index, 'size_score'] = size_scores.round(2)
    
    if include_transit:
        df.loc[df_complete.index, 'edinburgh_transit_score'] = edin_transit_scores.round(2)
        df.loc[df_complete.index, 'glasgow_transit_score'] = glas_transit_scores.round(2)

    # Calculate combined scores
    logger.info("\nCalculating combined scores...")
    for idx, row in df_complete.iterrows():
        include_price = WEIGHTS['PRICE_WEIGHT'] > 0
        combined = calculate_combined_score(row, price_scores, edin_dist_scores, edin_drive_scores, edin_transit_scores,
                                            glas_dist_scores, glas_drive_scores, glas_transit_scores, size_scores, balance_scores,
                                            bedroom_scores, bathroom_scores, include_size, include_transit, include_price)
        df.at[idx, 'combined_score'] = combined

    df['combined_score'] = pd.to_numeric(df['combined_score'], errors='coerce')
    logger.info("✓ Combined scores calculated")

    # Reorder columns to ensure combined_score is second-to-last and property_url is last
    if 'property_url' in df.columns and 'combined_score' in df.columns:
        # Get all columns except combined_score and property_url
        other_cols = [col for col in df.columns if col not in ['combined_score', 'property_url']]
        # Reorder: other columns, then combined_score, then property_url
        cols = other_cols + ['combined_score', 'property_url']
        df = df[cols]
        logger.info("✓ Moved combined_score to second-to-last and property_url to end")
    elif 'property_url' in df.columns:
        # If no combined_score column, just move property_url to end
        cols = [col for col in df.columns if col != 'property_url']
        cols.append('property_url')
        df = df[cols]
        logger.info("✓ Moved property_url column to end")

    # Save the updated CSV
    logger.info(f"\nSaving updated CSV to {output_file}")
    try:
        df.to_csv(output_file, index=False)
        logger.info("✓ CSV saved successfully!")
    except Exception as e:
        logger.error(f"✗ Error saving CSV: {e}")
        return 1

    # Display summary statistics
    scored_properties = df[df['combined_score'].notna()]

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total properties: {len(df)}")
    logger.info(f"Properties with scores: {len(scored_properties)} ({len(scored_properties)/len(df)*100:.1f}%)")

    if len(scored_properties) > 0:
        logger.info(f"\nScore Statistics:")
        logger.info(f"  Highest score: {scored_properties['combined_score'].max():.2f}")
        logger.info(f"  Lowest score: {scored_properties['combined_score'].min():.2f}")
        logger.info(f"  Average score: {scored_properties['combined_score'].mean():.2f}")
        logger.info(f"  Median score: {scored_properties['combined_score'].median():.2f}")

    # Show top 10 properties
    logger.info("\n" + "=" * 80)
    logger.info("TOP 10 PROPERTIES BY COMBINED SCORE")
    logger.info("=" * 80)

    top_10 = scored_properties.nlargest(10, 'combined_score')[
        ['address', 'price', 'bedrooms', 'property_size_sqm',
         'edinburgh_distance_km', 'edinburgh_drive_time_minutes', 'edinburgh_transit_time_minutes',
         'glasgow_distance_km', 'glasgow_drive_time_minutes', 'glasgow_transit_time_minutes',
         'combined_score']
    ]

    for i, (idx, row) in enumerate(top_10.iterrows(), 1):
        price_str = f"£{row['price']:.0f}" if pd.notna(row['price']) else "N/A"
        beds_str = f"{row['bedrooms']:.0f}" if pd.notna(row['bedrooms']) else "N/A"
        size_str = f"{row['property_size_sqm']:.0f}" if pd.notna(row['property_size_sqm']) else "N/A"

        logger.info(f"\n{i}. SCORE: {row['combined_score']:.2f}")
        logger.info(f"   {row['address'][:70]}")
        logger.info(f"   {price_str} pcm | {beds_str} beds | {size_str} sqm")
        logger.info(f"   Edinburgh: {row['edinburgh_distance_km']:.1f}km | Drive: {row['edinburgh_drive_time_minutes']:.0f}min | Transit: {row['edinburgh_transit_time_minutes']:.0f}min")
        logger.info(f"   Glasgow:   {row['glasgow_distance_km']:.1f}km | Drive: {row['glasgow_drive_time_minutes']:.0f}min | Transit: {row['glasgow_transit_time_minutes']:.0f}min")

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
