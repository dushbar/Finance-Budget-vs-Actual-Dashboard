CREATE DATABASE FinanceBudgetActualDB;
GO

USE FinanceBudgetActualDB;
GO

CREATE SCHEMA staging;
GO

CREATE SCHEMA finance;
GO


SELECT TOP 50 *
FROM staging.dim_date
ORDER BY [date];



SELECT 
    MIN([date]) AS min_date,
    MAX([date]) AS max_date,
    COUNT(*) AS row_count,
    COUNT(DISTINCT year_month) AS distinct_months
FROM staging.dim_date;




SELECT DISTINCT
    year_month,
    month_number,
    month_name,
    month_start_date
FROM staging.dim_date
ORDER BY year_month;



SELECT TOP 20
    [date],
    date_key,
    CONVERT(INT, FORMAT([date], 'yyyyMMdd')) AS expected_date_key
FROM staging.dim_date
ORDER BY [date];




