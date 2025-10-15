#!/usr/bin/env python3
"""
Modern Rightmove scraper that works with the current website structure (2025)
The site now uses Next.js and embeds property data as JSON in the page
"""

import requests
import json
import re
import pandas as pd
from datetime import datetime


def scrape_rightmove(url):
    """
    Scrape Rightmove property data from the new Next.js-based site

    Args:
        url: Rightmove search results URL

    Returns:
        pandas.DataFrame with property listings
    """
    print(f"Fetching: {url}")
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
    result_count = search_results.get('resultCount', 'N/A')

    print(f"Found {len(properties)} properties on this page")
    print(f"Total results available: {result_count}")

    if not properties:
        print("No properties found!")
        return pd.DataFrame()

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


def main():
    # Your search URL
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=South+East+London&useLocationIdentifier=true&locationIdentifier=REGION%5E92828&rent=To+rent&radius=0.0&_includeLetAgreed=on&maxPrice=1500&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=South-East-London.html&maxBedrooms=2&dontShow=houseShare%2Cretirement%2Cstudent&minPrice=600"

    print("=" * 80)
    print("Modern Rightmove Scraper - South East London Rentals")
    print("=" * 80)
    print("\nSearch criteria:")
    print("- Location: South East London")
    print("- Price range: £600 - £1,500 pcm")
    print("- Max bedrooms: 2")
    print("- Include let agreed: Yes")
    print("- Exclude: House shares, retirement, student properties")
    print("\n" + "=" * 80)

    df, search_results = scrape_rightmove(url)

    if df.empty:
        print("No properties found!")
        return

    # Display summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total properties scraped: {len(df)}")
    print(f"Total available: {search_results.get('resultCount', 'N/A')}")

    if 'price' in df.columns and df['price'].notna().any():
        avg_price = df['price'].mean()
        min_price = df['price'].min()
        max_price = df['price'].max()
        print(f"Average rent: £{avg_price:,.0f} pcm")
        print(f"Price range: £{min_price:,.0f} - £{max_price:,.0f} pcm")

    # Summary by bedrooms
    if 'bedrooms' in df.columns:
        print("\n" + "=" * 80)
        print("BY NUMBER OF BEDROOMS")
        print("=" * 80)
        bedroom_summary = df.groupby('bedrooms').agg({
            'price': ['count', 'mean', 'min', 'max']
        }).round(0)
        bedroom_summary.columns = ['Count', 'Avg Price', 'Min Price', 'Max Price']
        print(bedroom_summary.to_string())

    # Summary by postcode
    if 'postcode' in df.columns and df['postcode'].notna().any():
        print("\n" + "=" * 80)
        print("TOP 10 POSTCODES")
        print("=" * 80)
        postcode_summary = df.dropna(subset=['postcode']).groupby('postcode').agg({
            'price': ['count', 'mean']
        }).round(0)
        postcode_summary.columns = ['Count', 'Avg Price']
        postcode_summary = postcode_summary.sort_values('Count', ascending=False).head(10)
        print(postcode_summary.to_string())

    # Display first 10 properties
    print("\n" + "=" * 80)
    print("FIRST 10 PROPERTIES")
    print("=" * 80)
    for idx, row in df.head(10).iterrows():
        print(f"\n{idx + 1}. {row['property_type'] if pd.notna(row['property_type']) else 'Property'}")
        print(f"   Address: {row['address']}")
        if pd.notna(row['bedrooms']):
            print(f"   Bedrooms: {int(row['bedrooms'])}")
        if pd.notna(row['price']):
            print(f"   Rent: £{int(row['price']):,} pcm")
        elif row['price_display']:
            print(f"   Rent: {row['price_display']}")
        if row['added_or_reduced']:
            print(f"   Status: {row['added_or_reduced']}")
        if row['branch']:
            print(f"   Agent: {row['branch']}")
        print(f"   URL: {row['property_url']}")

    # Save to CSV
    output_file = "south_east_london_rentals.csv"
    df.to_csv(output_file, index=False)
    print("\n" + "=" * 80)
    print(f"Full results saved to: {output_file}")
    print("=" * 80)

    print(f"\nAvailable columns:")
    print(", ".join(df.columns.tolist()))

    # Pagination info
    pagination = search_results.get('pagination', {})
    if pagination:
        print(f"\nPagination:")
        print(f"  Total pages available: {pagination.get('total', 'N/A')}")
        print(f"  Current page: {pagination.get('page', 'N/A')}")
        print(f"  Results per page: {pagination.get('size', 'N/A')}")

        if pagination.get('total', 0) > 1:
            print(f"\n  Note: This script only scraped the first page.")
            print(f"  You can scrape additional pages by adding '&index=24', '&index=48', etc. to the URL")


if __name__ == "__main__":
    main()
