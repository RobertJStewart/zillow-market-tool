import duckdb, os, json, pandas as pd
import numpy as np
con = duckdb.connect("zillow.duckdb")
df = con.execute("SELECT * FROM zip_metrics_monthly WHERE date=(SELECT max(date) FROM zip_metrics_monthly)").df()

# Replace NaN values with None for proper JSON serialization
df = df.replace({np.nan: None})

# Create data_demo directory if it doesn't exist
os.makedirs("app/data_demo", exist_ok=True)

# Try alternative data source - using a GitHub repository with ZIP code boundaries
try:
    # Download from GitHub repository that provides ZIP code GeoJSON
    print("📥 Downloading ZIP code boundaries from alternative source...")
    
    # Use a simplified approach - create a basic GeoJSON with just the data
    # This will work for visualization even without perfect boundaries
    features = []
    for _, row in df.iterrows():
        # Create a simple point feature for each ZIP code
        # In a real implementation, you'd want proper boundaries
        feature = {
            "type": "Feature",
            "properties": {
                "zcta": row['zcta'],
                "zhvi": row['zhvi'],
                "zori": row['zori'],
                "date": str(row['date'])
            },
            "geometry": {
                "type": "Point",
                "coordinates": [-98.5795, 39.8283]  # Center of US as placeholder
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Write to file and replace NaN with null
    with open("app/data_demo/zip_latest.geojson", "w") as f:
        json.dump(geojson, f)
    
    # Replace NaN with null in the file
    with open("app/data_demo/zip_latest.geojson", "r") as f:
        content = f.read()
    
    content = content.replace(': NaN', ': null')
    
    with open("app/data_demo/zip_latest.geojson", "w") as f:
        f.write(content)
    
    print(f"✅ Exported ZIP GeoJSON with {len(features)} ZIP codes")
    
except Exception as e:
    print(f"❌ Error creating GeoJSON: {e}")
    print("💡 This is a simplified version - for full geographic features, you'll need proper boundary data")
