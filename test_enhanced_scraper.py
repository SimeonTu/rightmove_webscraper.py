#!/usr/bin/env python3
"""
Test script for the enhanced Rightmove scraper
Tests individual listing scraping functionality
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path so we can import the enhanced_scraper
sys.path.append(str(Path(__file__).parent))

from enhanced_scraper import scrape_individual_listing, scrape_rightmove_page
import pandas as pd


def test_individual_listing_scraping():
    """Test scraping a single individual listing"""
    print("=" * 80)
    print("TESTING INDIVIDUAL LISTING SCRAPING")
    print("=" * 80)
    
    # Test with a sample property URL (you can replace this with a real URL)
    test_url = "https://www.rightmove.co.uk/properties/123456789"  # This will likely fail, but tests the function
    
    print(f"Testing with URL: {test_url}")
    print("Note: This will likely fail as it's not a real URL, but tests the function structure")
    
    result = scrape_individual_listing(test_url, delay=0.1)
    
    print(f"\nResult structure:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    return result


def test_search_results_scraping():
    """Test scraping search results (without individual listings)"""
    print("=" * 80)
    print("TESTING SEARCH RESULTS SCRAPING")
    print("=" * 80)
    
    # Use a real search URL with only 5 results (perfect for testing)
    test_url = "https://www.rightmove.co.uk/property-to-rent/find.html?useLocationIdentifier=true&locationIdentifier=OUTCODE%5E2335&rent=To+rent&radius=0.0&_includeLetAgreed=on&maxPrice=1500&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=SE8.html&maxBedrooms=2&dontShow=houseShare%2Cretirement%2Cstudent&minPrice=1400"
    
    print(f"Testing with URL: {test_url}")
    
    try:
        df, search_results = scrape_rightmove_page(test_url)
        
        print(f"\nSearch results:")
        print(f"  Properties found: {len(df)}")
        print(f"  Total available: {search_results.get('resultCount', 'Unknown')}")
        
        if not df.empty:
            print(f"\nSample property data:")
            print(f"  First property address: {df.iloc[0]['address']}")
            print(f"  First property price: £{df.iloc[0]['price']:,}" if pd.notna(df.iloc[0]['price']) else "  First property price: N/A")
            print(f"  First property URL: {df.iloc[0]['property_url']}")
        
        print("\n" + "=" * 80)
        return df, search_results
        
    except Exception as e:
        print(f"Error testing search results: {e}")
        print("\n" + "=" * 80)
        return None, None


def test_enhanced_scraping_small():
    """Test the enhanced scraper with a very small sample"""
    print("=" * 80)
    print("TESTING ENHANCED SCRAPING (SMALL SAMPLE)")
    print("=" * 80)
    
    from enhanced_scraper import scrape_all_pages_with_details
    
    test_url = "https://www.rightmove.co.uk/property-to-rent/find.html?useLocationIdentifier=true&locationIdentifier=OUTCODE%5E2335&rent=To+rent&radius=0.0&_includeLetAgreed=on&maxPrice=1500&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=SE8.html&maxBedrooms=2&dontShow=houseShare%2Cretirement%2Cstudent&minPrice=1400"
    
    print("Testing enhanced scraper with parameters optimized for 5-result dataset:")
    print("- max_pages: 1")
    print("- max_listings: 5 (all available)")
    print("- delay: 1.0 seconds")
    print("\nThis will take about 5-10 minutes...")
    
    try:
        df = scrape_all_pages_with_details(
            test_url,
            max_pages=1,  # Only first page
            max_listings=5,  # All 5 available listings
            delay=1.0  # 1 second delay
        )
        
        if not df.empty:
            print(f"\nEnhanced scraping results:")
            print(f"  Total properties: {len(df)}")
            print(f"  Successful individual scrapes: {df['scraping_success'].sum()}")
            print(f"  Failed individual scrapes: {(~df['scraping_success']).sum()}")
            
            # Save files to results folder
            from enhanced_scraper import create_output_folder, generate_enhanced_statistics
            output_folder = create_output_folder()
            
            # Save CSV
            csv_file = output_folder / "test_enhanced_properties.csv"
            df.to_csv(csv_file, index=False)
            
            # Generate statistics
            search_info = {
                "Location": "SE8 (Deptford, London) - TEST",
                "Price range": "£1,400 - £1,500 pcm",
                "Max bedrooms": "2",
                "Test run": "Yes"
            }
            stats_file = generate_enhanced_statistics(df, output_folder, search_info)
            
            print(f"\nFiles saved:")
            print(f"  CSV file: {csv_file}")
            print(f"  Statistics file: {stats_file}")
            print(f"  Output folder: {output_folder}")
            
            # Show sample data
            print(f"\nSample enhanced data:")
            for idx, row in df.head(2).iterrows():
                print(f"\n  Property {idx + 1}:")
                print(f"    Address: {row['address']}")
                print(f"    Price: £{row['price']:,}" if pd.notna(row['price']) else "    Price: N/A")
                print(f"    Size: {row['property_size_sqm']} sq m" if pd.notna(row['property_size_sqm']) else "    Size: N/A")
                print(f"    Scraping success: {row['scraping_success']}")
                if row['letting_details']:
                    print(f"    Letting details found: {len(row['letting_details'])} fields")
                    for key, value in list(row['letting_details'].items())[:2]:
                        print(f"      {key}: {value}")
        else:
            print("No data returned from enhanced scraping")
        
        print("\n" + "=" * 80)
        return df
        
    except Exception as e:
        print(f"Error in enhanced scraping: {e}")
        print("\n" + "=" * 80)
        return None


def main():
    """Run all tests"""
    print("ENHANCED RIGHTMOVE SCRAPER - TEST SUITE")
    print("=" * 80)
    
    # Test 1: Individual listing scraping (will likely fail with fake URL)
    print("\n1. Testing individual listing scraping...")
    individual_result = test_individual_listing_scraping()
    
    # Test 2: Search results scraping
    print("\n2. Testing search results scraping...")
    search_df, search_results = test_search_results_scraping()
    
    # Test 3: Enhanced scraping (small sample)
    if search_df is not None and not search_df.empty:
        print("\n3. Testing enhanced scraping with small sample...")
        enhanced_df = test_enhanced_scraping_small()
    else:
        print("\n3. Skipping enhanced scraping test (search results failed)")
        enhanced_df = None
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Individual listing test: {'PASSED' if individual_result else 'FAILED'}")
    print(f"Search results test: {'PASSED' if search_df is not None else 'FAILED'}")
    print(f"Enhanced scraping test: {'PASSED' if enhanced_df is not None else 'FAILED'}")
    print("=" * 80)
    
    if enhanced_df is not None and not enhanced_df.empty:
        print("\nThe enhanced scraper is working! You can now run:")
        print("python enhanced_scraper.py")
        print("\nTo scrape with your desired parameters.")
    else:
        print("\nSome tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
