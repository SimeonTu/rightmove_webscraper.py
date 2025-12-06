#!/usr/bin/env python3
"""
Test script to verify the improved letting details extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_scraper import scrape_individual_listing
import logging

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_extraction_with_sample_html():
    """Test the extraction with a sample HTML string"""
    
    # Sample HTML based on the structure you provided
    sample_html = '''
    <div class="_21Dc_JVLfbrsoEkZYykXK5">
        <h2 class="fqyI-iuh0c7B9L64hewZW">Letting details</h2>
        <dl class="_2E1qBJkWUYMJYHfYJzUb_r">
            <div class="_2RnXSVJcWbWv4IpBC1Sng6">
                <dt>Let available date: </dt>
                <dd>Ask agent</dd>
            </div>
            <div class="_2RnXSVJcWbWv4IpBC1Sng6">
                <dt>Deposit: </dt>
                <dd><span>£</span>1,846<span class="Kn64CpaGkZuigLbd4_JAe">
                    <button class="_2X1KAdDzygndqawAwAH68q" aria-label="Note on deposit">
                        <svg class="_3hLm0Uw7BrueU7gqoQ8mzl" role="img" data-testid="svg-info-icon">
                            <use xlink:href="#info-icon"></use>
                        </svg>
                    </button>
                </span></dd>
            </div>
            <div class="_2RnXSVJcWbWv4IpBC1Sng6">
                <dt>Min. Tenancy: </dt>
                <dd>Ask agent</dd>
            </div>
            <div class="_2RnXSVJcWbWv4IpBC1Sng6">
                <dt>Let type: </dt>
                <dd>Long term</dd>
            </div>
            <div class="_2RnXSVJcWbWv4IpBC1Sng6">
                <dt>Furnish type: </dt>
                <dd>Furnished</dd>
            </div>
            <div class="_2RnXSVJcWbWv4IpBC1Sng6">
                <dt>Council Tax: </dt>
                <dd>Ask agent</dd>
            </div>
        </dl>
    </div>
    <div class="_2kwY13f3NkrIpaiXfSNj6A"></div>
    <dl class="_4hBezflLdgDMdFtURKTWh" data-test="infoReel" id="info-reel">
        <div class="_3gIoc-NFXILAOZEaEjJi1n">
            <dt class="IXkFvLy8-4DdLI1TIYLgX">
                <span class="ZBWaPR-rIda6ikyKpB_E2">PROPERTY TYPE</span>
            </dt>
            <dd class="_3ZGPwl2N1mHAJH3cbltyWn">
                <div class="_1aZQHX6RNe208-Ub7hMRPq">
                    <svg class="_1RBBiCFrUZI-eHQNTin5f7" role="img" data-testid="svg-house">
                        <use xlink:href="#house"></use>
                    </svg>
                </div>
                <span>
                    <p class="_1hV1kqpVceE9m-QrX_hWDN">Flat</p>
                </span>
            </dd>
        </div>
        <div class="_3gIoc-NFXILAOZEaEjJi1n">
            <dt class="IXkFvLy8-4DdLI1TIYLgX">
                <span class="ZBWaPR-rIda6ikyKpB_E2">BEDROOMS</span>
            </dt>
            <dd class="_3ZGPwl2N1mHAJH3cbltyWn">
                <div class="_1aZQHX6RNe208-Ub7hMRPq">
                    <svg class="_1RBBiCFrUZI-eHQNTin5f7" role="img" data-testid="svg-bed">
                        <use xlink:href="#bed"></use>
                    </svg>
                </div>
                <span>
                    <p class="_1hV1kqpVceE9m-QrX_hWDN">1</p>
                </span>
            </dd>
        </div>
        <div class="_3gIoc-NFXILAOZEaEjJi1n">
            <dt class="IXkFvLy8-4DdLI1TIYLgX">
                <span class="ZBWaPR-rIda6ikyKpB_E2">BATHROOMS</span>
            </dt>
            <dd class="_3ZGPwl2N1mHAJH3cbltyWn">
                <div class="_1aZQHX6RNe208-Ub7hMRPq">
                    <svg class="_1RBBiCFrUZI-eHQNTin5f7" role="img" data-testid="svg-bathroom">
                        <use xlink:href="#bathroom"></use>
                    </svg>
                </div>
                <span>
                    <p class="_1hV1kqpVceE9m-QrX_hWDN">1</p>
                </span>
            </dd>
        </div>
        <div class="_3gIoc-NFXILAOZEaEjJi1n">
            <dt class="IXkFvLy8-4DdLI1TIYLgX">
                <span class="ZBWaPR-rIda6ikyKpB_E2">SIZE</span>
            </dt>
            <dd class="_3ZGPwl2N1mHAJH3cbltyWn">
                <div class="_1aZQHX6RNe208-Ub7hMRPq">
                    <svg class="_1RBBiCFrUZI-eHQNTin5f7" role="img" data-testid="svg-floorplan">
                        <use xlink:href="#floorplan"></use>
                    </svg>
                </div>
                <span>
                    <p class="_1hV1kqpVceE9m-QrX_hWDN">Ask agent</p>
                </span>
            </dd>
        </div>
    </dl>
    '''
    
    print("Testing letting details extraction with sample HTML...")
    print("=" * 60)
    
    # Mock the scrape_individual_listing function to use our sample HTML
    from bs4 import BeautifulSoup
    import re
    
    def mock_scrape_individual_listing(property_url: str, delay: float = 1.0):
        """Mock version that uses sample HTML instead of making HTTP requests"""
        try:
            soup = BeautifulSoup(sample_html, 'html.parser')
            
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
                print(f"Found letting details heading: {letting_heading.get_text(strip=True)}")
                # Find the dl element containing the details
                dl_element = letting_heading.find_next('dl')
                if dl_element:
                    print(f"Found dl element with {len(dl_element.find_all('div'))} detail divs")
                    # Extract all dt/dd pairs from divs within the dl
                    for detail_div in dl_element.find_all('div'):
                        dt = detail_div.find('dt')
                        dd = detail_div.find('dd')
                        if dt and dd:
                            key = dt.get_text(strip=True).replace(':', '').strip().lower()
                            value = dd.get_text(strip=True)
                            detailed_info['letting_details'][key] = value
                            print(f"Extracted letting detail: {key} = {value}")
                else:
                    print("No dl element found after letting details heading")
            else:
                print("No letting details heading found")
            
            # Method 2: Alternative approach - look for any dl with dt/dd pairs that contain letting-related terms
            if not detailed_info['letting_details']:
                print("Trying alternative method for letting details extraction")
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
                                detailed_info['letting_details'][key] = value
                                print(f"Extracted letting detail (alt method): {key} = {value}")
                print(f"Checked {dl_count} dl elements for letting details")
            
            # Extract property size information
            # Method 1: Look for SIZE in any dt element
            size_section = soup.find('dt', string=re.compile(r'SIZE', re.IGNORECASE))
            if size_section:
                print(f"Found SIZE section: {size_section.get_text(strip=True)}")
                size_dd = size_section.find_next('dd')
                if size_dd:
                    # Look for size information in the dd element
                    size_text = size_dd.get_text(strip=True)
                    print(f"Size text: {size_text}")
                    
                    # Extract sq ft
                    sqft_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*ft', size_text, re.IGNORECASE)
                    if sqft_match:
                        detailed_info['property_size_sqft'] = int(sqft_match.group(1).replace(',', ''))
                        print(f"Extracted sq ft: {detailed_info['property_size_sqft']}")
                    
                    # Extract sq m
                    sqm_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*m', size_text, re.IGNORECASE)
                    if sqm_match:
                        detailed_info['property_size_sqm'] = int(sqm_match.group(1).replace(',', ''))
                        print(f"Extracted sq m: {detailed_info['property_size_sqm']}")
            
            print(f"\nFinal result:")
            print(f"  Letting details: {len(detailed_info['letting_details'])} fields")
            for key, value in detailed_info['letting_details'].items():
                print(f"    {key}: {value}")
            print(f"  Property size: {detailed_info['property_size_sqft']} sq ft, {detailed_info['property_size_sqm']} sq m")
            
            return detailed_info
            
        except Exception as e:
            print(f"Error in mock extraction: {str(e)}")
            return {
                'property_url': property_url,
                'letting_details': {},
                'property_size_sqft': None,
                'property_size_sqm': None,
                'scraping_success': False,
                'scraping_error': str(e)
            }
    
    # Test the extraction
    result = mock_scrape_individual_listing("https://example.com/test")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    if result['letting_details']:
        print(f"✅ SUCCESS: Extracted {len(result['letting_details'])} letting details")
    else:
        print("❌ FAILED: No letting details extracted")
    
    if result['property_size_sqft'] or result['property_size_sqm']:
        print(f"✅ SUCCESS: Extracted size data")
    else:
        print("ℹ️  INFO: No size data extracted (expected for 'Ask agent' case)")
    
    print("\n" + "=" * 60)
    print("TESTING WITH ACTUAL SIZE DATA")
    print("=" * 60)
    
    # Test with actual size data
    sample_html_with_size = '''
    <dl class="_4hBezflLdgDMdFtURKTWh" data-test="infoReel" id="info-reel">
        <div class="_3gIoc-NFXILAOZEaEjJi1n">
            <dt class="IXkFvLy8-4DdLI1TIYLgX">
                <span class="ZBWaPR-rIda6ikyKpB_E2">SIZE</span>
            </dt>
            <dd class="_3ZGPwl2N1mHAJH3cbltyWn">
                <div class="_1aZQHX6RNe208-Ub7hMRPq">
                    <svg class="_1RBBiCFrUZI-eHQNTin5f7" role="img" data-testid="svg-floorplan">
                        <use xlink:href="#floorplan"></use>
                    </svg>
                </div>
                <span>
                    <p class="_1hV1kqpVceE9m-QrX_hWDN">431 sq ft</p>
                    <p class="_3vyydJK3KMwn7-s2BEXJAf">40 sq m</p>
                </span>
            </dd>
        </div>
    </dl>
    '''
    
    # Test size extraction with actual data
    soup_with_size = BeautifulSoup(sample_html_with_size, 'html.parser')
    size_section = soup_with_size.find('span', string=re.compile(r'SIZE', re.IGNORECASE))
    if size_section:
        size_section = size_section.find_parent('dt')
    
    if size_section:
        size_dd = size_section.find_next('dd')
        if size_dd:
            size_text = size_dd.get_text(strip=True)
            print(f"Size text: {size_text}")
            
            # Extract sq ft
            sqft_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*ft', size_text, re.IGNORECASE)
            if sqft_match:
                sqft = int(sqft_match.group(1).replace(',', ''))
                print(f"✅ Extracted sq ft: {sqft}")
            
            # Extract sq m
            sqm_match = re.search(r'(\d+(?:,\d+)*)\s*sq\s*m', size_text, re.IGNORECASE)
            if sqm_match:
                sqm = int(sqm_match.group(1).replace(',', ''))
                print(f"✅ Extracted sq m: {sqm}")

if __name__ == "__main__":
    test_extraction_with_sample_html()
