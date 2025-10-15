#!/usr/bin/env python3
"""Debug script to check the current page structure"""

import requests
from lxml import html

url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=South+East+London&useLocationIdentifier=true&locationIdentifier=REGION%5E92828&rent=To+rent&radius=0.0&_includeLetAgreed=on&maxPrice=1500&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=South-East-London.html&maxBedrooms=2&dontShow=houseShare%2Cretirement%2Cstudent&minPrice=600"

print("Fetching page...")
r = requests.get(url)
print(f"Status code: {r.status_code}")

if r.status_code == 200:
    tree = html.fromstring(r.content)

    # Try to find result count with various xpaths
    print("\nTrying different xpaths for result count:")

    xpaths = [
        '//span[@class="searchHeader-resultCount"]/text()',
        '//span[contains(@class, "resultCount")]/text()',
        '//*[contains(@class, "searchHeader-title")]/text()',
        '//*[contains(text(), "propert")]/text()',
    ]

    for i, xpath in enumerate(xpaths, 1):
        try:
            result = tree.xpath(xpath)
            print(f"\n{i}. {xpath}")
            print(f"   Result: {result[:5] if result else 'No match'}")
        except Exception as e:
            print(f"\n{i}. {xpath}")
            print(f"   Error: {e}")

    # Save a snippet of the HTML for inspection
    print("\n" + "="*80)
    print("Saving HTML snippet...")
    with open("page_sample.html", "w", encoding="utf-8") as f:
        f.write(r.text[:10000])
    print("First 10000 characters saved to page_sample.html")

else:
    print(f"Failed to fetch page. Status code: {r.status_code}")
