#!/usr/bin/env python3
"""
Add Combined Score Script (with Drive Time)

This script adds a combined score field to the properties CSV based on:
- Price (lower is better)
- Distance to Chinatown (closer is better)
- Drive time to Chinatown (shorter is better)
- Property size (larger is better)

Each factor is normalized to 0-100 scale and combined with customizable weights.
Only properties with all four values available are scored.
"""

import pandas as pd
import numpy as np
import logging

# ============================================================================
# CUSTOMIZE YOUR WEIGHTS HERE (must add up to 1.0)
# ============================================================================
PRICE_WEIGHT = 0      # 15% - Lower emphasis on price
DISTANCE_WEIGHT = 0   # 25% - Moderate emphasis on distance
TIME_WEIGHT = 0.5       # 35% - Higher emphasis on drive time
SIZE_WEIGHT = 0.5      # 25% - Moderate emphasis on size

# Validate weights add up to 1.0 (100%)
assert abs(PRICE_WEIGHT + DISTANCE_WEIGHT + TIME_WEIGHT + SIZE_WEIGHT - 1.0) < 0.001, \
    "Weights must add up to 1.0 (100%)"
# ============================================================================

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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

    # Avoid division by zero
    if max_val == min_val:
        return pd.Series([50.0] * len(values), index=values.index)

    # Normalize to 0-1 range
    normalized = (values - min_val) / (max_val - min_val)

    # If lower is better, invert the score
    if not higher_is_better:
        normalized = 1 - normalized

    # Scale to 0-100
    return normalized * 100


def calculate_combined_score(row, price_scores, distance_scores, time_scores, size_scores):
    """
    Calculate combined score for a property using custom weights.

    Args:
        row: DataFrame row
        price_scores: Series of normalized price scores
        distance_scores: Series of normalized distance scores
        time_scores: Series of normalized drive time scores
        size_scores: Series of normalized size scores

    Returns:
        Combined score (0-100) or None if data is missing
    """
    # Check if this property has all required data
    if (pd.isna(row['price']) or pd.isna(row['distance_to_chinatown_km']) or
        pd.isna(row['drive_time_to_chinatown_minutes']) or pd.isna(row['property_size_sqm'])):
        return None

    # Get individual scores
    price_score = price_scores.get(row.name, 0)
    distance_score = distance_scores.get(row.name, 0)
    time_score = time_scores.get(row.name, 0)
    size_score = size_scores.get(row.name, 0)

    # Weighted combination using custom weights
    combined = (price_score * PRICE_WEIGHT +
                distance_score * DISTANCE_WEIGHT +
                time_score * TIME_WEIGHT +
                size_score * SIZE_WEIGHT)

    return round(combined, 2)


def main():
    """Main function to add combined score to CSV."""

    # File paths
    input_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_17h42m/enhanced_properties_with_chinatown_distance.csv"
    output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_17h42m/enhanced_properties_with_scores_4factors.csv"

    logger.info("=" * 80)
    logger.info("ADD COMBINED SCORE SCRIPT (4 FACTORS - CUSTOM WEIGHTS)")
    logger.info("=" * 80)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info("\nWeighting Configuration:")
    logger.info(f"  Price:      {PRICE_WEIGHT*100:.1f}%")
    logger.info(f"  Distance:   {DISTANCE_WEIGHT*100:.1f}%")
    logger.info(f"  Drive Time: {TIME_WEIGHT*100:.1f}%")
    logger.info(f"  Size:       {SIZE_WEIGHT*100:.1f}%")
    logger.info("=" * 80)

    # Load the CSV
    try:
        df = pd.read_csv(input_file)
        logger.info(f"✓ Loaded {len(df)} properties")
    except Exception as e:
        logger.error(f"✗ Error loading CSV: {e}")
        return 1

    # Check required columns exist
    required_columns = ['price', 'distance_to_chinatown_km', 'drive_time_to_chinatown_minutes', 'property_size_sqm']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        logger.error(f"✗ Missing required columns: {missing_columns}")
        return 1

    logger.info("✓ All required columns present")

    # Filter to properties with all required data
    df_complete = df[
        df['price'].notna() &
        df['distance_to_chinatown_km'].notna() &
        df['drive_time_to_chinatown_minutes'].notna() &
        df['property_size_sqm'].notna()
    ].copy()

    logger.info(f"\n✓ Found {len(df_complete)} properties with complete data (price, distance, time, size)")
    logger.info(f"  ({len(df_complete)/len(df)*100:.1f}% of total properties)")

    if len(df_complete) == 0:
        logger.error("✗ No properties with complete data found!")
        return 1

    # Display data ranges for context
    logger.info("\nData Ranges:")
    logger.info(f"  Price: £{df_complete['price'].min():.0f} - £{df_complete['price'].max():.0f}")
    logger.info(f"  Distance: {df_complete['distance_to_chinatown_km'].min():.2f} - {df_complete['distance_to_chinatown_km'].max():.2f} km")
    logger.info(f"  Drive Time: {df_complete['drive_time_to_chinatown_minutes'].min():.1f} - {df_complete['drive_time_to_chinatown_minutes'].max():.1f} min")
    logger.info(f"  Size: {df_complete['property_size_sqm'].min():.1f} - {df_complete['property_size_sqm'].max():.1f} sqm")

    # Calculate normalized scores for properties with complete data
    logger.info("\nCalculating normalized scores...")

    # Price score: lower price = higher score
    price_scores = normalize_to_0_100(df_complete['price'], higher_is_better=False)
    logger.info("✓ Price scores calculated (lower price = higher score)")

    # Distance score: closer to Chinatown = higher score
    distance_scores = normalize_to_0_100(df_complete['distance_to_chinatown_km'], higher_is_better=False)
    logger.info("✓ Distance scores calculated (closer = higher score)")

    # Drive time score: shorter time = higher score
    time_scores = normalize_to_0_100(df_complete['drive_time_to_chinatown_minutes'], higher_is_better=False)
    logger.info("✓ Drive time scores calculated (shorter time = higher score)")

    # Size score: larger size = higher score
    size_scores = normalize_to_0_100(df_complete['property_size_sqm'], higher_is_better=True)
    logger.info("✓ Size scores calculated (larger = higher score)")

    # Initialize score columns in main dataframe
    df['price_score'] = None
    df['distance_score'] = None
    df['time_score'] = None
    df['size_score'] = None
    df['combined_score_4factors'] = None

    # Add individual scores to main dataframe
    df.loc[df_complete.index, 'price_score'] = price_scores.round(2)
    df.loc[df_complete.index, 'distance_score'] = distance_scores.round(2)
    df.loc[df_complete.index, 'time_score'] = time_scores.round(2)
    df.loc[df_complete.index, 'size_score'] = size_scores.round(2)

    # Calculate combined scores
    logger.info(f"\nCalculating combined scores (Price: {PRICE_WEIGHT*100:.0f}%, Distance: {DISTANCE_WEIGHT*100:.0f}%, Time: {TIME_WEIGHT*100:.0f}%, Size: {SIZE_WEIGHT*100:.0f}%)...")
    for idx, row in df_complete.iterrows():
        combined = calculate_combined_score(row, price_scores, distance_scores, time_scores, size_scores)
        df.at[idx, 'combined_score_4factors'] = combined

    # Convert combined_score to numeric type
    df['combined_score_4factors'] = pd.to_numeric(df['combined_score_4factors'], errors='coerce')

    logger.info("✓ Combined scores calculated")

    # Save the updated CSV
    logger.info(f"\nSaving updated CSV to {output_file}")
    try:
        df.to_csv(output_file, index=False)
        logger.info("✓ CSV saved successfully!")
    except Exception as e:
        logger.error(f"✗ Error saving CSV: {e}")
        return 1

    # Display summary statistics
    scored_properties = df[df['combined_score_4factors'].notna()]

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total properties: {len(df)}")
    logger.info(f"Properties with scores: {len(scored_properties)} ({len(scored_properties)/len(df)*100:.1f}%)")
    logger.info(f"Properties without scores: {len(df) - len(scored_properties)} (missing price/distance/time/size data)")

    if len(scored_properties) > 0:
        logger.info(f"\nScore Statistics:")
        logger.info(f"  Highest score: {scored_properties['combined_score_4factors'].max():.2f}")
        logger.info(f"  Lowest score: {scored_properties['combined_score_4factors'].min():.2f}")
        logger.info(f"  Average score: {scored_properties['combined_score_4factors'].mean():.2f}")
        logger.info(f"  Median score: {scored_properties['combined_score_4factors'].median():.2f}")

    # Show top 10 properties by combined score
    logger.info("\n" + "=" * 80)
    logger.info("TOP 10 PROPERTIES BY COMBINED SCORE (4 FACTORS)")
    logger.info("=" * 80)

    top_10 = scored_properties.nlargest(10, 'combined_score_4factors')[
        ['address', 'price', 'bedrooms', 'property_size_sqm', 'distance_to_chinatown_km',
         'drive_time_to_chinatown_minutes', 'price_score', 'distance_score', 'time_score', 'size_score', 'combined_score_4factors']
    ]

    for i, (idx, row) in enumerate(top_10.iterrows(), 1):
        price_str = f"£{row['price']:.0f}" if pd.notna(row['price']) else "N/A"
        beds_str = f"{row['bedrooms']:.0f}" if pd.notna(row['bedrooms']) else "N/A"
        size_str = f"{row['property_size_sqm']:.0f}" if pd.notna(row['property_size_sqm']) else "N/A"
        dist_str = f"{row['distance_to_chinatown_km']:.1f}" if pd.notna(row['distance_to_chinatown_km']) else "N/A"
        time_str = f"{row['drive_time_to_chinatown_minutes']:.0f}" if pd.notna(row['drive_time_to_chinatown_minutes']) else "N/A"

        logger.info(f"\n{i}. SCORE: {row['combined_score_4factors']:.2f}")
        logger.info(f"   {row['address'][:70]}")
        logger.info(f"   {price_str} pcm | {beds_str} beds | {size_str} sqm | {dist_str} km | {time_str} min")
        logger.info(f"   Breakdown: Price={row['price_score']:.1f}, Distance={row['distance_score']:.1f}, Time={row['time_score']:.1f}, Size={row['size_score']:.1f}")

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
