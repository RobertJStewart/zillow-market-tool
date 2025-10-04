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

def get_zip_coordinates_batch(zip_codes: List[str]) -> Dict[str, Tuple[float, float]]:
    """
    Get coordinates for multiple ZIP codes in batches for much better performance.
    """
    coordinates = {}
    batch_size = 50  # Process 50 ZIP codes at a time
    
    for i in range(0, len(zip_codes), batch_size):
        batch = zip_codes[i:i + batch_size]
        print(f"📍 Processing batch {i//batch_size + 1}/{(len(zip_codes) + batch_size - 1)//batch_size} ({len(batch)} ZIP codes)")
        
        # Use concurrent requests for much faster processing
        import concurrent.futures
        import threading
        
        def get_single_coordinate(zip_code):
            try:
                url = f"https://api.zippopotam.us/us/{zip_code}"
                response = requests.get(url, timeout=3)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'places' in data and len(data['places']) > 0:
                        place = data['places'][0]
                        return zip_code, (float(place['latitude']), float(place['longitude']))
                
                return zip_code, (None, None)
            except Exception as e:
                return zip_code, (None, None)
        
        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(get_single_coordinate, batch))
            
            for zip_code, coords in results:
                if coords[0] is not None and coords[1] is not None:
                    coordinates[zip_code] = {'lat': coords[0], 'lon': coords[1]}
                    print(f"✅ {zip_code}: {coords[0]}, {coords[1]}")
                else:
                    print(f"❌ {zip_code}: No coordinates found")
        
        # Small delay between batches to be respectful to the API
        time.sleep(0.5)
    
    return coordinates

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
    
    # Filter out ZIP codes we already have
    missing_zip_codes = [zip_code for zip_code in zip_codes if zip_code not in existing_coords]
    
    if not missing_zip_codes:
        print("✅ All ZIP codes already have coordinates!")
        return
    
    print(f"🚀 Processing {len(missing_zip_codes)} missing ZIP codes in batches...")
    
    # Process missing ZIP codes in batches
    new_coordinates = get_zip_coordinates_batch(missing_zip_codes)
    
    # Merge with existing coordinates
    coordinates = {**existing_coords, **new_coordinates}
    
    processed = len(existing_coords)
    new_coords = len(new_coordinates)
    
    # Save final results
    with open(coords_file, 'w') as f:
        json.dump(coordinates, f, indent=2)
    
    print(f"✅ Complete! Processed {processed} existing, added {new_coords} new coordinates")
    print(f"📁 Saved to {coords_file}")
    print(f"📊 Total coordinates: {len(coordinates)}")

if __name__ == "__main__":
    main()
