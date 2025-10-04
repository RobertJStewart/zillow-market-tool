#!/usr/bin/env python3
"""
Simple ZIP code coordinate fetching using a reliable data source.
"""

import json
import os
import requests
from typing import Dict, List

def get_zip_coordinates_simple(zip_code: str) -> tuple:
    """Get coordinates for a single ZIP code using a reliable service."""
    try:
        # Use a more reliable geocoding service
        url = f"https://api.zippopotam.us/us/{zip_code}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'places' in data and len(data['places']) > 0:
                place = data['places'][0]
                return float(place['latitude']), float(place['longitude'])
        
        return None, None
    except Exception as e:
        return None, None

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
    print("🚀 Simple ZIP code coordinate fetching...")
    
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
            existing_coords = {}
    
    # Filter out ZIP codes we already have
    missing_zip_codes = [zip_code for zip_code in zip_codes if zip_code not in existing_coords]
    
    if not missing_zip_codes:
        print("✅ All ZIP codes already have coordinates!")
        return
    
    print(f"🚀 Processing {len(missing_zip_codes)} missing ZIP codes...")
    
    # Process missing ZIP codes
    coordinates = existing_coords.copy()
    processed = 0
    new_coords = 0
    
    for i, zip_code in enumerate(missing_zip_codes):
        print(f"📍 Processing {zip_code} ({i+1}/{len(missing_zip_codes)})")
        
        lat, lon = get_zip_coordinates_simple(zip_code)
        if lat is not None and lon is not None:
            coordinates[zip_code] = {'lat': lat, 'lon': lon}
            new_coords += 1
            print(f"✅ {zip_code}: {lat}, {lon}")
        else:
            print(f"❌ {zip_code}: No coordinates found")
        
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
