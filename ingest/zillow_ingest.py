import duckdb, pandas as pd
con = duckdb.connect("zillow.duckdb")
zhvi = pd.read_csv("data_raw/zhvi.csv")
zori = pd.read_csv("data_raw/zori.csv")
con.execute("CREATE OR REPLACE TABLE zhvi_raw AS SELECT * FROM zhvi")
con.execute("CREATE OR REPLACE TABLE zori_raw AS SELECT * FROM zori")
print("✅ Zillow CSVs loaded into DuckDB")
