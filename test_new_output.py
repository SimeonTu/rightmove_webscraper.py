#!/usr/bin/env python3
"""Test script to verify the new output folder structure works correctly"""

from multi_page_scraper import scrape_all_pages, create_output_folder, generate_full_statistics

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

print("\nTesting new output structure...")
print("Scraping first 2 pages only for testing...\n")

# Create output folder
output_folder = create_output_folder()
print(f"✓ Created output folder: {output_folder}\n")

# Scrape just 2 pages for testing
df = scrape_all_pages(url, max_pages=2, delay=1.0)

if df.empty:
    print("No data scraped")
    exit(1)

print(f"\n✓ Scraped {len(df)} properties\n")

# Save CSV
csv_file = output_folder / "properties.csv"
df.to_csv(csv_file, index=False)
print(f"✓ Saved CSV: {csv_file}")

# Generate statistics
stats_file = generate_full_statistics(df, output_folder, search_info)
print(f"✓ Generated statistics: {stats_file}")

print("\n" + "=" * 80)
print("TEST SUCCESSFUL!")
print("=" * 80)
print(f"Check the folder: {output_folder}")
print("It should contain:")
print("  - properties.csv (property data)")
print("  - statistics.txt (full statistics report)")
print("=" * 80)
