# Enhanced Rightmove Scraper Guide

## Overview

The Enhanced Rightmove Scraper is a new feature that extends the existing multi-page scraper to also visit individual property listing pages and extract detailed letting information and property size data. This provides much more comprehensive data than the standard search results scraping.

## Key Features

### 1. Individual Listing Page Scraping
- Visits each property's individual listing page
- Extracts detailed letting information (deposit, tenancy length, let type, furnish type, council tax)
- Extracts property size in both square feet and square meters
- Handles scraping errors gracefully with detailed error reporting

### 2. Enhanced Statistics
- Comprehensive statistics for property sizes
- Analysis of letting details (deposit amounts, tenancy lengths, etc.)
- Price per square meter calculations
- Success/failure rates for individual page scraping

### 3. Flexible Configuration
- Control number of search result pages to scrape
- Limit number of individual listings to process
- Configurable delays between requests
- Detailed progress reporting

## Files

- `enhanced_scraper.py` - Main enhanced scraper script
- `test_enhanced_scraper.py` - Test script to verify functionality
- `requirements.txt` - Updated with BeautifulSoup dependency

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from enhanced_scraper import scrape_all_pages_with_details

# Scrape with default settings
df = scrape_all_pages_with_details("https://www.rightmove.co.uk/property-to-rent/find.html?...")
```

### Advanced Usage

```python
# Scrape with custom parameters
df = scrape_all_pages_with_details(
    base_url="https://www.rightmove.co.uk/property-to-rent/find.html?...",
    max_pages=3,        # Limit to first 3 search result pages
    max_listings=50,    # Limit to first 50 individual listings
    delay=2.0          # 2 second delay between requests
)
```

### Running the Full Script

```bash
# Scrape all available pages and listings (default)
python enhanced_scraper.py

# Scrape with custom limits
python enhanced_scraper.py --max-pages 5 --max-listings 100

# Scrape with custom delay
python enhanced_scraper.py --delay 3.0

# Show help
python enhanced_scraper.py --help
```

### Command Line Options

The enhanced scraper supports several command line options for customization:

- `--max-pages N` - Limit to N search result pages (default: all available)
- `--max-listings N` - Limit to N individual listings (default: all available)  
- `--delay N` - Delay between requests in seconds (default: 2.0)
- `--help, -h` - Show help message and usage information

**Examples:**
```bash
# Quick test with limited data
python enhanced_scraper.py --max-pages 2 --max-listings 20

# Slower scraping to avoid rate limiting
python enhanced_scraper.py --delay 5.0

# Full scraping (default behavior)
python enhanced_scraper.py
```

## Data Structure

The enhanced scraper returns a DataFrame with all the standard search result columns plus:

### New Columns

- `letting_details` - Dictionary containing detailed letting information
- `property_size_sqft` - Property size in square feet
- `property_size_sqm` - Property size in square meters
- `scraping_success` - Boolean indicating if individual page scraping succeeded
- `scraping_error` - Error message if individual page scraping failed

### Letting Details Fields

The `letting_details` dictionary may contain:
- `let available date` - When the property becomes available
- `deposit` - Required deposit amount
- `min. tenancy` - Minimum tenancy length
- `let type` - Type of let (e.g., "Long term")
- `furnish type` - Furnishing status (e.g., "Unfurnished")
- `council tax` - Council tax information

## Statistics Generated

The enhanced scraper generates comprehensive statistics including:

### Property Size Statistics
- Average, median, min, max property sizes
- Size distribution by number of bedrooms
- Price per square meter analysis

### Letting Details Analysis
- Frequency analysis of all letting detail fields
- Most common deposit amounts, tenancy lengths, etc.
- Success rates for data extraction

### Scraping Performance
- Success/failure rates for individual page scraping
- Error analysis and reporting

## Example Output

```
ENHANCED RIGHTMOVE SCRAPER - DETAILED STATISTICS REPORT
================================================================================
Generated: 2025-01-15 14:30:00
================================================================================

OVERALL STATISTICS
--------------------------------------------------------------------------------
Total properties: 25
Individual listing scrapes:
  Successful: 23
  Failed: 2
  Success rate: 92.0%

Property size statistics (sq m):
  Count (with size): 23
  Average: 45.2 sq m
  Median: 42.0 sq m
  Std Dev: 12.1 sq m
  Min: 28.0 sq m
  Max: 78.0 sq m

LETTING DETAILS ANALYSIS
--------------------------------------------------------------------------------
deposit:
  Total entries: 23
  Unique values: 8
  Most common:
    £1,200: 5 (21.7%)
    £1,500: 4 (17.4%)
    £1,000: 3 (13.0%)

min. tenancy:
  Total entries: 23
  Unique values: 2
  Most common:
    12 months: 20 (87.0%)
    6 months: 3 (13.0%)
```

## Configuration Options

### Parameters

- `max_pages` - Maximum number of search result pages to scrape (None = all)
- `max_listings` - Maximum number of individual listings to scrape (None = all)
- `delay` - Delay in seconds between requests (recommended: 1.0-3.0)

### Recommended Settings

- **Testing**: `max_pages=1, max_listings=5, delay=1.0`
- **Small dataset**: `max_pages=2, max_listings=20, delay=2.0`
- **Full scraping**: `max_pages=None, max_listings=None, delay=2.0`

## Error Handling

The enhanced scraper includes robust error handling:

- Individual page scraping failures don't stop the overall process
- Detailed error logging for debugging
- Success/failure tracking for each property
- Graceful handling of network timeouts and parsing errors

## Performance Considerations

- Individual page scraping is significantly slower than search results only
- Recommended delay of 2+ seconds between requests to avoid rate limiting
- Consider using `max_listings` parameter for large datasets
- Monitor success rates and adjust delay if needed

## Testing

Run the test script to verify functionality:

```bash
python test_enhanced_scraper.py
```

This will test:
1. Individual listing scraping (with a test URL)
2. Search results scraping
3. Enhanced scraping with a small sample

## Troubleshooting

### Common Issues

1. **Low success rate**: Increase delay between requests
2. **Parsing errors**: Rightmove may have changed their HTML structure
3. **Network timeouts**: Check internet connection and increase delay
4. **Memory issues**: Use `max_listings` to limit dataset size

### Debugging

- Check the generated statistics file for detailed error information
- Use the test script to verify individual components
- Monitor the console output for real-time progress and errors

## Comparison with Standard Scraper

| Feature | Standard Scraper | Enhanced Scraper |
|---------|------------------|------------------|
| Search results | ✅ | ✅ |
| Individual pages | ❌ | ✅ |
| Letting details | ❌ | ✅ |
| Property size | ❌ | ✅ |
| Speed | Fast | Slower |
| Data completeness | Basic | Comprehensive |
| Rate limiting risk | Low | Higher |

## Future Enhancements

Potential improvements for future versions:
- Parallel processing for individual page scraping
- Caching of individual page data
- Additional property details extraction
- Integration with property image analysis
- Automated retry logic for failed scrapes
