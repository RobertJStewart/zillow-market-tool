import duckdb
import pandas as pd

# Connect to DuckDB
con = duckdb.connect("zillow.duckdb")

def load_and_melt(csv_path, table_name):
    """Load Zillow CSV and melt wide monthly columns into long format"""
    df = pd.read_csv(csv_path)
    
    # Zillow CSV has metadata columns, then monthly columns (YYYY-MM format)
    id_vars = ["RegionID", "SizeRank", "RegionName", "StateName", "Metro", "CountyName"]
    value_vars = [c for c in df.columns if c not in id_vars]
    
    # Melt the wide format into long format
    df_melted = df.melt(
        id_vars=["RegionName"],   # we only really care about RegionName for zcta
        value_vars=value_vars,
        var_name="Date",
        value_name="Value"
    )
    
    # Ensure date column is proper YYYY-MM format
    df_melted["Date"] = pd.to_datetime(df_melted["Date"], errors="coerce")
    
    # Remove rows with invalid dates or null values
    df_melted = df_melted.dropna(subset=["Date", "Value"])
    
    # Write into DuckDB
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.register("temp_df", df_melted)
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_df")
    
    print(f"✅ Loaded {table_name} with {len(df_melted)} rows")

# Run for both datasets
load_and_melt("data_raw/zhvi.csv", "zhvi_raw")
load_and_melt("data_raw/zori.csv", "zori_raw")
print("✅ Zillow CSVs loaded into DuckDB")
