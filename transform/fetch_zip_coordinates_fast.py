#!/usr/bin/env python3
"""
Fast ZIP code coordinate fetching using a pre-built database approach.
This is much faster than API calls and doesn't require rate limiting.
"""

import json
import os
import csv
import requests
from typing import Dict, List

def download_zip_database():
    """Download a comprehensive ZIP code database."""
    print("📥 Downloading comprehensive ZIP code database...")
    
    # Use a free ZIP code database from GitHub
    url = "https://raw.githubusercontent.com/kelvins/US-ZipCodes-Database/master/US-ZipCodes.csv"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save the CSV file
        with open('temp_zip_database.csv', 'w') as f:
            f.write(response.text)
        
        print("✅ ZIP code database downloaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading ZIP database: {e}")
        return False

def load_zip_database() -> Dict[str, Dict[str, float]]:
    """Load ZIP code coordinates from the downloaded database."""
    coordinates = {}
    
    try:
        with open('temp_zip_database.csv', 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                zip_code = row['ZipCode'].strip()
                try:
                    lat = float(row['Latitude'])
                    lon = float(row['Longitude'])
                    
                    coordinates[zip_code] = {'lat': lat, 'lon': lon}
                    
                except (ValueError, KeyError):
                    continue
        
        print(f"✅ Loaded {len(coordinates)} ZIP codes from database")
        return coordinates
        
    except Exception as e:
        print(f"❌ Error loading ZIP database: {e}")
        return {}

def load_zip_codes_from_geojson() -> List[str]:
    """Load ZIP codes from the existing GeoJSON file."""
    try:
        with open('data_demo/zip_latest.geojson', 'r') as f:
            data = json.load(f)
        
        zip_codes = []
        for feature in data['features']:
            if 'zcta' in feature['properties']:
                zip_codes.append(str(feature['properties']['zcta']))
        
        return zip_codes
    except Exception as e:
        print(f"❌ Error loading ZIP codes: {e}")
        return []

def main():
    print("🚀 Fast ZIP code coordinate fetching...")
    
    # Load existing ZIP codes
    zip_codes = load_zip_codes_from_geojson()
    if not zip_codes:
        print("❌ No ZIP codes found. Run the pipeline first.")
        return
    
    print(f"📊 Found {len(zip_codes)} ZIP codes to process")
    
    # Check if coordinates file already exists
    coords_file = 'data_demo/zip_coordinates.json'
    existing_coords = {}
    
    if os.path.exists(coords_file):
        try:
            with open(coords_file, 'r') as f:
                existing_coords = json.load(f)
            print(f"📁 Found existing coordinates file with {len(existing_coords)} entries")
        except Exception as e:
            print(f"⚠️ Error loading existing coordinates: {e}")
    
    # Filter out ZIP codes we already have
    missing_zip_codes = [zip_code for zip_code in zip_codes if zip_code not in existing_coords]
    
    if not missing_zip_codes:
        print("✅ All ZIP codes already have coordinates!")
        return
    
    print(f"🚀 Processing {len(missing_zip_codes)} missing ZIP codes...")
    
    # Download and load the ZIP database
    if not download_zip_database():
        print("❌ Failed to download ZIP database")
        return
    
    # Load coordinates from database
    database_coords = load_zip_database()
    
    # Find coordinates for missing ZIP codes
    new_coordinates = {}
    found_count = 0
    
    for zip_code in missing_zip_codes:
        if zip_code in database_coords:
            new_coordinates[zip_code] = database_coords[zip_code]
            found_count += 1
        else:
            print(f"⚠️ {zip_code}: Not found in database")
    
    # Merge with existing coordinates
    coordinates = {**existing_coords, **new_coordinates}
    
    # Save final results
    with open(coords_file, 'w') as f:
        json.dump(coordinates, f, indent=2)
    
    print(f"✅ Complete! Found {found_count} new coordinates")
    print(f"📁 Saved to {coords_file}")
    print(f"📊 Total coordinates: {len(coordinates)}")
    
    # Clean up temporary file
    if os.path.exists('temp_zip_database.csv'):
        os.remove('temp_zip_database.csv')
        print("🧹 Cleaned up temporary files")

if __name__ == "__main__":
    main()
