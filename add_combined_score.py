#!/usr/bin/env python3
"""
Add Combined Score Script

This script adds a combined score field to the properties CSV based on:
- Price (lower is better)
- Distance to Chinatown (closer is better)
- Property size (larger is better)

Each factor is weighted equally (33.33% each) and normalized to 0-100 scale.
Only properties with size data available are scored.
"""

import pandas as pd
import numpy as np
import logging

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


def calculate_combined_score(row, price_scores, distance_scores, size_scores):
    """
    Calculate combined score for a property.

    Args:
        row: DataFrame row
        price_scores: Series of normalized price scores
        distance_scores: Series of normalized distance scores
        size_scores: Series of normalized size scores

    Returns:
        Combined score (0-100) or None if data is missing
    """
    # Check if this property has all required data
    if pd.isna(row['price']) or pd.isna(row['distance_to_chinatown_km']) or pd.isna(row['property_size_sqm']):
        return None

    # Get individual scores
    price_score = price_scores.get(row.name, 0)
    distance_score = distance_scores.get(row.name, 0)
    size_score = size_scores.get(row.name, 0)

    # Equal weighting: 33.33% each
    combined = (price_score + distance_score + size_score) / 3

    return round(combined, 2)


def main():
    """Main function to add combined score to CSV."""

    # File paths
    input_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_17h42m/enhanced_properties_with_chinatown_distance.csv"
    output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_17h42m/enhanced_properties_with_scores.csv"

    logger.info("=" * 80)
    logger.info("ADD COMBINED SCORE SCRIPT")
    logger.info("=" * 80)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 80)

    # Load the CSV
    try:
        df = pd.read_csv(input_file)
        logger.info(f"✓ Loaded {len(df)} properties")
    except Exception as e:
        logger.error(f"✗ Error loading CSV: {e}")
        return 1

    # Check required columns exist
    required_columns = ['price', 'distance_to_chinatown_km', 'property_size_sqm']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        logger.error(f"✗ Missing required columns: {missing_columns}")
        return 1

    logger.info("✓ All required columns present")

    # Filter to properties with all required data
    df_complete = df[
        df['price'].notna() &
        df['distance_to_chinatown_km'].notna() &
        df['property_size_sqm'].notna()
    ].copy()

    logger.info(f"\n✓ Found {len(df_complete)} properties with complete data (price, distance, size)")
    logger.info(f"  ({len(df_complete)/len(df)*100:.1f}% of total properties)")

    if len(df_complete) == 0:
        logger.error("✗ No properties with complete data found!")
        return 1

    # Display data ranges for context
    logger.info("\nData Ranges:")
    logger.info(f"  Price: £{df_complete['price'].min():.0f} - £{df_complete['price'].max():.0f}")
    logger.info(f"  Distance: {df_complete['distance_to_chinatown_km'].min():.2f} - {df_complete['distance_to_chinatown_km'].max():.2f} km")
    logger.info(f"  Size: {df_complete['property_size_sqm'].min():.1f} - {df_complete['property_size_sqm'].max():.1f} sqm")

    # Calculate normalized scores for properties with complete data
    logger.info("\nCalculating normalized scores...")

    # Price score: lower price = higher score
    price_scores = normalize_to_0_100(df_complete['price'], higher_is_better=False)
    logger.info("✓ Price scores calculated (lower price = higher score)")

    # Distance score: closer to Chinatown = higher score
    distance_scores = normalize_to_0_100(df_complete['distance_to_chinatown_km'], higher_is_better=False)
    logger.info("✓ Distance scores calculated (closer = higher score)")

    # Size score: larger size = higher score
    size_scores = normalize_to_0_100(df_complete['property_size_sqm'], higher_is_better=True)
    logger.info("✓ Size scores calculated (larger = higher score)")

    # Initialize score columns in main dataframe
    df['price_score'] = None
    df['distance_score'] = None
    df['size_score'] = None
    df['combined_score'] = None

    # Add individual scores to main dataframe
    df.loc[df_complete.index, 'price_score'] = price_scores.round(2)
    df.loc[df_complete.index, 'distance_score'] = distance_scores.round(2)
    df.loc[df_complete.index, 'size_score'] = size_scores.round(2)

    # Calculate combined scores
    logger.info("\nCalculating combined scores (equal weighting: 33.33% each)...")
    for idx, row in df_complete.iterrows():
        combined = calculate_combined_score(row, price_scores, distance_scores, size_scores)
        df.at[idx, 'combined_score'] = combined

    # Convert combined_score to numeric type
    df['combined_score'] = pd.to_numeric(df['combined_score'], errors='coerce')

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
    scored_properties = df[df['combined_score'].notna()]

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total properties: {len(df)}")
    logger.info(f"Properties with scores: {len(scored_properties)} ({len(scored_properties)/len(df)*100:.1f}%)")
    logger.info(f"Properties without scores: {len(df) - len(scored_properties)} (missing price/distance/size data)")

    if len(scored_properties) > 0:
        logger.info(f"\nScore Statistics:")
        logger.info(f"  Highest score: {scored_properties['combined_score'].max():.2f}")
        logger.info(f"  Lowest score: {scored_properties['combined_score'].min():.2f}")
        logger.info(f"  Average score: {scored_properties['combined_score'].mean():.2f}")
        logger.info(f"  Median score: {scored_properties['combined_score'].median():.2f}")

    # Show top 10 properties by combined score
    logger.info("\n" + "=" * 80)
    logger.info("TOP 10 PROPERTIES BY COMBINED SCORE")
    logger.info("=" * 80)

    top_10 = scored_properties.nlargest(10, 'combined_score')[
        ['address', 'price', 'bedrooms', 'property_size_sqm', 'distance_to_chinatown_km',
         'price_score', 'distance_score', 'size_score', 'combined_score']
    ]

    for i, (idx, row) in enumerate(top_10.iterrows(), 1):
        price_str = f"£{row['price']:.0f}" if pd.notna(row['price']) else "N/A"
        beds_str = f"{row['bedrooms']:.0f}" if pd.notna(row['bedrooms']) else "N/A"
        size_str = f"{row['property_size_sqm']:.0f}" if pd.notna(row['property_size_sqm']) else "N/A"
        dist_str = f"{row['distance_to_chinatown_km']:.1f}" if pd.notna(row['distance_to_chinatown_km']) else "N/A"

        logger.info(f"\n{i}. SCORE: {row['combined_score']:.2f}")
        logger.info(f"   {row['address'][:70]}")
        logger.info(f"   {price_str} pcm | {beds_str} beds | {size_str} sqm | {dist_str} km from Chinatown")
        logger.info(f"   Breakdown: Price={row['price_score']:.1f}, Distance={row['distance_score']:.1f}, Size={row['size_score']:.1f}")

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
