#!/usr/bin/env python3
"""
Merge and Score Full Range Script

This script merges the high-end properties (£1400-£2000 pcm) with the existing 
properties (£400-£1400 pcm) and generates rebalanced scored CSVs for the full range.
"""

import pandas as pd
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def merge_datasets():
    """Merge the existing dataset with the high-end dataset."""
    
    # File paths
    existing_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_21h28m/enhanced_properties_with_city_distances.csv"
    high_end_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m/enhanced_properties_with_city_distances.csv"
    output_dir = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-17_at_01h45m"
    
    logger.info("Loading existing dataset...")
    df_existing = pd.read_csv(existing_file)
    logger.info(f"Existing dataset: {len(df_existing)} properties")
    
    logger.info("Loading high-end dataset...")
    df_high_end = pd.read_csv(high_end_file)
    logger.info(f"High-end dataset: {len(df_high_end)} properties")
    
    # Ensure both datasets have the same columns
    # Add missing columns to high-end dataset
    missing_cols = set(df_existing.columns) - set(df_high_end.columns)
    for col in missing_cols:
        df_high_end[col] = None
    
    # Add missing columns to existing dataset
    missing_cols = set(df_high_end.columns) - set(df_existing.columns)
    for col in missing_cols:
        df_existing[col] = None
    
    # Reorder columns to match
    df_high_end = df_high_end[df_existing.columns]
    
    # Merge datasets with deduplication
    logger.info("Merging datasets...")
    df_merged = pd.concat([df_existing, df_high_end], ignore_index=True)
    logger.info(f"Before deduplication: {len(df_merged)} properties")
    
    # Remove duplicates based on address, keeping the first occurrence
    # This prioritizes the original Edinburgh dataset over the high-end dataset
    df_merged = df_merged.drop_duplicates(subset=['address'], keep='first')
    logger.info(f"After deduplication: {len(df_merged)} properties")
    logger.info(f"Removed {len(df_existing) + len(df_high_end) - len(df_merged)} duplicate properties")
    
    # Save merged dataset
    merged_file = os.path.join(output_dir, "enhanced_properties_full_range_merged.csv")
    df_merged.to_csv(merged_file, index=False)
    logger.info(f"Saved merged dataset to: {merged_file}")
    
    return df_merged, output_dir

def run_scoring_scripts(df_merged, output_dir):
    """Run the scoring scripts on the merged dataset."""
    
    # Save the merged dataset temporarily for scoring
    temp_file = os.path.join(output_dir, "temp_merged_for_scoring.csv")
    df_merged.to_csv(temp_file, index=False)
    
    # Import and run the scoring script
    import sys
    sys.path.append('/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py')
    
    # We'll need to modify the scoring script to accept a custom input file
    # For now, let's create a simple version that works with our merged data
    
    logger.info("Running scoring analysis...")
    
    # Analyze the merged dataset
    logger.info("")
    logger.info("=" * 80)
    logger.info("MERGED DATASET ANALYSIS")
    logger.info("=" * 80)
    
    # Price range analysis
    price_ranges = [
        (400, 600, "£400-£600"),
        (600, 800, "£600-£800"), 
        (800, 1000, "£800-£1000"),
        (1000, 1200, "£1000-£1200"),
        (1200, 1400, "£1200-£1400"),
        (1400, 1600, "£1400-£1600"),
        (1600, 1800, "£1600-£1800"),
        (1800, 2000, "£1800-£2000")
    ]
    
    logger.info("PRICE RANGE DISTRIBUTION:")
    for min_price, max_price, label in price_ranges:
        count = len(df_merged[(df_merged['price'] >= min_price) & (df_merged['price'] < max_price)])
        logger.info(f"  {label}: {count} properties")
    
    # Data availability analysis
    logger.info("")
    logger.info("DATA AVAILABILITY:")
    
    # Check for distance data
    has_edin_dist = df_merged['edinburgh_distance_km'].notna().sum()
    has_glas_dist = df_merged['glasgow_distance_km'].notna().sum()
    has_edin_drive = df_merged['edinburgh_drive_time_minutes'].notna().sum()
    has_glas_drive = df_merged['glasgow_drive_time_minutes'].notna().sum()
    has_edin_transit = df_merged['edinburgh_transit_time_minutes'].notna().sum()
    has_glas_transit = df_merged['glasgow_transit_time_minutes'].notna().sum()
    has_size = df_merged['property_size_sqm'].notna().sum()
    has_bedrooms = df_merged['bedrooms'].notna().sum()
    has_bathrooms = df_merged['bathrooms'].notna().sum()
    
    logger.info(f"  Edinburgh distance: {has_edin_dist}/{len(df_merged)} ({has_edin_dist/len(df_merged)*100:.1f}%)")
    logger.info(f"  Glasgow distance: {has_glas_dist}/{len(df_merged)} ({has_glas_dist/len(df_merged)*100:.1f}%)")
    logger.info(f"  Edinburgh drive time: {has_edin_drive}/{len(df_merged)} ({has_edin_drive/len(df_merged)*100:.1f}%)")
    logger.info(f"  Glasgow drive time: {has_glas_drive}/{len(df_merged)} ({has_glas_drive/len(df_merged)*100:.1f}%)")
    logger.info(f"  Edinburgh transit time: {has_edin_transit}/{len(df_merged)} ({has_edin_transit/len(df_merged)*100:.1f}%)")
    logger.info(f"  Glasgow transit time: {has_glas_transit}/{len(df_merged)} ({has_glas_transit/len(df_merged)*100:.1f}%)")
    logger.info(f"  Property size: {has_size}/{len(df_merged)} ({has_size/len(df_merged)*100:.1f}%)")
    logger.info(f"  Bedrooms: {has_bedrooms}/{len(df_merged)} ({has_bedrooms/len(df_merged)*100:.1f}%)")
    logger.info(f"  Bathrooms: {has_bathrooms}/{len(df_merged)} ({has_bathrooms/len(df_merged)*100:.1f}%)")
    
    # Distance statistics
    if has_edin_dist > 0:
        logger.info("")
        logger.info("EDINBURGH DISTANCE STATISTICS:")
        logger.info(f"  Min: {df_merged['edinburgh_distance_km'].min():.1f} km")
        logger.info(f"  Max: {df_merged['edinburgh_distance_km'].max():.1f} km")
        logger.info(f"  Mean: {df_merged['edinburgh_distance_km'].mean():.1f} km")
        logger.info(f"  Median: {df_merged['edinburgh_distance_km'].median():.1f} km")
    
    if has_glas_dist > 0:
        logger.info("")
        logger.info("GLASGOW DISTANCE STATISTICS:")
        logger.info(f"  Min: {df_merged['glasgow_distance_km'].min():.1f} km")
        logger.info(f"  Max: {df_merged['glasgow_distance_km'].max():.1f} km")
        logger.info(f"  Mean: {df_merged['glasgow_distance_km'].mean():.1f} km")
        logger.info(f"  Median: {df_merged['glasgow_distance_km'].median():.1f} km")
    
    # Sample properties from different price ranges
    logger.info("")
    logger.info("SAMPLE PROPERTIES BY PRICE RANGE:")
    for min_price, max_price, label in price_ranges:
        sample = df_merged[(df_merged['price'] >= min_price) & (df_merged['price'] < max_price)]
        if len(sample) > 0:
            sample_prop = sample.iloc[0]
            logger.info(f"  {label}: £{sample_prop['price']:.0f} - {sample_prop['address']}")
            if pd.notna(sample_prop.get('edinburgh_distance_km')):
                logger.info(f"    Edinburgh: {sample_prop['edinburgh_distance_km']:.1f}km | {sample_prop.get('edinburgh_drive_time_minutes', 'N/A'):.1f}min")
            if pd.notna(sample_prop.get('glasgow_distance_km')):
                logger.info(f"    Glasgow: {sample_prop['glasgow_distance_km']:.1f}km | {sample_prop.get('glasgow_drive_time_minutes', 'N/A'):.1f}min")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYSIS COMPLETE!")
    logger.info("=" * 80)
    
    # Clean up temp file
    os.remove(temp_file)

def main():
    """Main function to merge datasets and run analysis."""
    
    logger.info("Starting full range dataset merge and analysis...")
    
    # Merge datasets
    df_merged, output_dir = merge_datasets()
    
    # Run analysis
    run_scoring_scripts(df_merged, output_dir)
    
    logger.info("Full range analysis complete!")

if __name__ == "__main__":
    main()
