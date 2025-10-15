# Rightmove Multi-Page Scraper - Usage Guide

## Overview

This project contains modern scrapers for Rightmove that work with their current website (2025). The original package is outdated and doesn't work anymore.

## Setup

```bash
# Activate the virtual environment
source venv/bin/activate
```

## Available Scripts

### 1. Single-Page Scraper (`modern_scraper.py`)
Scrapes only the first page of results (25 properties)

```bash
python modern_scraper.py
```

**Use when:** You want a quick sample or preview of available properties

### 2. Multi-Page Scraper (`multi_page_scraper.py`)
Scrapes ALL pages of results from your search

```bash
python multi_page_scraper.py
```

**Features:**
- Automatically scrapes all available pages
- Progress tracking with visual feedback
- Removes duplicates
- Polite 1.5-second delay between requests
- Comprehensive statistics and analysis
- Exports to organized timestamped folders

**Use when:** You need complete data for analysis or comparison

## Customizing Your Search

### Method 1: Modify the URL in the Script

Open `multi_page_scraper.py` and change the `url` variable around line 401:

```python
url = "YOUR_RIGHTMOVE_SEARCH_URL_HERE"
```

### Method 2: Get a New Search URL from Rightmove

1. Go to [rightmove.co.uk](https://www.rightmove.co.uk)
2. Search for properties with your desired filters:
   - Location
   - Price range
   - Number of bedrooms/bathrooms
   - Property type
   - Rent/Sale
   - etc.
3. Copy the URL from your browser
4. Paste it into the script

### Method 3: Use as a Python Module

```python
from multi_page_scraper import scrape_all_pages, display_summary

# Your custom URL
url = "https://www.rightmove.co.uk/property-to-rent/..."

# Scrape all pages
df = scrape_all_pages(url, delay=1.5)

# Or limit to first 5 pages
df = scrape_all_pages(url, max_pages=5, delay=1.0)

# Display statistics
display_summary(df)

# Save to custom file
df.to_csv("my_properties.csv", index=False)

# Analyze the data
print(df['bedrooms'].value_counts())
print(df.groupby('postcode')['price'].mean())
```

## Output Structure

Each run creates a timestamped folder:

```
results/
└── scrape_2025-Oct-15_at_13h45m/
    ├── properties.csv (all property data)
    └── statistics.txt (comprehensive analysis)
```

## CSV Columns

Each row contains:
- `id` - Unique property ID
- `price` - Monthly rent (numeric)
- `price_display` - Formatted price string
- `frequency` - Payment frequency (monthly)
- `property_type` - Studio, Flat, Apartment, etc.
- `bedrooms` - Number of bedrooms
- `bathrooms` - Number of bathrooms
- `address` - Display address
- `summary` - Property description
- `property_url` - Link to full listing
- `contact_url` - Contact form URL
- `branch` - Estate agent name
- `branch_id` - Agent ID
- `added_or_reduced` - "Added today", "Reduced today", etc.
- `first_visible_date` - When listing first appeared
- `let_type` - Rental type
- `postcode` - Extracted postcode (area only)
- `search_date` - When the scrape was performed

## Statistics File

The `statistics.txt` file includes:
- **All postcodes** (not limited to top 15)
- **All estate agents** (complete list with counts)
- **All property types**
- Price quartiles and standard deviations
- Bedroom/bathroom breakdowns
- Listing status analysis
- Search criteria documentation

## Advanced Configuration

### Adjust Request Delay

```python
# Faster (less polite) - 0.5 seconds
df = scrape_all_pages(url, delay=0.5)

# Slower (more polite) - 3 seconds
df = scrape_all_pages(url, delay=3.0)
```

### Limit Number of Pages

```python
# Scrape only first 3 pages
df = scrape_all_pages(url, max_pages=3)
```

## Important Notes

### Legal & Terms of Service
According to Rightmove's terms, web scraping is unauthorized. Use this tool:
- For personal research/education only
- Responsibly and politely (use delays between requests)
- At your own risk

### Rate Limiting
- The scraper includes delays (default 1.5s)
- Don't reduce delays too much or you may get blocked
- If you get status 400/403 errors, increase the delay

### Data Accuracy
- Some listings may have incomplete data
- Prices marked as "POA" may appear as null
- Parking spaces/storage are included (filter by `property_type`)

## Troubleshooting

### "ModuleNotFoundError"
Make sure you've activated the virtual environment:
```bash
source venv/bin/activate
```

### "Status code: 403" or "Status code: 400"
You may have been rate-limited. Try:
1. Increasing the delay: `delay=3.0`
2. Waiting a few minutes before retrying

### "Could not find property data"
The page structure may have changed or the URL is invalid.
Verify the URL works in your browser first.

## Example Analysis

```python
import pandas as pd

# Load the data
df = pd.read_csv('results/scrape_2025-Oct-15_at_13h45m/properties.csv')

# Filter out parking spaces
df = df[df['property_type'] != 'Parking']

# Find cheapest 1-bedroom flats in SE18
se18_1bed = df[(df['postcode'] == 'SE18') & (df['bedrooms'] == 1)]
se18_1bed = se18_1bed.sort_values('price')
print(se18_1bed[['address', 'price', 'property_url']].head())

# Compare prices by area
price_by_area = df.groupby('postcode')['price'].agg(['mean', 'count'])
print(price_by_area.sort_values('mean'))

# Find recently added properties
recent = df[df['added_or_reduced'].str.contains('Added', na=False)]
print(f"Recently added: {len(recent)} properties")
```

## Questions or Issues?

The scraper works by extracting JSON data embedded in Rightmove's Next.js pages. If Rightmove updates their website structure, the scraper may need updating.
