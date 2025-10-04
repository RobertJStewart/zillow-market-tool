#!/usr/bin/env python3
"""
Create a focused test dataset for the multi-level geographic system.
- 1 Region
- 2 State Regions  
- 3 States
- 5 ZIP codes per state (15 total)
"""

import json
import os
import random
from typing import Dict, List

# Test data structure
TEST_STRUCTURE = {
    'region': 'Northeast',
    'state_regions': [
        'New England',
        'Mid-Atlantic'
    ],
    'states': {
        'New England': ['23', '25', '33'],  # ME, MA, NH
        'Mid-Atlantic': ['34', '36', '42']   # NJ, NY, PA
    },
    'zip_codes_per_state': 5
}

# Sample ZIP codes for each state (real ZIP codes)
STATE_ZIP_CODES = {
    '23': ['04001', '04002', '04003', '04004', '04005'],  # Maine
    '25': ['01001', '01002', '01003', '01004', '01005'],  # Massachusetts  
    '33': ['03001', '03002', '03003', '03004', '03005'],  # New Hampshire
    '34': ['07001', '07002', '07003', '07004', '07005'],  # New Jersey
    '36': ['10001', '10002', '10003', '10004', '10005'],  # New York
    '42': ['15001', '15002', '15003', '15004', '15005']   # Pennsylvania
}

# Sample coordinates for each state (realistic lat/lon)
STATE_COORDINATES = {
    '23': (44.0, -69.0),   # Maine
    '25': (42.0, -71.0),   # Massachusetts
    '33': (43.0, -71.0),   # New Hampshire
    '34': (40.0, -74.0),   # New Jersey
    '36': (41.0, -74.0),   # New York
    '42': (40.0, -77.0)    # Pennsylvania
}

def generate_test_geojson():
    """Generate a test GeoJSON with the specified structure."""
    features = []
    
    # Generate ZIP code features
    for state_code, zip_codes in STATE_ZIP_CODES.items():
        state_lat, state_lon = STATE_COORDINATES[state_code]
        
        for i, zip_code in enumerate(zip_codes):
            # Add some variation to coordinates within the state
            lat = state_lat + random.uniform(-0.5, 0.5)
            lon = state_lon + random.uniform(-0.5, 0.5)
            
            # Generate realistic ZHVI and ZORI values
            base_zhvi = random.uniform(200000, 800000)
            base_zori = random.uniform(1500, 4000)
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lon, lat]
                },
                'properties': {
                    'zcta': zip_code,
                    'zhvi': round(base_zhvi),
                    'zori': round(base_zori),
                    'date': '2024-06',
                    'state_code': state_code
                }
            }
            features.append(feature)
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    return geojson

def create_zip_coordinates():
    """Create coordinates file for the test ZIP codes."""
    coordinates = {}
    
    for state_code, zip_codes in STATE_ZIP_CODES.items():
        state_lat, state_lon = STATE_COORDINATES[state_code]
        
        for i, zip_code in enumerate(zip_codes):
            # Add variation within state
            lat = state_lat + random.uniform(-0.5, 0.5)
            lon = state_lon + random.uniform(-0.5, 0.5)
            
            coordinates[zip_code] = {
                'lat': round(lat, 4),
                'lon': round(lon, 4)
            }
    
    return coordinates

def create_aggregated_data():
    """Create aggregated data for different geographic levels."""
    
    # Calculate region-level data
    region_data = {
        'Northeast': {
            'total_zhvi': 0,
            'total_zori': 0,
            'count': 0,
            'coordinates': []
        }
    }
    
    # Calculate state region data
    state_region_data = {
        'New England': {
            'total_zhvi': 0,
            'total_zori': 0,
            'count': 0,
            'coordinates': [],
            'states': ['23', '25', '33']
        },
        'Mid-Atlantic': {
            'total_zhvi': 0,
            'total_zori': 0,
            'count': 0,
            'coordinates': [],
            'states': ['34', '36', '42']
        }
    }
    
    # Calculate state data
    state_data = {}
    
    # Load the test GeoJSON
    with open('data_demo/zip_latest.geojson', 'r') as f:
        geojson_data = json.load(f)
    
    # Process each feature
    for feature in geojson_data['features']:
        props = feature['properties']
        state_code = props['state_code']
        zhvi = props['zhvi']
        zori = props['zori']
        coords = feature['geometry']['coordinates']
        
        # Update region data
        region_data['Northeast']['total_zhvi'] += zhvi
        region_data['Northeast']['total_zori'] += zori
        region_data['Northeast']['count'] += 1
        region_data['Northeast']['coordinates'].append((coords[1], coords[0]))
        
        # Update state region data
        if state_code in ['23', '25', '33']:
            state_region = 'New England'
        else:
            state_region = 'Mid-Atlantic'
            
        state_region_data[state_region]['total_zhvi'] += zhvi
        state_region_data[state_region]['total_zori'] += zori
        state_region_data[state_region]['count'] += 1
        state_region_data[state_region]['coordinates'].append((coords[1], coords[0]))
        
        # Update state data
        if state_code not in state_data:
            state_data[state_code] = {
                'total_zhvi': 0,
                'total_zori': 0,
                'count': 0,
                'coordinates': []
            }
        
        state_data[state_code]['total_zhvi'] += zhvi
        state_data[state_code]['total_zori'] += zori
        state_data[state_code]['count'] += 1
        state_data[state_code]['coordinates'].append((coords[1], coords[0]))
    
    return region_data, state_region_data, state_data

def create_geojson_features(aggregated_data, level_name):
    """Create GeoJSON features from aggregated data."""
    features = []
    
    for key, data in aggregated_data.items():
        if not data['coordinates']:
            continue
            
        # Calculate center coordinates
        avg_lat = sum(coord[0] for coord in data['coordinates']) / len(data['coordinates'])
        avg_lon = sum(coord[1] for coord in data['coordinates']) / len(data['coordinates'])
        
        # Calculate statistics
        avg_zhvi = data['total_zhvi'] / data['count'] if data['count'] > 0 else 0
        avg_zori = data['total_zori'] / data['count'] if data['count'] > 0 else 0
        
        # Create polygon bounds
        lat_range = max(coord[0] for coord in data['coordinates']) - min(coord[0] for coord in data['coordinates'])
        lon_range = max(coord[1] for coord in data['coordinates']) - min(coord[1] for coord in data['coordinates'])
        
        # Create reasonable polygon size
        lat_padding = max(0.2, lat_range * 0.2)
        lon_padding = max(0.2, lon_range * 0.2)
        
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [[
                    [avg_lon - lon_padding, avg_lat - lat_padding],
                    [avg_lon + lon_padding, avg_lat - lat_padding],
                    [avg_lon + lon_padding, avg_lat + lat_padding],
                    [avg_lon - lon_padding, avg_lat + lat_padding],
                    [avg_lon - lon_padding, avg_lat - lat_padding]
                ]]
            },
            'properties': {
                'id': key,
                'level': level_name,
                'count': data['count'],
                'avg_zhvi': round(avg_zhvi),
                'avg_zori': round(avg_zori),
                'median_zhvi': round(avg_zhvi * 0.95),
                'median_zori': round(avg_zori * 0.95),
                'max_zhvi': round(avg_zhvi * 1.2),
                'max_zori': round(avg_zori * 1.2),
                'min_zhvi': round(avg_zhvi * 0.8),
                'min_zori': round(avg_zori * 0.8),
                'timeValues': {
                    '2024-01': { 'zhvi': round(avg_zhvi * 0.95), 'zori': round(avg_zori * 0.95) },
                    '2024-02': { 'zhvi': round(avg_zhvi * 0.97), 'zori': round(avg_zori * 0.97) },
                    '2024-03': { 'zhvi': round(avg_zhvi * 0.99), 'zori': round(avg_zori * 0.99) },
                    '2024-04': { 'zhvi': round(avg_zhvi * 1.01), 'zori': round(avg_zori * 1.01) },
                    '2024-05': { 'zhvi': round(avg_zhvi * 1.03), 'zori': round(avg_zori * 1.03) },
                    '2024-06': { 'zhvi': round(avg_zhvi), 'zori': round(avg_zori) }
                }
            }
        }
        
        if level_name == 'state_region' and 'states' in data:
            feature['properties']['states'] = data['states']
            
        features.append(feature)
    
    return features

def main():
    print("🧪 Creating focused test dataset...")
    print("📊 Structure: 1 Region → 2 State Regions → 3 States → 15 ZIP codes")
    
    # Create data directory
    os.makedirs('data_demo/aggregated', exist_ok=True)
    
    # 1. Create test ZIP code GeoJSON
    print("📍 Step 1: Creating test ZIP code data...")
    test_geojson = generate_test_geojson()
    
    with open('data_demo/zip_latest.geojson', 'w') as f:
        json.dump(test_geojson, f, indent=2)
    
    print(f"✅ Created {len(test_geojson['features'])} ZIP code features")
    
    # 2. Create coordinates file
    print("📍 Step 2: Creating coordinates file...")
    coordinates = create_zip_coordinates()
    
    with open('data_demo/zip_coordinates.json', 'w') as f:
        json.dump(coordinates, f, indent=2)
    
    print(f"✅ Created coordinates for {len(coordinates)} ZIP codes")
    
    # 3. Create aggregated data
    print("📍 Step 3: Creating aggregated data...")
    region_data, state_region_data, state_data = create_aggregated_data()
    
    # 4. Generate region-level GeoJSON
    print("🗺️ Creating region-level aggregation...")
    region_features = create_geojson_features(region_data, 'region')
    
    region_geojson = {
        'type': 'FeatureCollection',
        'features': region_features
    }
    
    with open('data_demo/aggregated/regions.geojson', 'w') as f:
        json.dump(region_geojson, f, indent=2)
    
    print(f"✅ Created {len(region_features)} region features")
    
    # 5. Generate state region-level GeoJSON
    print("🗺️ Creating state region-level aggregation...")
    state_region_features = create_geojson_features(state_region_data, 'state_region')
    
    state_region_geojson = {
        'type': 'FeatureCollection',
        'features': state_region_features
    }
    
    with open('data_demo/aggregated/state_regions.geojson', 'w') as f:
        json.dump(state_region_geojson, f, indent=2)
    
    print(f"✅ Created {len(state_region_features)} state region features")
    
    # 6. Generate state-level GeoJSON
    print("🗺️ Creating state-level aggregation...")
    state_features = create_geojson_features(state_data, 'state')
    
    state_geojson = {
        'type': 'FeatureCollection',
        'features': state_features
    }
    
    with open('data_demo/aggregated/states.geojson', 'w') as f:
        json.dump(state_geojson, f, indent=2)
    
    print(f"✅ Created {len(state_features)} state features")
    
    # 7. Create configuration file
    config = {
        'geographic_levels': {
            'region': { 'zoom_threshold': 4, 'file': 'data_demo/aggregated/regions.geojson' },
            'state_region': { 'zoom_threshold': 6, 'file': 'data_demo/aggregated/state_regions.geojson' },
            'state': { 'zoom_threshold': 8, 'file': 'data_demo/aggregated/states.geojson' },
            'zipcode': { 'zoom_threshold': 10, 'file': 'data_demo/zip_latest.geojson' }
        },
        'statistical_methods': ['average', 'median', 'max', 'min', 'count'],
        'data_files': {
            'regions': 'data_demo/aggregated/regions.geojson',
            'state_regions': 'data_demo/aggregated/state_regions.geojson',
            'states': 'data_demo/aggregated/states.geojson',
            'zipcodes': 'data_demo/zip_latest.geojson'
        }
    }
    
    with open('data_demo/aggregated/config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Test dataset creation complete!")
    print("📁 Files created:")
    print("  - data_demo/zip_latest.geojson (15 ZIP codes)")
    print("  - data_demo/zip_coordinates.json (15 coordinates)")
    print("  - data_demo/aggregated/regions.geojson (1 region)")
    print("  - data_demo/aggregated/state_regions.geojson (2 state regions)")
    print("  - data_demo/aggregated/states.geojson (6 states)")
    print("  - data_demo/aggregated/config.json (configuration)")
    print("")
    print("🌐 Open index.html in your browser to test the system!")

if __name__ == "__main__":
    main()
