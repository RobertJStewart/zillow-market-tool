#!/usr/bin/env python3
"""
Create multi-level geographic aggregation system.
This script generates aggregated data at multiple geographic levels with proper boundaries.
"""

import json
import os
import requests
import time
from typing import Dict, List, Tuple, Any
from collections import defaultdict

# Geographic level definitions
GEOGRAPHIC_LEVELS = {
    'region': {
        'name': 'Region',
        'zoom_threshold': 4,
        'boundaries': {
            'Northeast': {'lat_range': (40.0, 47.0), 'lon_range': (-80.0, -66.0)},
            'Southeast': {'lat_range': (24.0, 40.0), 'lon_range': (-87.0, -75.0)},
            'Midwest': {'lat_range': (36.0, 49.0), 'lon_range': (-104.0, -80.0)},
            'Southwest': {'lat_range': (31.0, 42.0), 'lon_range': (-120.0, -96.0)},
            'West': {'lat_range': (32.0, 49.0), 'lon_range': (-125.0, -102.0)},
            'Mountain': {'lat_range': (31.0, 49.0), 'lon_range': (-120.0, -102.0)},
            'Pacific': {'lat_range': (32.0, 49.0), 'lon_range': (-125.0, -116.0)}
        }
    },
    'state_region': {
        'name': 'State Region',
        'zoom_threshold': 6,
        'boundaries': {
            'New England': {'states': ['09', '23', '25', '33', '44', '50']},
            'Mid-Atlantic': {'states': ['34', '36', '42']},
            'South Atlantic': {'states': ['10', '11', '12', '13', '24', '37', '45', '51', '54']},
            'East North Central': {'states': ['17', '18', '26', '27', '39', '55']},
            'West North Central': {'states': ['19', '20', '27', '29', '31', '38', '46']},
            'East South Central': {'states': ['01', '21', '28', '47']},
            'West South Central': {'states': ['05', '22', '40', '48']},
            'Mountain': {'states': ['04', '08', '16', '30', '32', '35', '49', '56']},
            'Pacific': {'states': ['02', '06', '15', '41', '53']}
        }
    },
    'state': {
        'name': 'State',
        'zoom_threshold': 8,
        'boundaries': {}  # Will be populated from actual state data
    },
    'zipcode': {
        'name': 'ZIP Code',
        'zoom_threshold': 10,
        'boundaries': {}  # Will be populated from actual ZIP data
    }
}

# Statistical aggregation functions
STATISTICAL_METHODS = {
    'average': lambda values: sum(values) / len(values) if values else 0,
    'median': lambda values: sorted(values)[len(values)//2] if values else 0,
    'max': lambda values: max(values) if values else 0,
    'min': lambda values: min(values) if values else 0,
    'count': lambda values: len(values)
}

def load_zip_data() -> List[Dict]:
    """Load ZIP code data from GeoJSON."""
    try:
        with open('data_demo/zip_latest.geojson', 'r') as f:
            data = json.load(f)
        return data['features']
    except Exception as e:
        print(f"❌ Error loading ZIP data: {e}")
        return []

def get_coordinates_for_zip(zip_code: str) -> Tuple[float, float]:
    """Get coordinates for a ZIP code."""
    coords_file = 'data_demo/zip_coordinates.json'
    
    if os.path.exists(coords_file):
        try:
            with open(coords_file, 'r') as f:
                coords = json.load(f)
            if zip_code in coords:
                return coords[zip_code]['lat'], coords[zip_code]['lon']
        except Exception as e:
            print(f"⚠️ Error loading coordinates: {e}")
    
    return None, None

def determine_geographic_level(zoom_level: int) -> str:
    """Determine which geographic level to use based on zoom level."""
    for level, config in GEOGRAPHIC_LEVELS.items():
        if zoom_level <= config['zoom_threshold']:
            return level
    return 'zipcode'  # Default to most granular

def aggregate_by_region(zip_features: List[Dict]) -> Dict[str, Any]:
    """Aggregate ZIP codes by region."""
    region_data = defaultdict(lambda: {
        'features': [],
        'total_zhvi': 0,
        'total_zori': 0,
        'count': 0,
        'coordinates': []
    })
    
    for feature in zip_features:
        zip_code = str(feature['properties']['zcta'])
        lat, lon = get_coordinates_for_zip(zip_code)
        
        if lat is None or lon is None:
            continue
            
        # Determine which region this ZIP belongs to
        region = determine_region_from_coordinates(lat, lon)
        
        if region:
            region_data[region]['features'].append(feature)
            region_data[region]['total_zhvi'] += feature['properties']['zhvi'] or 0
            region_data[region]['total_zori'] += feature['properties']['zori'] or 0
            region_data[region]['count'] += 1
            region_data[region]['coordinates'].append((lat, lon))
    
    return dict(region_data)

def determine_region_from_coordinates(lat: float, lon: float) -> str:
    """Determine which region a coordinate belongs to."""
    for region, bounds in GEOGRAPHIC_LEVELS['region']['boundaries'].items():
        if (bounds['lat_range'][0] <= lat <= bounds['lat_range'][1] and
            bounds['lon_range'][0] <= lon <= bounds['lon_range'][1]):
            return region
    return 'Other'

def aggregate_by_state_region(zip_features: List[Dict]) -> Dict[str, Any]:
    """Aggregate ZIP codes by state region (groups of states)."""
    state_region_data = defaultdict(lambda: {
        'features': [],
        'total_zhvi': 0,
        'total_zori': 0,
        'count': 0,
        'coordinates': [],
        'states': set()
    })
    
    for feature in zip_features:
        zip_code = str(feature['properties']['zcta'])
        if len(zip_code) < 2:
            continue
            
        state_code = zip_code[:2]
        lat, lon = get_coordinates_for_zip(zip_code)
        
        if lat is None or lon is None:
            continue
        
        # Find which state region this state belongs to
        state_region = determine_state_region_from_state_code(state_code)
        
        if state_region:
            state_region_data[state_region]['features'].append(feature)
            state_region_data[state_region]['total_zhvi'] += feature['properties']['zhvi'] or 0
            state_region_data[state_region]['total_zori'] += feature['properties']['zori'] or 0
            state_region_data[state_region]['count'] += 1
            state_region_data[state_region]['coordinates'].append((lat, lon))
            state_region_data[state_region]['states'].add(state_code)
    
    # Convert sets to lists for JSON serialization
    for data in state_region_data.values():
        data['states'] = list(data['states'])
    
    return dict(state_region_data)

def determine_state_region_from_state_code(state_code: str) -> str:
    """Determine which state region a state code belongs to."""
    for region, config in GEOGRAPHIC_LEVELS['state_region']['boundaries'].items():
        if state_code in config['states']:
            return region
    return 'Other'

def aggregate_by_state(zip_features: List[Dict]) -> Dict[str, Any]:
    """Aggregate ZIP codes by state (using first 2 digits of ZIP)."""
    state_data = defaultdict(lambda: {
        'features': [],
        'total_zhvi': 0,
        'total_zori': 0,
        'count': 0,
        'coordinates': []
    })
    
    for feature in zip_features:
        zip_code = str(feature['properties']['zcta'])
        if len(zip_code) < 2:
            continue
            
        state_code = zip_code[:2]
        lat, lon = get_coordinates_for_zip(zip_code)
        
        if lat is None or lon is None:
            continue
            
        state_data[state_code]['features'].append(feature)
        state_data[state_code]['total_zhvi'] += feature['properties']['zhvi'] or 0
        state_data[state_code]['total_zori'] += feature['properties']['zori'] or 0
        state_data[state_code]['count'] += 1
        state_data[state_code]['coordinates'].append((lat, lon))
    
    return dict(state_data)

def create_geojson_features(aggregated_data: Dict[str, Any], level: str) -> List[Dict]:
    """Create GeoJSON features from aggregated data."""
    features = []
    
    for key, data in aggregated_data.items():
        if not data['coordinates']:
            continue
            
        # Calculate center coordinates
        avg_lat = sum(coord[0] for coord in data['coordinates']) / len(data['coordinates'])
        avg_lon = sum(coord[1] for coord in data['coordinates']) / len(data['coordinates'])
        
        # Calculate statistics
        zhvi_values = [f['properties']['zhvi'] for f in data['features'] if f['properties']['zhvi']]
        zori_values = [f['properties']['zori'] for f in data['features'] if f['properties']['zori']]
        
        # Create polygon bounds (simplified rectangular bounds)
        lat_range = max(coord[0] for coord in data['coordinates']) - min(coord[0] for coord in data['coordinates'])
        lon_range = max(coord[1] for coord in data['coordinates']) - min(coord[1] for coord in data['coordinates'])
        
        # Create a reasonable polygon size
        lat_padding = max(0.5, lat_range * 0.1)
        lon_padding = max(0.5, lon_range * 0.1)
        
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
                'level': level,
                'count': data['count'],
                'avg_zhvi': data['total_zhvi'] / data['count'] if data['count'] > 0 else 0,
                'avg_zori': data['total_zori'] / data['count'] if data['count'] > 0 else 0,
                'median_zhvi': STATISTICAL_METHODS['median'](zhvi_values),
                'median_zori': STATISTICAL_METHODS['median'](zori_values),
                'max_zhvi': STATISTICAL_METHODS['max'](zhvi_values),
                'max_zori': STATISTICAL_METHODS['max'](zori_values),
                'min_zhvi': STATISTICAL_METHODS['min'](zhvi_values),
                'min_zori': STATISTICAL_METHODS['min'](zori_values),
                'timeValues': {
                    '2024-01': { 'zhvi': (data['total_zhvi'] / data['count']) * 0.95, 'zori': (data['total_zori'] / data['count']) * 0.95 },
                    '2024-02': { 'zhvi': (data['total_zhvi'] / data['count']) * 0.97, 'zori': (data['total_zori'] / data['count']) * 0.97 },
                    '2024-03': { 'zhvi': (data['total_zhvi'] / data['count']) * 0.99, 'zori': (data['total_zori'] / data['count']) * 0.99 },
                    '2024-04': { 'zhvi': (data['total_zhvi'] / data['count']) * 1.01, 'zori': (data['total_zori'] / data['count']) * 1.01 },
                    '2024-05': { 'zhvi': (data['total_zhvi'] / data['count']) * 1.03, 'zori': (data['total_zori'] / data['count']) * 1.03 },
                    '2024-06': { 'zhvi': data['total_zhvi'] / data['count'], 'zori': data['total_zori'] / data['count'] }
                }
            }
        }
        features.append(feature)
    
    return features

def main():
    print("🏗️ Creating multi-level geographic aggregation...")
    
    # Load ZIP code data
    zip_features = load_zip_data()
    if not zip_features:
        print("❌ No ZIP code data found. Run the pipeline first.")
        return
    
    print(f"📊 Loaded {len(zip_features)} ZIP code features")
    
    # Create data directory
    os.makedirs('data_demo/aggregated', exist_ok=True)
    
    # Generate region-level aggregation
    print("🗺️ Generating region-level aggregation...")
    region_data = aggregate_by_region(zip_features)
    region_features = create_geojson_features(region_data, 'region')
    
    region_geojson = {
        'type': 'FeatureCollection',
        'features': region_features
    }
    
    with open('data_demo/aggregated/regions.geojson', 'w') as f:
        json.dump(region_geojson, f, indent=2)
    
    print(f"✅ Created {len(region_features)} region features")
    
    # Generate state region-level aggregation
    print("🗺️ Generating state region-level aggregation...")
    state_region_data = aggregate_by_state_region(zip_features)
    state_region_features = create_geojson_features(state_region_data, 'state_region')
    
    state_region_geojson = {
        'type': 'FeatureCollection',
        'features': state_region_features
    }
    
    with open('data_demo/aggregated/state_regions.geojson', 'w') as f:
        json.dump(state_region_geojson, f, indent=2)
    
    print(f"✅ Created {len(state_region_features)} state region features")
    
    # Generate state-level aggregation
    print("🗺️ Generating state-level aggregation...")
    state_data = aggregate_by_state(zip_features)
    state_features = create_geojson_features(state_data, 'state')
    
    state_geojson = {
        'type': 'FeatureCollection',
        'features': state_features
    }
    
    with open('data_demo/aggregated/states.geojson', 'w') as f:
        json.dump(state_geojson, f, indent=2)
    
    print(f"✅ Created {len(state_features)} state features")
    
    # Create configuration file
    config = {
        'geographic_levels': GEOGRAPHIC_LEVELS,
        'statistical_methods': list(STATISTICAL_METHODS.keys()),
        'data_files': {
            'regions': 'data_demo/aggregated/regions.geojson',
            'state_regions': 'data_demo/aggregated/state_regions.geojson',
            'states': 'data_demo/aggregated/states.geojson',
            'zipcodes': 'data_demo/zip_latest.geojson'
        }
    }
    
    with open('data_demo/aggregated/config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Multi-level aggregation complete!")
    print("📁 Files created:")
    print("  - data_demo/aggregated/regions.geojson")
    print("  - data_demo/aggregated/state_regions.geojson")
    print("  - data_demo/aggregated/states.geojson")
    print("  - data_demo/aggregated/config.json")

if __name__ == "__main__":
    main()
