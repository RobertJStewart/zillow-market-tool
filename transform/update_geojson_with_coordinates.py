#!/usr/bin/env python3
"""
Update the GeoJSON file with real ZIP code coordinates.
This script reads the coordinates file and updates the GeoJSON with actual lat/lon values.
"""

import json
import os

def load_coordinates() -> dict:
    """Load the coordinates from the JSON file."""
    coords_file = 'data_demo/zip_coordinates.json'
    
    if not os.path.exists(coords_file):
        print(f"❌ Coordinates file not found: {coords_file}")
        print("Run fetch_zip_coordinates.py first!")
        return {}
    
    try:
        with open(coords_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading coordinates: {e}")
        return {}

def update_geojson_with_coordinates():
    """Update the GeoJSON file with real coordinates."""
    print("🗺️ Updating GeoJSON with real coordinates...")
    
    # Load coordinates
    coordinates = load_coordinates()
    if not coordinates:
        return
    
    print(f"📊 Loaded {len(coordinates)} coordinate pairs")
    
    # Load GeoJSON
    geojson_file = 'data_demo/zip_latest.geojson'
    try:
        with open(geojson_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading GeoJSON: {e}")
        return
    
    # Update features with real coordinates
    updated_count = 0
    missing_count = 0
    
    for feature in data['features']:
        if 'zcta' in feature['properties']:
            zip_code = str(feature['properties']['zcta'])
            
            if zip_code in coordinates:
                coords = coordinates[zip_code]
                # Update geometry to use real coordinates
                feature['geometry'] = {
                    "type": "Point",
                    "coordinates": [coords['lon'], coords['lat']]
                }
                updated_count += 1
            else:
                missing_count += 1
                # Keep placeholder coordinates for missing ZIP codes
                feature['geometry'] = {
                    "type": "Point", 
                    "coordinates": [-98.5795, 39.8283]  # Center of US
                }
    
    # Save updated GeoJSON
    try:
        with open(geojson_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Updated GeoJSON successfully!")
        print(f"📍 Updated {updated_count} features with real coordinates")
        print(f"⚠️ {missing_count} features still using placeholder coordinates")
        print(f"💾 Saved to {geojson_file}")
        
    except Exception as e:
        print(f"❌ Error saving GeoJSON: {e}")

if __name__ == "__main__":
    update_geojson_with_coordinates()
