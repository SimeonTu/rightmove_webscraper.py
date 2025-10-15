# rightmove-webscraper

[![Downloads](https://pepy.tech/badge/rightmove-webscraper)](https://pepy.tech/project/rightmove-webscraper)

A modern Python web scraper for [rightmove.co.uk](http://www.rightmove.co.uk/), one of the UK's largest property listings websites. This scraper extracts property data and prepares it in organized CSV files with comprehensive statistical analysis.

> **⚠️ Important Note**: This is a modernized version that works with Rightmove's current website (2025). The original package (`rightmove_webscraper` v1.1) is no longer functional due to Rightmove's website redesign.

---

## 🚀 Quick Start

### 1. Setup

```bash
# Clone the repository
git clone <repository-url>
cd rightmove_webscraper.py

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get Your Search URL

1. Go to [rightmove.co.uk](https://www.rightmove.co.uk)
2. Search for properties with your desired filters:
   - Location, price range, bedrooms, property type, etc.
3. Copy the URL from your browser's address bar

### 3. Run the Scraper

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run the main scraper (scrapes all pages)
python multi_page_scraper.py
```

**Output**: Creates a timestamped folder like `results/scrape_2025-Oct-15_at_13h45m/` containing:
- `properties.csv` - All property data (18 columns)
- `statistics.txt` - Comprehensive analysis report

---

## 📊 What Gets Scraped?

The scraper automatically collects all available pages from your search URL (up to Rightmove's 42-page limit).

### Property Data Fields (18 columns)

| Field | Description |
|-------|-------------|
| `id` | Unique property ID |
| `price` | Monthly rent or sale price (numeric) |
| `price_display` | Formatted price string |
| `frequency` | Payment frequency (monthly, etc.) |
| `property_type` | Studio, Flat, Apartment, House, etc. |
| `bedrooms` | Number of bedrooms |
| `bathrooms` | Number of bathrooms |
| `address` | Display address |
| `summary` | Property description |
| `property_url` | Direct link to listing |
| `contact_url` | Agent contact form URL |
| `branch` | Estate agent name |
| `branch_id` | Agent branch ID |
| `added_or_reduced` | "Added today", "Reduced yesterday", etc. |
| `first_visible_date` | When listing first appeared |
| `let_type` | Rental type information |
| `postcode` | Extracted postcode area (e.g., SE18) |
| `search_date` | Timestamp of scrape |

### Statistics Report Includes

- **Price analysis**: Mean, median, std dev, quartiles
- **All postcodes**: Complete breakdown (not limited to top 10)
- **All estate agents**: Full list with property counts
- **Property types**: Breakdown by type
- **Bedroom/bathroom counts**: Detailed summaries
- **Listing status**: Added/reduced analysis
- **Search criteria**: Documented for reference

---

## 📁 Available Scripts

### Production Scripts

#### `multi_page_scraper.py` ⭐ **Recommended**
Scrapes **all pages** from your search automatically.

**Features:**
- Automatic pagination (up to 42 pages / ~1,000 properties)
- Progress tracking with ✓ symbols
- Duplicate removal
- Rate limiting (1.5s delay between requests)
- Organized output in timestamped folders
- Comprehensive statistics with no limits

**Usage:**
```bash
python multi_page_scraper.py
```

#### `modern_scraper.py`
Quick test scraper for the **first page only** (25 properties).

**Usage:**
```bash
python modern_scraper.py
```

### Testing & Debug Scripts

#### `test_new_output.py`
Tests the output folder structure by scraping 2 pages.

#### `debug_page.py`
Debugs HTML structure and XPath selectors.

#### `check_json_data.py`
Inspects embedded JSON data structure.

---

## 🔧 Customizing Your Search

### Method 1: Edit the Script

Open `multi_page_scraper.py` and modify line 401:

```python
url = "YOUR_RIGHTMOVE_SEARCH_URL_HERE"
```

Update the `search_info` dictionary (lines 404-410) to document your criteria:

```python
search_info = {
    "Location": "Your Location",
    "Price range": "£X - £Y pcm",
    "Max bedrooms": "N",
    # ... etc
}
```

### Method 2: Use as a Module

```python
from multi_page_scraper import scrape_all_pages, generate_full_statistics, create_output_folder

# Your search URL
url = "https://www.rightmove.co.uk/property-to-rent/..."

# Create output folder
output_folder = create_output_folder()

# Scrape all pages
df = scrape_all_pages(url, delay=1.5)

# Or limit to first 5 pages for testing
df = scrape_all_pages(url, max_pages=5, delay=1.0)

# Save results
df.to_csv(output_folder / "properties.csv", index=False)

# Generate statistics
search_info = {"Location": "London", "Price range": "£500-£1500"}
generate_full_statistics(df, output_folder, search_info)
```

---

## 📈 Example Analysis

### Load and Filter Data

```python
import pandas as pd

# Load scraped data
df = pd.read_csv('results/scrape_2025-Oct-15_at_13h45m/properties.csv')

# Filter out parking spaces
df = df[df['property_type'] != 'Parking']

# Find 1-bedroom properties in SE18
se18_1bed = df[(df['postcode'] == 'SE18') & (df['bedrooms'] == 1)]
print(se18_1bed[['address', 'price', 'property_url']].head())

# Compare average prices by area
price_by_area = df.groupby('postcode')['price'].agg(['mean', 'count'])
print(price_by_area.sort_values('mean'))

# Find recently added properties
recent = df[df['added_or_reduced'].str.contains('Added today', na=False)]
print(f"Added today: {len(recent)} properties")
```

---

## ⚙️ Configuration Options

### Adjust Scraping Speed

```python
# Faster (use cautiously - may get rate limited)
df = scrape_all_pages(url, delay=0.5)

# Slower (more polite to the server)
df = scrape_all_pages(url, delay=3.0)
```

### Limit Pages for Testing

```python
# Scrape only first 3 pages (72 properties)
df = scrape_all_pages(url, max_pages=3)
```

---

## 📋 Output Structure

Each scrape creates a new timestamped folder:

```
results/
├── scrape_2025-Oct-15_at_13h45m/
│   ├── properties.csv          # All property data
│   └── statistics.txt          # Comprehensive analysis
├── scrape_2025-Oct-15_at_16h22m/
│   ├── properties.csv
│   └── statistics.txt
└── ...
```

This organization allows you to:
- Track searches over time
- Compare market changes
- Keep historical data organized

---

## 🔍 What Changed from Original?

| Feature | Original (v1.1) | Modern Version |
|---------|----------------|----------------|
| **Website Compatibility** | ❌ Broken (XPath) | ✅ Works (JSON extraction) |
| **Data Fields** | 9 basic fields | 18 extended fields |
| **Output Organization** | Flat files | Timestamped folders |
| **Statistics** | Top 10-15 only | Unlimited (all data) |
| **Progress Tracking** | None | Real-time ✓ symbols |
| **Rate Limiting** | None | Configurable delays |
| **Error Handling** | Basic | Comprehensive |

**See [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) for detailed technical changes.**

---

## 🚨 Troubleshooting

### "ModuleNotFoundError"
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

### "Status code: 403" or Rate Limiting
```python
# Increase delay between requests
df = scrape_all_pages(url, delay=3.0)

# Or wait a few minutes and try again
```

### "No properties found"
- Verify the URL works in your browser
- Check your search isn't too restrictive
- Ensure the URL includes search parameters

### "Could not find property data"
The page structure may have changed. The scraper extracts data from Next.js JSON. If Rightmove updates their site, the scraper may need updating.

---

## 📚 Documentation

- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - Comprehensive usage guide with advanced examples
- **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)** - Detailed changelog and technical details
- **[FILES_RESTORED_COMPLETE.md](FILES_RESTORED_COMPLETE.md)** - Quick reference of all files

---

## ⚖️ Legal Notice

**Important**: According to Rightmove's [terms and conditions](https://www.rightmove.co.uk/this-site/terms-of-use.html), the use of web scrapers is unauthorized.

This tool is provided for:
- **Educational purposes only**
- **Personal research and analysis**
- **Non-commercial use**

**Use at your own risk.** Be respectful:
- Use reasonable delays between requests (default 1.5s)
- Don't overload their servers
- Respect their terms of service

---

## 🛠️ Technical Details

### Requirements
- Python 3.6+
- Dependencies: lxml, numpy, pandas, requests

### How It Works
1. Fetches Rightmove search results page
2. Extracts embedded JSON from Next.js `__NEXT_DATA__` tag
3. Parses property data from JSON structure
4. Iterates through all result pages automatically
5. Removes duplicates and validates data
6. Exports to organized CSV and statistics files

### Architecture
```
URL → HTTP Request → HTML Response → JSON Extraction →
DataFrame Processing → Duplicate Removal →
CSV Export + Statistics Generation → Timestamped Folder
```

---

## 🤝 Contributing

Found a bug or want to add a feature? Contributions welcome!

1. Check if the issue is with Rightmove's site structure changing
2. Update the JSON extraction logic in `scrape_rightmove_page()` if needed
3. Test with multiple searches to ensure compatibility
4. Update documentation accordingly

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🙏 Credits

- Original project by [Toby Petty](https://github.com/toby-p)
- Modernized for 2025 Rightmove website
- Updated with comprehensive statistics and organized output

---

**Happy property hunting! 🏠**
