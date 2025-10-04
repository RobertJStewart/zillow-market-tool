CREATE OR REPLACE TABLE zip_metrics_monthly AS
WITH zhvi_clean AS (
  SELECT 
    RegionName AS zcta,
    "Date" AS date,
    Value AS zhvi
  FROM zhvi_raw
),
zori_clean AS (
  SELECT 
    RegionName AS zcta,
    "Date" AS date,
    Value AS zori
  FROM zori_raw
)
SELECT 
  m.zcta,
  m.date,
  m.zhvi,
  r.zori
FROM zhvi_clean m
LEFT JOIN zori_clean r USING (zcta, date);
