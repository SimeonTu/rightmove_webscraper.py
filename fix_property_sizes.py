#!/usr/bin/env python3
"""
Fix Property Sizes Script

This script replaces unrealistic property sizes (9999.0 sqm) with the average
size of all valid properties.
"""

import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main function to fix property sizes in CSV."""

    # File paths
    input_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_21h28m/enhanced_properties_with_city_distances.csv"
    output_file = "/Users/simeontu/Documents/vscode-projects/rightmove_webscraper.py/results/enhanced_scrape_2025-Oct-16_at_21h28m/enhanced_properties_with_city_distances.csv"

    logger.info("=" * 80)
    logger.info("FIX PROPERTY SIZES SCRIPT")
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

    # Check if property_size_sqft column exists
    if 'property_size_sqft' not in df.columns:
        logger.error("✗ Error: 'property_size_sqft' column not found in CSV")
        return 1

    # Count properties with 9999.0 sqft
    unrealistic_sizes = df['property_size_sqft'] == 9999.0
    unrealistic_count = unrealistic_sizes.sum()

    logger.info(f"\n✓ Found {unrealistic_count} properties with unrealistic size (9999.0 sqft)")

    if unrealistic_count == 0:
        logger.info("✓ No properties need fixing!")
        return 0

    # Calculate average of valid sizes (excluding 9999.0 and NaN)
    valid_sizes = df[(df['property_size_sqft'].notna()) & (df['property_size_sqft'] != 9999.0)]['property_size_sqft']

    if len(valid_sizes) == 0:
        logger.error("✗ No valid property sizes found to calculate average!")
        return 1

    average_size_sqft = valid_sizes.mean()
    average_size_sqm = average_size_sqft * 0.092903  # Convert sqft to sqm
    logger.info(f"✓ Calculated average size from {len(valid_sizes)} valid properties: {average_size_sqft:.2f} sqft ({average_size_sqm:.2f} sqm)")

    # Show some examples of properties being fixed
    logger.info("\nProperties being fixed:")
    properties_to_fix = df[unrealistic_sizes][['address', 'price', 'bedrooms', 'property_size_sqft']].head(10)
    for i, (idx, row) in enumerate(properties_to_fix.iterrows(), 1):
        logger.info(f"  {i}. {row['address'][:60]} - £{row['price']} pcm - {row['bedrooms']} beds")

    if unrealistic_count > 10:
        logger.info(f"  ... and {unrealistic_count - 10} more")

    # Replace 9999.0 with average in both sqft and sqm columns
    df.loc[unrealistic_sizes, 'property_size_sqft'] = round(average_size_sqft, 2)
    df.loc[unrealistic_sizes, 'property_size_sqm'] = round(average_size_sqm, 2)

    logger.info(f"\n✓ Replaced {unrealistic_count} unrealistic sizes with average ({average_size_sqft:.2f} sqft / {average_size_sqm:.2f} sqm)")

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
    logger.info(f"Total properties: {len(df)}")
    logger.info(f"Properties fixed: {unrealistic_count}")
    logger.info(f"Average size used: {average_size_sqft:.2f} sqft ({average_size_sqm:.2f} sqm)")

    # Show updated size distribution
    size_stats_sqft = df['property_size_sqft'].describe()
    size_stats_sqm = df['property_size_sqm'].describe()
    logger.info(f"\nUpdated Size Distribution (sqft):")
    logger.info(f"  Min: {size_stats_sqft['min']:.2f} sqft")
    logger.info(f"  Max: {size_stats_sqft['max']:.2f} sqft")
    logger.info(f"  Mean: {size_stats_sqft['mean']:.2f} sqft")
    logger.info(f"  Median: {size_stats_sqft['50%']:.2f} sqft")
    logger.info(f"\nUpdated Size Distribution (sqm):")
    logger.info(f"  Min: {size_stats_sqm['min']:.2f} sqm")
    logger.info(f"  Max: {size_stats_sqm['max']:.2f} sqm")
    logger.info(f"  Mean: {size_stats_sqm['mean']:.2f} sqm")
    logger.info(f"  Median: {size_stats_sqm['50%']:.2f} sqm")

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
