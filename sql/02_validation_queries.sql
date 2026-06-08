USE FinanceBudgetActualDB;
GO

-- Row counts
SELECT 'dim_date' AS table_name, COUNT(*) AS row_count FROM staging.dim_date
UNION ALL
SELECT 'dim_department', COUNT(*) FROM staging.dim_department
UNION ALL
SELECT 'dim_category', COUNT(*) FROM staging.dim_category
UNION ALL
SELECT 'dim_region', COUNT(*) FROM staging.dim_region
UNION ALL
SELECT 'fact_budget', COUNT(*) FROM staging.fact_budget
UNION ALL
SELECT 'fact_actuals', COUNT(*) FROM staging.fact_actuals;
GO

-- Date range
SELECT
    MIN(date) AS min_actual_date,
    MAX(date) AS max_actual_date
FROM staging.fact_actuals;
GO

-- Budget date range
SELECT
    MIN(month_start_date) AS min_budget_month,
    MAX(month_start_date) AS max_budget_month
FROM staging.fact_budget;
GO

-- Budget by account type
SELECT
    account_type,
    SUM(budget_amount) AS total_budget
FROM staging.fact_budget
GROUP BY account_type;
GO

-- Actuals by account type
SELECT
    account_type,
    SUM(actual_amount) AS total_actual
FROM staging.fact_actuals
GROUP BY account_type;
GO

-- Check department joins
SELECT COUNT(*) AS actual_rows_without_department
FROM staging.fact_actuals fa
LEFT JOIN staging.dim_department dd
    ON fa.department_id = dd.department_id
WHERE dd.department_id IS NULL;
GO

-- Check category joins
SELECT COUNT(*) AS actual_rows_without_category
FROM staging.fact_actuals fa
LEFT JOIN staging.dim_category dc
    ON fa.category_id = dc.category_id
WHERE dc.category_id IS NULL;
GO

-- Check region joins
SELECT COUNT(*) AS actual_rows_without_region
FROM staging.fact_actuals fa
LEFT JOIN staging.dim_region dr
    ON fa.region_id = dr.region_id
WHERE dr.region_id IS NULL;
GO

-- Check budget grain uniqueness
SELECT
    month_start_date,
    department_id,
    category_id,
    region_id,
    COUNT(*) AS row_count
FROM staging.fact_budget
GROUP BY
    month_start_date,
    department_id,
    category_id,
    region_id
HAVING COUNT(*) > 1;
GO