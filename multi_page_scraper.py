#!/usr/bin/env python3
"""
Multi-page Rightmove scraper that collects ALL results from a search
Works with the current Next.js-based Rightmove website (2025)
"""

import requests
import json
import re
import pandas as pd
from datetime import datetime
import time
import os
from pathlib import Path
from typing import Tuple, Optional


def scrape_rightmove_page(url: str) -> Tuple[pd.DataFrame, dict]:
    """
    Scrape a single page of Rightmove property data

    Args:
        url: Rightmove search results URL

    Returns:
        Tuple of (DataFrame with property listings, search_results dict)
    """
    r = requests.get(url)

    if r.status_code != 200:
        raise Exception(f"Failed to fetch page. Status code: {r.status_code}")

    # Extract JSON data from Next.js script tag
    pattern = r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>'
    matches = re.findall(pattern, r.text, re.DOTALL)

    if not matches:
        raise Exception("Could not find property data in page")

    data = json.loads(matches[0])

    # Navigate to property data
    search_results = data['props']['pageProps']['searchResults']
    properties = search_results.get('properties', [])

    if not properties:
        return pd.DataFrame(), search_results

    # Extract relevant fields from each property
    extracted_data = []
    for prop in properties:
        property_data = {
            'id': prop.get('id'),
            'price': prop.get('price', {}).get('amount'),
            'price_display': prop.get('price', {}).get('displayPrices', [{}])[0].get('displayPrice'),
            'frequency': prop.get('price', {}).get('frequency'),
            'property_type': prop.get('propertySubType'),
            'bedrooms': prop.get('bedrooms'),
            'bathrooms': prop.get('bathrooms'),
            'address': prop.get('displayAddress'),
            'summary': prop.get('summary'),
            'property_url': f"https://www.rightmove.co.uk{prop.get('propertyUrl', '')}",
            'contact_url': prop.get('contactUrl'),
            'branch': prop.get('customer', {}).get('branchDisplayName'),
            'branch_id': prop.get('customer', {}).get('branchId'),
            'added_or_reduced': prop.get('addedOrReduced'),
            'first_visible_date': prop.get('firstVisibleDate'),
            'let_type': prop.get('letType'),
            'postcode': None,  # Will extract from address
            'search_date': datetime.now().isoformat()
        }

        # Extract postcode from address if possible
        if property_data['address']:
            # UK postcode pattern (simplified)
            postcode_match = re.search(r'\b([A-Z]{1,2}[0-9][A-Z0-9]?)\b', property_data['address'])
            if postcode_match:
                property_data['postcode'] = postcode_match.group(1)

        extracted_data.append(property_data)

    # Convert to DataFrame
    df = pd.DataFrame(extracted_data)

    return df, search_results


def scrape_all_pages(base_url: str, max_pages: Optional[int] = None, delay: float = 1.0) -> pd.DataFrame:
    """
    Scrape all pages of results from a Rightmove search

    Args:
        base_url: Base search URL (without index parameter)
        max_pages: Maximum number of pages to scrape (None = all pages)
        delay: Delay in seconds between requests to be polite to the server

    Returns:
        DataFrame containing all properties from all pages
    """
    all_properties = []
    page_num = 0
    index = 0

    print("=" * 80)
    print("Multi-Page Rightmove Scraper")
    print("=" * 80)

    # First page
    print(f"\nFetching page {page_num + 1}...")

    # Remove existing index parameter if present and clean up URL
    clean_url = re.sub(r'&index=\d+', '', base_url)
    if not clean_url.endswith('?') and '?' not in clean_url.split('/')[-1]:
        if '&' in clean_url:
            clean_url = clean_url  # Already has parameters
        else:
            clean_url += '?'

    try:
        df, search_results = scrape_rightmove_page(clean_url)

        if df.empty:
            print("No properties found!")
            return pd.DataFrame()

        all_properties.append(df)

        # Get pagination info
        pagination = search_results.get('pagination', {})
        total_pages = pagination.get('total', 1)
        result_count = search_results.get('resultCount', 'Unknown')

        print(f"✓ Page 1: {len(df)} properties")
        print(f"Total results available: {result_count}")
        print(f"Total pages available: {total_pages}")

        # Determine how many pages to scrape
        pages_to_scrape = min(max_pages, total_pages) if max_pages else total_pages

        if pages_to_scrape > 1:
            print(f"\nScraping {pages_to_scrape - 1} more pages...")

        # Scrape remaining pages
        for page_num in range(1, pages_to_scrape):
            time.sleep(delay)  # Be polite to the server

            index = page_num * 24  # Rightmove uses 24 results per page
            page_url = f"{clean_url}&index={index}"

            print(f"Fetching page {page_num + 1}... ", end='', flush=True)

            try:
                df, _ = scrape_rightmove_page(page_url)

                if df.empty:
                    print("✗ No properties found, stopping")
                    break

                all_properties.append(df)
                print(f"✓ {len(df)} properties")

            except Exception as e:
                print(f"✗ Error: {e}")
                print(f"Stopping at page {page_num}")
                break

        # Combine all pages
        if all_properties:
            combined_df = pd.concat(all_properties, ignore_index=True)

            # Remove duplicates (in case any property appears on multiple pages)
            original_count = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset=['id'], keep='first')
            duplicates_removed = original_count - len(combined_df)

            print("\n" + "=" * 80)
            print(f"Total properties scraped: {len(combined_df)}")
            if duplicates_removed > 0:
                print(f"Duplicates removed: {duplicates_removed}")
            print("=" * 80)

            return combined_df
        else:
            return pd.DataFrame()

    except Exception as e:
        print(f"Error scraping first page: {e}")
        return pd.DataFrame()


def create_output_folder() -> Path:
    """
    Create a timestamped output folder for this scraping session

    Returns:
        Path to the created output folder
    """
    # Create main results folder if it doesn't exist
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # Create timestamped subfolder for this run with clearer format
    # Format: 2025-Oct-15_at_13h45m
    timestamp = datetime.now().strftime("%Y-%b-%d_at_%Hh%Mm")
    run_folder = results_dir / f"scrape_{timestamp}"
    run_folder.mkdir(exist_ok=True)

    return run_folder


def generate_full_statistics(df: pd.DataFrame, output_folder: Path, search_info: dict = None):
    """
    Generate a comprehensive statistics text file with ALL data (not limited to top 10/15)

    Args:
        df: DataFrame with property data
        output_folder: Folder to save the statistics file
        search_info: Optional dict with search criteria information
    """
    stats_file = output_folder / "statistics.txt"

    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RIGHTMOVE PROPERTY SCRAPER - FULL STATISTICS REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        # Search criteria if provided
        if search_info:
            f.write("SEARCH CRITERIA\n")
            f.write("-" * 80 + "\n")
            for key, value in search_info.items():
                f.write(f"{key}: {value}\n")
            f.write("\n" + "=" * 80 + "\n\n")

        if df.empty:
            f.write("No data available.\n")
            return

        # Overall statistics
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total properties: {len(df)}\n")

        if 'price' in df.columns and df['price'].notna().any():
            price_data = df['price'].dropna()
            f.write(f"\nPrice statistics:\n")
            f.write(f"  Count (with price): {len(price_data)}\n")
            f.write(f"  Average: £{price_data.mean():,.2f} pcm\n")
            f.write(f"  Median:  £{price_data.median():,.2f} pcm\n")
            f.write(f"  Std Dev: £{price_data.std():,.2f}\n")
            f.write(f"  Min:     £{price_data.min():,.2f} pcm\n")
            f.write(f"  Max:     £{price_data.max():,.2f} pcm\n")

            # Quartiles
            f.write(f"\nPrice quartiles:\n")
            f.write(f"  25th percentile: £{price_data.quantile(0.25):,.2f} pcm\n")
            f.write(f"  50th percentile: £{price_data.quantile(0.50):,.2f} pcm\n")
            f.write(f"  75th percentile: £{price_data.quantile(0.75):,.2f} pcm\n")

        f.write("\n" + "=" * 80 + "\n\n")

        # Full bedroom summary
        if 'bedrooms' in df.columns and df['bedrooms'].notna().any():
            f.write("FULL BREAKDOWN BY NUMBER OF BEDROOMS\n")
            f.write("-" * 80 + "\n")
            bedroom_summary = df.dropna(subset=['price']).groupby('bedrooms').agg({
                'price': ['count', 'mean', 'median', 'std', 'min', 'max']
            }).round(2)
            bedroom_summary.columns = ['Count', 'Avg Price', 'Median Price', 'Std Dev', 'Min Price', 'Max Price']
            f.write(bedroom_summary.to_string())
            f.write("\n\n" + "=" * 80 + "\n\n")

        # Full postcode summary (ALL postcodes, not just top 15)
        if 'postcode' in df.columns and df['postcode'].notna().any():
            f.write("FULL BREAKDOWN BY POSTCODE (ALL POSTCODES)\n")
            f.write("-" * 80 + "\n")
            postcode_summary = df.dropna(subset=['postcode', 'price']).groupby('postcode').agg({
                'price': ['count', 'mean', 'median', 'min', 'max']
            }).round(2)
            postcode_summary.columns = ['Count', 'Avg Price', 'Median Price', 'Min Price', 'Max Price']
            postcode_summary = postcode_summary.sort_values('Count', ascending=False)
            f.write(f"Total unique postcodes: {len(postcode_summary)}\n\n")
            f.write(postcode_summary.to_string())
            f.write("\n\n" + "=" * 80 + "\n\n")

        # Full property type summary (ALL types)
        if 'property_type' in df.columns and df['property_type'].notna().any():
            f.write("FULL BREAKDOWN BY PROPERTY TYPE (ALL TYPES)\n")
            f.write("-" * 80 + "\n")
            type_summary = df.dropna(subset=['property_type', 'price']).groupby('property_type').agg({
                'price': ['count', 'mean', 'median', 'min', 'max']
            }).round(2)
            type_summary.columns = ['Count', 'Avg Price', 'Median Price', 'Min Price', 'Max Price']
            type_summary = type_summary.sort_values('Count', ascending=False)
            f.write(f"Total unique property types: {len(type_summary)}\n\n")
            f.write(type_summary.to_string())
            f.write("\n\n" + "=" * 80 + "\n\n")

        # Bathroom summary if available
        if 'bathrooms' in df.columns and df['bathrooms'].notna().any():
            f.write("FULL BREAKDOWN BY NUMBER OF BATHROOMS\n")
            f.write("-" * 80 + "\n")
            bathroom_summary = df.dropna(subset=['bathrooms', 'price']).groupby('bathrooms').agg({
                'price': ['count', 'mean', 'median', 'min', 'max']
            }).round(2)
            bathroom_summary.columns = ['Count', 'Avg Price', 'Median Price', 'Min Price', 'Max Price']
            bathroom_summary = bathroom_summary.sort_values('Count', ascending=False)
            f.write(bathroom_summary.to_string())
            f.write("\n\n" + "=" * 80 + "\n\n")

        # Agent/Branch summary
        if 'branch' in df.columns and df['branch'].notna().any():
            f.write("FULL BREAKDOWN BY ESTATE AGENT (ALL AGENTS)\n")
            f.write("-" * 80 + "\n")
            agent_summary = df.dropna(subset=['branch', 'price']).groupby('branch').agg({
                'price': ['count', 'mean', 'median']
            }).round(2)
            agent_summary.columns = ['Count', 'Avg Price', 'Median Price']
            agent_summary = agent_summary.sort_values('Count', ascending=False)
            f.write(f"Total unique agents: {len(agent_summary)}\n\n")
            f.write(agent_summary.to_string())
            f.write("\n\n" + "=" * 80 + "\n\n")

        # Added/Reduced status summary
        if 'added_or_reduced' in df.columns and df['added_or_reduced'].notna().any():
            f.write("BREAKDOWN BY LISTING STATUS\n")
            f.write("-" * 80 + "\n")
            status_summary = df[df['added_or_reduced'].notna()]['added_or_reduced'].value_counts()
            for status, count in status_summary.items():
                f.write(f"{status}: {count}\n")
            f.write("\n" + "=" * 80 + "\n\n")

        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")

    return stats_file


def display_summary(df: pd.DataFrame):
    """Display summary statistics for the scraped properties"""

    if df.empty:
        print("\nNo data to display")
        return

    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total properties: {len(df)}")

    if 'price' in df.columns and df['price'].notna().any():
        avg_price = df['price'].mean()
        median_price = df['price'].median()
        min_price = df['price'].min()
        max_price = df['price'].max()
        print(f"\nPrice statistics:")
        print(f"  Average: £{avg_price:,.0f} pcm")
        print(f"  Median:  £{median_price:,.0f} pcm")
        print(f"  Range:   £{min_price:,.0f} - £{max_price:,.0f} pcm")

    # Summary by bedrooms
    if 'bedrooms' in df.columns and df['bedrooms'].notna().any():
        print("\n" + "=" * 80)
        print("BY NUMBER OF BEDROOMS")
        print("=" * 80)
        bedroom_summary = df.dropna(subset=['price']).groupby('bedrooms').agg({
            'price': ['count', 'mean', 'median', 'min', 'max']
        }).round(0)
        bedroom_summary.columns = ['Count', 'Avg Price', 'Median Price', 'Min Price', 'Max Price']
        print(bedroom_summary.to_string())

    # Summary by postcode
    if 'postcode' in df.columns and df['postcode'].notna().any():
        print("\n" + "=" * 80)
        print("TOP 15 POSTCODES")
        print("=" * 80)
        postcode_summary = df.dropna(subset=['postcode', 'price']).groupby('postcode').agg({
            'price': ['count', 'mean']
        }).round(0)
        postcode_summary.columns = ['Count', 'Avg Price']
        postcode_summary = postcode_summary.sort_values('Count', ascending=False).head(15)
        print(postcode_summary.to_string())

    # Summary by property type
    if 'property_type' in df.columns and df['property_type'].notna().any():
        print("\n" + "=" * 80)
        print("TOP 10 PROPERTY TYPES")
        print("=" * 80)
        type_summary = df.dropna(subset=['property_type', 'price']).groupby('property_type').agg({
            'price': ['count', 'mean']
        }).round(0)
        type_summary.columns = ['Count', 'Avg Price']
        type_summary = type_summary.sort_values('Count', ascending=False).head(10)
        print(type_summary.to_string())


def main():
    # Your search URL
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=South+East+London&useLocationIdentifier=true&locationIdentifier=REGION%5E92828&rent=To+rent&radius=0.0&_includeLetAgreed=on&maxPrice=1500&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=South-East-London.html&maxBedrooms=2&dontShow=houseShare%2Cretirement%2Cstudent&minPrice=600"

    # Search criteria for documentation
    search_info = {
        "Location": "South East London",
        "Price range": "£600 - £1,500 pcm",
        "Max bedrooms": "2",
        "Include let agreed": "Yes",
        "Exclude": "House shares, retirement, student properties",
        "Search URL": url
    }

    print("\nSearch criteria:")
    for key, value in search_info.items():
        if key != "Search URL":
            print(f"- {key}: {value}")

    # Create output folder for this run
    print("\n" + "=" * 80)
    output_folder = create_output_folder()
    print(f"Output folder created: {output_folder}")
    print("=" * 80)

    # Scrape all pages (or set max_pages to limit)
    # Examples:
    # df = scrape_all_pages(url, max_pages=5)  # Scrape first 5 pages only
    # df = scrape_all_pages(url)  # Scrape all pages

    df = scrape_all_pages(url, delay=1.5)  # 1.5 second delay between requests

    if df.empty:
        print("\nNo properties were scraped.")
        return

    # Display summary
    display_summary(df)

    # Save CSV to output folder
    csv_file = output_folder / "properties.csv"
    df.to_csv(csv_file, index=False)

    # Generate full statistics file
    stats_file = generate_full_statistics(df, output_folder, search_info)

    print(f"\n" + "=" * 80)
    print("FILES SAVED")
    print("=" * 80)
    print(f"CSV file:        {csv_file}")
    print(f"Statistics file: {stats_file}")
    print(f"Output folder:   {output_folder}")
    print("=" * 80)

    # Display sample properties
    print("\n" + "=" * 80)
    print("SAMPLE PROPERTIES (First 5 and Last 5)")
    print("=" * 80)

    for idx, row in df.head(5).iterrows():
        print(f"\n{idx + 1}. {row['property_type'] if pd.notna(row['property_type']) else 'Property'}")
        print(f"   Address: {row['address']}")
        if pd.notna(row['bedrooms']):
            print(f"   Bedrooms: {int(row['bedrooms'])}")
        if pd.notna(row['price']):
            print(f"   Rent: £{int(row['price']):,} pcm")
        if row['branch']:
            print(f"   Agent: {row['branch']}")

    print("\n" + "..." + "\n")

    for idx, row in df.tail(5).iterrows():
        print(f"\n{idx + 1}. {row['property_type'] if pd.notna(row['property_type']) else 'Property'}")
        print(f"   Address: {row['address']}")
        if pd.notna(row['bedrooms']):
            print(f"   Bedrooms: {int(row['bedrooms'])}")
        if pd.notna(row['price']):
            print(f"   Rent: £{int(row['price']):,} pcm")
        if row['branch']:
            print(f"   Agent: {row['branch']}")

    print("\n" + "=" * 80)
    print("Scraping complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
