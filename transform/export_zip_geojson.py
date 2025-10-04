import geopandas as gpd, duckdb
con = duckdb.connect("zillow.duckdb")
df = con.execute("SELECT * FROM zip_metrics_monthly WHERE date=(SELECT max(date) FROM zip_metrics_monthly)").df()
shp = gpd.read_file("https://www2.census.gov/geo/tiger/TIGER2023/ZCTA5/tl_2023_us_zcta520.zip")
shp = shp.rename(columns={"ZCTA5CE20":"zcta"})
gdf = shp.merge(df, on="zcta", how="inner")
gdf.to_file("app/data_demo/zip_latest.geojson", driver="GeoJSON")
print("✅ Exported ZIP GeoJSON")
