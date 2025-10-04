import duckdb, h3, json, os
con = duckdb.connect("zillow.duckdb")

# Create data_demo directory if it doesn't exist
os.makedirs("app/data_demo", exist_ok=True)

# Only get the latest data for each ZIP code to reduce processing time
print("📊 Processing H3 grid projection...")
df = con.execute("""
    SELECT zcta, 
           AVG(zhvi) as avg_zhvi, 
           AVG(zori) as avg_zori,
           MAX(date) as latest_date
    FROM zip_metrics_monthly 
    GROUP BY zcta
    LIMIT 1000
""").df()

print(f"Processing {len(df)} ZIP codes...")

features = [] 
for _, row in df.iterrows():
    # Use a fixed location for now (center of US)
    # In a real implementation, you'd geocode each ZIP to get lat/lon
    hex_id = h3.geo_to_h3(39.8283, -98.5795, 5)  # Center of US
    features.append({
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [h3.h3_to_geo_boundary(hex_id, geo_json=True)]
        },
        "properties": {
            "zcta": row['zcta'],
            "avg_zhvi": float(row['avg_zhvi']) if row['avg_zhvi'] is not None else 0,
            "avg_zori": float(row['avg_zori']) if row['avg_zori'] is not None else 0,
            "latest_date": str(row['latest_date'])
        }
    })

geo = {"type": "FeatureCollection", "features": features}
with open("app/data_demo/grid_latest.geojson", "w") as f: 
    json.dump(geo, f)

print(f"✅ Exported H3 grid GeoJSON with {len(features)} features")
