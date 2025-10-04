#!/usr/bin/env python3
"""
Fetch ZIP code coordinates and store them for use in the web app.
This script gets real lat/lon coordinates for each ZIP code and saves them to a JSON file.
"""

import json
import requests
import time
import os
from typing import Dict, Tuple

def get_zip_coordinates(zip_code: str) -> Tuple[float, float]:
    """
    Get coordinates for a ZIP code using a geocoding service.
    Using a free service for demonstration - in production you'd want a more reliable service.
    """
    try:
        # Using a free geocoding service (you might want to use Google Maps API, etc.)
        url = f"https://api.zippopotam.us/us/{zip_code}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'places' in data and len(data['places']) > 0:
                place = data['places'][0]
                return float(place['latitude']), float(place['longitude'])
        
        return None, None
    except Exception as e:
        print(f"Error getting coordinates for {zip_code}: {e}")
        return None, None

def load_zip_codes_from_geojson() -> list:
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
        print(f"Error loading ZIP codes: {e}")
        return []

def main():
    print("🗺️ Fetching ZIP code coordinates...")
    
    # Load existing ZIP codes
    zip_codes = load_zip_codes_from_geojson()
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
    
    # Process ZIP codes
    coordinates = existing_coords.copy()
    processed = 0
    new_coords = 0
    
    for i, zip_code in enumerate(zip_codes):
        if zip_code in coordinates:
            processed += 1
            continue
            
        print(f"📍 Processing {zip_code} ({i+1}/{len(zip_codes)})")
        
        lat, lon = get_zip_coordinates(zip_code)
        if lat is not None and lon is not None:
            coordinates[zip_code] = {'lat': lat, 'lon': lon}
            new_coords += 1
            print(f"✅ {zip_code}: {lat}, {lon}")
        else:
            print(f"❌ {zip_code}: No coordinates found")
        
        # Rate limiting - be nice to the API
        time.sleep(0.1)
        
        # Save progress every 100 coordinates
        if (i + 1) % 100 == 0:
            with open(coords_file, 'w') as f:
                json.dump(coordinates, f, indent=2)
            print(f"💾 Saved progress: {len(coordinates)} coordinates")
    
    # Save final results
    with open(coords_file, 'w') as f:
        json.dump(coordinates, f, indent=2)
    
    print(f"✅ Complete! Processed {processed} existing, added {new_coords} new coordinates")
    print(f"📁 Saved to {coords_file}")
    print(f"📊 Total coordinates: {len(coordinates)}")

if __name__ == "__main__":
    main()
