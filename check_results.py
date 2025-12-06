#!/usr/bin/env python3
"""
Check results folder structure and show generated files
"""

import os
from pathlib import Path
from datetime import datetime


def check_results_folder():
    """Check the results folder structure and show generated files"""
    
    print("=" * 80)
    print("RIGHTMOVE SCRAPER - RESULTS FOLDER CHECK")
    print("=" * 80)
    
    results_dir = Path("results")
    
    if not results_dir.exists():
        print("❌ Results folder does not exist!")
        print("   Run the enhanced scraper first to create results.")
        return
    
    print(f"✓ Results folder exists: {results_dir.absolute()}")
    
    # List all subdirectories (scraping runs)
    subdirs = [d for d in results_dir.iterdir() if d.is_dir()]
    
    if not subdirs:
        print("❌ No scraping runs found in results folder!")
        print("   Run the enhanced scraper first to generate data.")
        return
    
    print(f"\nFound {len(subdirs)} scraping run(s):")
    print("-" * 80)
    
    for i, subdir in enumerate(sorted(subdirs, key=lambda x: x.name), 1):
        print(f"\n{i}. {subdir.name}")
        print(f"   Path: {subdir.absolute()}")
        
        # Check for files in this run
        files = list(subdir.glob("*"))
        if files:
            print(f"   Files ({len(files)}):")
            for file in sorted(files):
                file_size = file.stat().st_size if file.is_file() else 0
                file_type = "📁" if file.is_dir() else "📄"
                print(f"     {file_type} {file.name} ({file_size:,} bytes)")
        else:
            print("   ❌ No files found in this run")
    
    # Show the most recent run details
    if subdirs:
        latest_run = max(subdirs, key=lambda x: x.stat().st_mtime)
        print(f"\n" + "=" * 80)
        print(f"LATEST RUN: {latest_run.name}")
        print("=" * 80)
        
        # Check for expected files
        csv_files = list(latest_run.glob("*.csv"))
        txt_files = list(latest_run.glob("*.txt"))
        
        print(f"CSV files: {len(csv_files)}")
        for csv_file in csv_files:
            size = csv_file.stat().st_size
            print(f"  ✓ {csv_file.name} ({size:,} bytes)")
        
        print(f"\nStatistics files: {len(txt_files)}")
        for txt_file in txt_files:
            size = txt_file.stat().st_size
            print(f"  ✓ {txt_file.name} ({size:,} bytes)")
        
        # Show sample of CSV content if available
        if csv_files:
            try:
                import pandas as pd
                df = pd.read_csv(csv_files[0])
                print(f"\nCSV Content Preview ({csv_files[0].name}):")
                print(f"  Rows: {len(df)}")
                print(f"  Columns: {len(df.columns)}")
                print(f"  Columns: {', '.join(df.columns.tolist())}")
                
                # Show sample data
                if not df.empty:
                    print(f"\n  Sample data (first 2 rows):")
                    for idx, row in df.head(2).iterrows():
                        print(f"    Row {idx + 1}: {row.get('address', 'N/A')} - £{row.get('price', 'N/A')}")
            except Exception as e:
                print(f"  ❌ Error reading CSV: {e}")
        
        # Show sample of statistics if available
        if txt_files:
            try:
                with open(txt_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    print(f"\nStatistics Preview ({txt_files[0].name}):")
                    print(f"  Lines: {len(lines)}")
                    print(f"  Size: {len(content):,} characters")
                    
                    # Show first few lines
                    print(f"\n  First 10 lines:")
                    for i, line in enumerate(lines[:10]):
                        if line.strip():
                            print(f"    {i+1:2d}: {line}")
            except Exception as e:
                print(f"  ❌ Error reading statistics: {e}")
    
    print(f"\n" + "=" * 80)
    print("RESULTS FOLDER CHECK COMPLETE")
    print("=" * 80)


def main():
    """Main function"""
    check_results_folder()


if __name__ == "__main__":
    main()


