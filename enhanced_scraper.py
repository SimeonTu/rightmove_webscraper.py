#!/usr/bin/env python3
"""
Enhanced Rightmove scraper that scrapes both search results AND individual listing pages
to extract detailed letting information and property size data
"""

import requests
import json
import re
import csv
import pandas as pd
from datetime import datetime
import time
import os
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_deposit_value(value: str) -> str:
    """
    Clean deposit value by removing tooltip text and keeping only the amount
    
    Args:
        value: Raw deposit value from HTML
        
    Returns:
        Cleaned deposit value with only the amount
    """
    if not value:
        return value
    
    # Remove common tooltip text patterns
    patterns_to_remove = [
        r'A deposit provides security for a landlord against damage.*$',
        r'Read moreaboutdepositin our glossary page.*$',
        r'Read more about deposit in our glossary page.*$',
        r'Read more.*glossary.*$',
        r'aboutdepositin.*$'
    ]
    
    cleaned_value = value
    for pattern in patterns_to_remove:
        cleaned_value = re.sub(pattern, '', cleaned_value, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up any extra whitespace
    cleaned_value = cleaned_value.strip()
    
    return cleaned_value


def scrape_individual_listing(property_url: str, delay: float = 1.0) -> Dict[str, Any]:
    """
    Scrape detailed information from an individual property listing page
    
    Args:
        property_url: URL of the individual property listing
        delay: Delay in seconds before making the request
        
    Returns:
        Dictionary with detailed property information
    """
    if delay > 0:
        time.sleep(delay)
    
    try:
        logger.info(f"Scraping individual listing: {property_url}")
        
        # Add headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(property_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Initialize result dictionary
        detailed_info = {
            'property_url': property_url,
            'letting_details': {},
            'property_size_sqft': None,
            'property_size_sqm': None,
            'scraping_success': True,
            'scraping_error': None
        }
        
        # Extract letting details from the specific HTML structure
        # Method 1: Look for the letting details heading and its associated dl
        letting_heading = soup.find('h2', string=re.compile(r'Letting details', re.IGNORECASE))
        if letting_heading:
            logger.info(f"Found letting details heading: {letting_heading.get_text(strip=True)}")
            # Find the dl element containing the details
            dl_element = letting_heading.find_next('dl')
            if dl_element:
                logger.info(f"Found dl element with {len(dl_element.find_all('div'))} detail divs")
                # Extract all dt/dd pairs from divs within the dl
                for detail_div in dl_element.find_all('div'):
                    dt = detail_div.find('dt')
                    dd = detail_div.find('dd')
                    if dt and dd:
                        key = dt.get_text(strip=True).replace(':', '').strip().lower()
                        value = dd.get_text(strip=True)
                        
                        # Clean deposit value if it's a deposit field
                        if 'deposit' in key:
                            value = clean_deposit_value(value)
                        
                        detailed_info['letting_details'][key] = value
                        logger.info(f"Extracted letting detail: {key} = {value}")
            else:
                logger.warning("No dl element found after letting details heading")
        else:
            logger.warning("No letting details heading found")
        
        # Method 2: Alternative approach - look for any dl with dt/dd pairs that contain letting-related terms
        if not detailed_info['letting_details']:
            logger.info("Trying alternative method for letting details extraction")
            letting_terms = ['let available date', 'deposit', 'min. tenancy', 'let type', 'furnish type', 'council tax']
            dl_count = 0
            for dl in soup.find_all('dl'):
                dl_count += 1
                for detail_div in dl.find_all('div'):
                    dt = detail_div.find('dt')
                    dd = detail_div.find('dd')
                    if dt and dd:
                        dt_text = dt.get_text(strip=True).lower()
                        if any(term in dt_text for term in letting_terms):
                            key = dt.get_text(strip=True).replace(':', '').strip().lower()
                            value = dd.get_text(strip=True)
                            
                            # Clean deposit value if it's a deposit field
                            if 'deposit' in key:
                                value = clean_deposit_value(value)
                            
                            detailed_info['letting_details'][key] = value
                            logger.info(f"Extracted letting detail (alt method): {key} = {value}")
            logger.info(f"Checked {dl_count} dl elements for letting details")
        
        # Extract property size information
        # Method 1: Look for SIZE in any dt element (including nested spans)
        size_section = soup.find('dt', string=re.compile(r'SIZE', re.IGNORECASE))
        if not size_section:
            # Try looking for SIZE in nested spans
            size_span = soup.find('span', string=re.compile(r'SIZE', re.IGNORECASE))
            if size_span:
                size_section = size_span.find_parent('dt')
        
        if size_section:
            logger.info(f"Found SIZE section: {size_section.get_text(strip=True)}")
            size_dd = size_section.find_next('dd')
            if size_dd:
                # Look for size information in the dd element
                size_text = size_dd.get_text(strip=True)
                logger.info(f"Size text: {size_text}")
                
                # Check if it's "Ask agent" or similar
                if 'ask agent' in size_text.lower() or 'contact' in size_text.lower():
                    logger.info("Size data not available (Ask agent)")
                else:
                    # Extract sq ft
                    sqft_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*ft', size_text, re.IGNORECASE)
                    if sqft_match:
                        detailed_info['property_size_sqft'] = int(sqft_match.group(1).replace(',', ''))
                        logger.info(f"Extracted sq ft: {detailed_info['property_size_sqft']}")
                    
                    # Extract sq m
                    sqm_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*m', size_text, re.IGNORECASE)
                    if sqm_match:
                        detailed_info['property_size_sqm'] = int(sqm_match.group(1).replace(',', ''))
                        logger.info(f"Extracted sq m: {detailed_info['property_size_sqm']}")
            else:
                logger.warning("No dd element found after SIZE dt")
        else:
            logger.warning("No SIZE section found")
        
        # Method 2: Look for size in the info-reel section (data-test="infoReel")
        if not detailed_info['property_size_sqft'] and not detailed_info['property_size_sqm']:
            info_reel = soup.find('dl', {'data-test': 'infoReel'})
            if info_reel:
                size_dt = info_reel.find('dt', string=re.compile(r'SIZE', re.IGNORECASE))
                if size_dt:
                    size_dd = size_dt.find_next('dd')
                    if size_dd:
                        size_text = size_dd.get_text(strip=True)
                        
                        # Extract sq ft
                        sqft_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*ft', size_text, re.IGNORECASE)
                        if sqft_match:
                            detailed_info['property_size_sqft'] = int(sqft_match.group(1).replace(',', ''))
                        
                        # Extract sq m
                        sqm_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*m', size_text, re.IGNORECASE)
                        if sqm_match:
                            detailed_info['property_size_sqm'] = int(sqm_match.group(1).replace(',', ''))
        
        # Method 3: Look for any element containing size information
        if not detailed_info['property_size_sqft'] and not detailed_info['property_size_sqm']:
            # Search for any text containing size patterns
            size_patterns = [
                r'(\d+(?:,\d+)*)\s*sq\s*ft',
                r'(\d+(?:,\d+)*)\s*sq\s*m',
                r'(\d+(?:,\d+)*)\s*square\s*feet',
                r'(\d+(?:,\d+)*)\s*square\s*meters?'
            ]
            
            for pattern in size_patterns:
                matches = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
                for match in matches:
                    if 'sq ft' in match.lower():
                        sqft_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*ft', match, re.IGNORECASE)
                        if sqft_match:
                            detailed_info['property_size_sqft'] = int(sqft_match.group(1).replace(',', ''))
                    elif 'sq m' in match.lower():
                        sqm_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*m', match, re.IGNORECASE)
                        if sqm_match:
                            detailed_info['property_size_sqm'] = int(sqm_match.group(1).replace(',', ''))
        
        logger.info(f"Successfully scraped: {property_url}")
        return detailed_info
        
    except Exception as e:
        logger.error(f"Error scraping {property_url}: {str(e)}")
        return {
            'property_url': property_url,
            'letting_details': {},
            'property_size_sqft': None,
            'property_size_sqm': None,
            'scraping_success': False,
            'scraping_error': str(e)
        }


def scrape_rightmove_page(url: str) -> Tuple[pd.DataFrame, dict]:
    """
    Scrape a single page of Rightmove property data (existing functionality)
    
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


def scrape_all_pages_with_details(base_url: str, max_pages: Optional[int] = None, 
                                 max_listings: Optional[int] = None, 
                                 delay: float = 1.0) -> pd.DataFrame:
    """
    Scrape all pages of results AND individual listing details
    
    Args:
        base_url: Base search URL (without index parameter)
        max_pages: Maximum number of pages to scrape (None = all pages)
        max_listings: Maximum number of individual listings to scrape (None = all)
        delay: Delay in seconds between requests
        
    Returns:
        DataFrame containing all properties with detailed information
    """
    all_properties = []
    page_num = 0
    index = 0
    total_listings_scraped = 0

    print("=" * 80)
    print("Enhanced Rightmove Scraper with Individual Listing Details")
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
            print(f"Estimated time: {(pages_to_scrape - 1) * delay:.1f} seconds for search results")

        # Scrape remaining pages
        for page_num in range(1, pages_to_scrape):
            time.sleep(delay)  # Be polite to the server

            index = page_num * 24  # Rightmove uses 24 results per page
            page_url = f"{clean_url}&index={index}"

            print(f"Fetching page {page_num + 1}... ", end='', flush=True)

            try:
                df_page, _ = scrape_rightmove_page(page_url)

                if df_page.empty:
                    print("✗ No properties found, stopping")
                    break

                df = pd.concat([df, df_page], ignore_index=True)
                print(f"✓ {len(df_page)} properties")

            except Exception as e:
                print(f"✗ Error: {e}")
                print(f"Stopping at page {page_num}")
                break

        # Remove duplicates
        original_count = len(df)
        df = df.drop_duplicates(subset=['id'], keep='first')
        duplicates_removed = original_count - len(df)

        print(f"\nTotal properties from search results: {len(df)}")
        if duplicates_removed > 0:
            print(f"Duplicates removed: {duplicates_removed}")

        # Now scrape individual listing details
        print(f"\n{'='*80}")
        print("SCRAPING INDIVIDUAL LISTING DETAILS")
        print(f"{'='*80}")
        
        # Determine how many listings to scrape
        listings_to_scrape = min(max_listings, len(df)) if max_listings else len(df)
        print(f"Scraping details for {listings_to_scrape} individual listings...")
        print(f"Estimated time: {listings_to_scrape * delay:.1f} seconds for individual pages")
        print(f"Progress will be shown every 10 listings...")
        
        detailed_data = []
        successful_scrapes = 0
        failed_scrapes = 0
        
        for idx, row in df.head(listings_to_scrape).iterrows():
            if total_listings_scraped >= listings_to_scrape:
                break
                
            print(f"Scraping listing {total_listings_scraped + 1}/{listings_to_scrape}: {row['address'][:50]}...")
            
            detailed_info = scrape_individual_listing(row['property_url'], delay)
            
            # Combine search result data with detailed info
            combined_data = row.to_dict()
            combined_data.update({
                'letting_details': detailed_info['letting_details'],
                'property_size_sqft': detailed_info['property_size_sqft'],
                'property_size_sqm': detailed_info['property_size_sqm'],
                'scraping_success': detailed_info['scraping_success'],
                'scraping_error': detailed_info['scraping_error']
            })
            
            detailed_data.append(combined_data)
            total_listings_scraped += 1
            
            if detailed_info['scraping_success']:
                successful_scrapes += 1
            else:
                failed_scrapes += 1
            
            # Progress update every 10 listings
            if total_listings_scraped % 10 == 0:
                print(f"Progress: {total_listings_scraped}/{listings_to_scrape} listings scraped")
        
        # Convert to DataFrame
        enhanced_df = pd.DataFrame(detailed_data)
        
        print(f"\n{'='*80}")
        print("INDIVIDUAL LISTING SCRAPING COMPLETE")
        print(f"{'='*80}")
        print(f"Total listings processed: {total_listings_scraped}")
        print(f"Successful scrapes: {successful_scrapes}")
        print(f"Failed scrapes: {failed_scrapes}")
        print(f"Success rate: {(successful_scrapes/total_listings_scraped*100):.1f}%" if total_listings_scraped > 0 else "N/A")
        
        print(f"\n{'='*80}")
        print("SCRAPING COMPLETE - SUMMARY")
        print(f"{'='*80}")
        print(f"Total properties found: {len(enhanced_df)}")
        print(f"Total pages scraped: {pages_to_scrape}")
        print(f"Individual pages scraped: {total_listings_scraped}")
        print(f"Overall success rate: {(successful_scrapes/total_listings_scraped*100):.1f}%" if total_listings_scraped > 0 else "N/A")
        
        return enhanced_df

    except Exception as e:
        print(f"Error scraping search results: {e}")
        return pd.DataFrame()


def generate_enhanced_statistics(df: pd.DataFrame, output_folder: Path, search_info: dict = None):
    """
    Generate comprehensive statistics including letting details and property size data
    
    Args:
        df: DataFrame with enhanced property data
        output_folder: Folder to save the statistics file
        search_info: Optional dict with search criteria information
    """
    stats_file = output_folder / "enhanced_statistics.txt"

    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ENHANCED RIGHTMOVE SCRAPER - DETAILED STATISTICS REPORT\n")
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
        
        # Scraping success statistics
        if 'scraping_success' in df.columns:
            successful_scrapes = df['scraping_success'].sum()
            failed_scrapes = len(df) - successful_scrapes
            f.write(f"Individual listing scrapes:\n")
            f.write(f"  Successful: {successful_scrapes}\n")
            f.write(f"  Failed: {failed_scrapes}\n")
            f.write(f"  Success rate: {(successful_scrapes/len(df)*100):.1f}%\n")

        # Price statistics
        if 'price' in df.columns and df['price'].notna().any():
            price_data = df['price'].dropna()
            f.write(f"\nPrice statistics:\n")
            f.write(f"  Count (with price): {len(price_data)}\n")
            f.write(f"  Average: £{price_data.mean():,.2f} pcm\n")
            f.write(f"  Median:  £{price_data.median():,.2f} pcm\n")
            f.write(f"  Std Dev: £{price_data.std():,.2f}\n")
            f.write(f"  Min:     £{price_data.min():,.2f} pcm\n")
            f.write(f"  Max:     £{price_data.max():,.2f} pcm\n")

        # Property size statistics
        if 'property_size_sqm' in df.columns and df['property_size_sqm'].notna().any():
            size_data = df['property_size_sqm'].dropna()
            f.write(f"\nProperty size statistics (sq m):\n")
            f.write(f"  Count (with size): {len(size_data)}\n")
            f.write(f"  Average: {size_data.mean():.1f} sq m\n")
            f.write(f"  Median:  {size_data.median():.1f} sq m\n")
            f.write(f"  Std Dev: {size_data.std():.1f} sq m\n")
            f.write(f"  Min:     {size_data.min():.1f} sq m\n")
            f.write(f"  Max:     {size_data.max():.1f} sq m\n")
            
            # Quartiles
            f.write(f"\nSize quartiles (sq m):\n")
            f.write(f"  25th percentile: {size_data.quantile(0.25):.1f} sq m\n")
            f.write(f"  50th percentile: {size_data.quantile(0.50):.1f} sq m\n")
            f.write(f"  75th percentile: {size_data.quantile(0.75):.1f} sq m\n")

        if 'property_size_sqft' in df.columns and df['property_size_sqft'].notna().any():
            sqft_data = df['property_size_sqft'].dropna()
            f.write(f"\nProperty size statistics (sq ft):\n")
            f.write(f"  Count (with size): {len(sqft_data)}\n")
            f.write(f"  Average: {sqft_data.mean():.0f} sq ft\n")
            f.write(f"  Median:  {sqft_data.median():.0f} sq ft\n")
            f.write(f"  Std Dev: {sqft_data.std():.0f} sq ft\n")
            f.write(f"  Min:     {sqft_data.min():.0f} sq ft\n")
            f.write(f"  Max:     {sqft_data.max():.0f} sq ft\n")

        f.write("\n" + "=" * 80 + "\n\n")

        # Letting details analysis
        f.write("LETTING DETAILS ANALYSIS\n")
        f.write("-" * 80 + "\n")
        
        # Extract all letting details keys
        letting_keys = set()
        for details in df['letting_details']:
            if isinstance(details, dict):
                letting_keys.update(details.keys())
        
        for key in sorted(letting_keys):
            f.write(f"\n{key.upper()}:\n")
            values = []
            for details in df['letting_details']:
                if isinstance(details, dict) and key in details:
                    values.append(details[key])
            
            if values:
                # Count occurrences
                from collections import Counter
                value_counts = Counter(values)
                f.write(f"  Total entries: {len(values)}\n")
                f.write(f"  Unique values: {len(value_counts)}\n")
                f.write(f"  Most common:\n")
                for value, count in value_counts.most_common(10):
                    f.write(f"    {value}: {count} ({count/len(values)*100:.1f}%)\n")

        f.write("\n" + "=" * 80 + "\n\n")

        # Size analysis by bedrooms
        if 'bedrooms' in df.columns and 'property_size_sqm' in df.columns:
            f.write("PROPERTY SIZE BY BEDROOMS\n")
            f.write("-" * 80 + "\n")
            size_by_bedrooms = df.dropna(subset=['bedrooms', 'property_size_sqm']).groupby('bedrooms')['property_size_sqm'].agg(['count', 'mean', 'median', 'std', 'min', 'max']).round(1)
            size_by_bedrooms.columns = ['Count', 'Avg Size (sq m)', 'Median Size (sq m)', 'Std Dev', 'Min Size (sq m)', 'Max Size (sq m)']
            f.write(size_by_bedrooms.to_string())
            f.write("\n\n" + "=" * 80 + "\n\n")

        # Price per square meter analysis
        if 'price' in df.columns and 'property_size_sqm' in df.columns:
            f.write("PRICE PER SQUARE METER ANALYSIS\n")
            f.write("-" * 80 + "\n")
            price_size_data = df.dropna(subset=['price', 'property_size_sqm'])
            if len(price_size_data) > 0:
                price_size_data = price_size_data.copy()
                price_size_data['price_per_sqm'] = price_size_data['price'] / price_size_data['property_size_sqm']
                
                f.write(f"Properties with both price and size: {len(price_size_data)}\n")
                f.write(f"Average price per sq m: £{price_size_data['price_per_sqm'].mean():.2f}\n")
                f.write(f"Median price per sq m: £{price_size_data['price_per_sqm'].median():.2f}\n")
                f.write(f"Min price per sq m: £{price_size_data['price_per_sqm'].min():.2f}\n")
                f.write(f"Max price per sq m: £{price_size_data['price_per_sqm'].max():.2f}\n")
                
                # By bedrooms
                f.write(f"\nPrice per sq m by bedrooms:\n")
                price_per_sqm_by_bedrooms = price_size_data.groupby('bedrooms')['price_per_sqm'].agg(['count', 'mean', 'median']).round(2)
                price_per_sqm_by_bedrooms.columns = ['Count', 'Avg £/sqm', 'Median £/sqm']
                f.write(price_per_sqm_by_bedrooms.to_string())
                f.write("\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF ENHANCED REPORT\n")
        f.write("=" * 80 + "\n")

    return stats_file


def create_output_folder() -> Path:
    """
    Create a timestamped output folder for this scraping session
    """
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%b-%d_at_%Hh%Mm")
    run_folder = results_dir / f"enhanced_scrape_{timestamp}"
    run_folder.mkdir(exist_ok=True)
    
    # Verify folder was created
    if not run_folder.exists():
        raise Exception(f"Failed to create output folder: {run_folder}")
    
    print(f"✓ Results folder created: {run_folder}")
    return run_folder


def main():
    import sys
    
    # Your search URL - SE8 area with only 5 results (perfect for testing)
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?minBedrooms=2&dontShow=retirement%2Cstudent%2ChouseShare&channel=RENT&index=0&retirement=false&houseFlatShare=false&sortType=6&minPrice=1400&areaSizeUnit=sqft&maxPrice=2000&locationIdentifier=USERDEFINEDAREA%5E%7B%22polylines%22%3A%22_%60qpIztj%5CbfKokuDemLejwCkrz%40czjEcm%5Eicm%40qoe%40sjDo%60s%40%7Cre%40syv%40%7CxeAugT%7Cj_A%7BaPditDpt%5Dl%7BhFr%7E%5Ed%7EvA%7Elp%40fwsAxvUtfQjqz%40r_Np%7BjA_fBr%7BYstWv%7BC%7Duu%40kzVqfxBcf%40ia%40%22%7D&transactionType=LETTING&displayLocationIdentifier=undefined"
    
    # Alternative test URL from test_enhanced_scraper.py (SE8 area with 5 results)
    # Uncomment the line below and comment out the line above to use the test URL
    # url = "https://www.rightmove.co.uk/property-to-rent/find.html?useLocationIdentifier=true&locationIdentifier=OUTCODE%5E2335&rent=To+rent&radius=0.0&_includeLetAgreed=on&maxPrice=1500&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=SE8.html&maxBedrooms=2&dontShow=houseShare%2Cretirement%2Cstudent&minPrice=1400"
    
    # Parse command line arguments for optional limits
    max_pages = None
    max_listings = None
    delay = 0.25
    
    if len(sys.argv) > 1:
        try:
            if '--max-pages' in sys.argv:
                idx = sys.argv.index('--max-pages')
                max_pages = int(sys.argv[idx + 1])
            if '--max-listings' in sys.argv:
                idx = sys.argv.index('--max-listings')
                max_listings = int(sys.argv[idx + 1])
            if '--delay' in sys.argv:
                idx = sys.argv.index('--delay')
                delay = float(sys.argv[idx + 1])
            if '--help' in sys.argv or '-h' in sys.argv:
                print("Enhanced Rightmove Scraper")
                print("Usage: python enhanced_scraper.py [options]")
                print("\nOptions:")
                print("  --max-pages N      Limit to N search result pages (default: all)")
                print("  --max-listings N   Limit to N individual listings (default: all)")
                print("  --delay N          Delay between requests in seconds (default: 2.0)")
                print("  --help, -h         Show this help message")
                print("\nExample:")
                print("  python enhanced_scraper.py --max-pages 3 --max-listings 50")
                return
        except (ValueError, IndexError):
            print("Error: Invalid command line arguments. Use --help for usage information.")
            return

    # Search criteria for documentation
    search_info = {
        "Location": "SE8 (Deptford, London)",
        "Price range": "£1,400 - £1,500 pcm",
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

    # Scrape with enhanced details
    # You can adjust these parameters:
    # - max_pages: Limit number of search result pages (None = all)
    # - max_listings: Limit number of individual listings to scrape (None = all)
    # - delay: Delay between requests in seconds
    
    print("Configuration:")
    print(f"  - Max pages: {max_pages if max_pages else 'All available'}")
    print(f"  - Max listings: {max_listings if max_listings else 'All available'}")
    print(f"  - Delay between requests: {delay} seconds")
    print(f"  - Individual page scraping: Enabled")
    print("=" * 80)
    
    df = scrape_all_pages_with_details(
        url, 
        max_pages=max_pages,  # Use command line argument or None for all
        max_listings=max_listings,  # Use command line argument or None for all
        delay=delay  # Use command line argument or default 2.0
    )

    if df.empty:
        print("\nNo properties were scraped.")
        return

    # Save CSV to output folder
    csv_file = output_folder / "enhanced_properties.csv"
    df.to_csv(csv_file, index=False, quoting=csv.QUOTE_ALL, escapechar='\\')
    
    # Verify CSV was created
    if not csv_file.exists():
        raise Exception(f"Failed to create CSV file: {csv_file}")
    print(f"✓ CSV file created: {csv_file}")

    # Generate enhanced statistics file
    stats_file = generate_enhanced_statistics(df, output_folder, search_info)
    
    # Verify statistics file was created
    if not stats_file.exists():
        raise Exception(f"Failed to create statistics file: {stats_file}")
    print(f"✓ Statistics file created: {stats_file}")

    print(f"\n" + "=" * 80)
    print("FILES SAVED")
    print("=" * 80)
    print(f"CSV file:        {csv_file}")
    print(f"Statistics file: {stats_file}")
    print(f"Output folder:   {output_folder}")
    print("=" * 80)

    # Display sample of enhanced data
    print("\n" + "=" * 80)
    print("SAMPLE ENHANCED DATA")
    print("=" * 80)
    
    for idx, row in df.head(3).iterrows():
        print(f"\n{idx + 1}. {row['address']}")
        print(f"   Price: £{row['price']:,} pcm" if pd.notna(row['price']) else "   Price: N/A")
        print(f"   Size: {row['property_size_sqm']} sq m" if pd.notna(row['property_size_sqm']) else "   Size: N/A")
        print(f"   Scraping success: {row['scraping_success']}")
        if row['letting_details']:
            print(f"   Letting details: {len(row['letting_details'])} fields found")
            for key, value in list(row['letting_details'].items())[:3]:  # Show first 3 details
                print(f"     {key}: {value}")

    print("\n" + "=" * 80)
    print("Enhanced scraping complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
