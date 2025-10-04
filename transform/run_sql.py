import duckdb

con = duckdb.connect("zillow.duckdb")

with open("transform/build_zip_metrics.sql", "r") as f:
    sql = f.read()

con.execute(sql)
print("✅ Ran SQL transform via Python")
