import duckdb, h3, json
con = duckdb.connect("zillow.duckdb")
df = con.execute("SELECT * FROM zip_metrics_monthly").df()
features=[] 
for _,row in df.iterrows():
    hex_id=h3.geo_to_h3(37.77,-122.42,5)
    features.append({"type":"Feature","geometry":{"type":"Polygon","coordinates":[h3.h3_to_geo_boundary(hex_id,geo_json=True)]},"properties":dict(row)})
geo={"type":"FeatureCollection","features":features}
with open("app/data_demo/grid_latest.geojson","w") as f: json.dump(geo,f)
print("✅ Exported H3 grid GeoJSON")
