#!/usr/bin/env python3
"""Check if there's JSON data embedded in the page"""

import requests
import json
import re

url = "https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=South+East+London&useLocationIdentifier=true&locationIdentifier=REGION%5E92828&rent=To+rent&radius=0.0&_includeLetAgreed=on&maxPrice=1500&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=South-East-London.html&maxBedrooms=2&dontShow=houseShare%2Cretirement%2Cstudent&minPrice=600"

print("Fetching page...")
r = requests.get(url)
print(f"Status code: {r.status_code}\n")

if r.status_code == 200:
    # Look for JSON data in script tags
    print("Searching for JSON data in the page...")

    # Common patterns for Next.js data
    patterns = [
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        r'window\.__NEXT_DATA__\s*=\s*({.*?});',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, r.text, re.DOTALL)
        if matches:
            print(f"Found data with pattern: {pattern[:50]}...")
            try:
                data = json.loads(matches[0])
                print(f"\nJSON structure keys: {list(data.keys())}")

                # Save to file for inspection
                with open("page_data.json", "w") as f:
                    json.dump(data, f, indent=2)
                print("\nFull JSON saved to page_data.json")

                # Try to find property data
                def find_properties(obj, path=""):
                    """Recursively search for property listings"""
                    if isinstance(obj, dict):
                        if 'properties' in obj or 'propertyData' in obj:
                            print(f"\nFound potential property data at: {path}")
                            print(f"Keys: {obj.keys()}")
                        for key, value in obj.items():
                            find_properties(value, f"{path}.{key}" if path else key)
                    elif isinstance(obj, list) and len(obj) > 0:
                        find_properties(obj[0], f"{path}[0]")

                find_properties(data)
                break

            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
    else:
        print("No JSON data found in expected locations")
        print("\nLet's check the content length and type:")
        print(f"Content length: {len(r.text)}")
        print(f"Content type: {r.headers.get('content-type')}")
