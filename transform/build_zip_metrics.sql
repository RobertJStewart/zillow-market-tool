CREATE OR REPLACE TABLE zip_metrics AS
SELECT RegionName AS zcta, Date AS date, Value AS zhvi FROM zhvi_raw;
CREATE OR REPLACE TABLE zip_rent AS
SELECT RegionName AS zcta, Date AS date, Value AS zori FROM zori_raw;
CREATE OR REPLACE TABLE zip_metrics_monthly AS
SELECT m.zcta, m.date, m.zhvi, r.zori FROM zip_metrics m
LEFT JOIN zip_rent r USING (zcta, date);
