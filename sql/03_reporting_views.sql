USE FinanceBudgetActualDB;
GO


--create the main Budget vs Actual view
CREATE OR ALTER VIEW finance.vw_monthly_budget_vs_actual AS
WITH actual_monthly AS (
    SELECT
        dd.month_start_date,
        fa.department_id,
        fa.category_id,
        fa.region_id,
        fa.account_type,
        SUM(fa.actual_amount) AS total_actual
    FROM staging.fact_actuals fa
    INNER JOIN staging.dim_date dd
        ON fa.date = dd.date
    GROUP BY
        dd.month_start_date,
        fa.department_id,
        fa.category_id,
        fa.region_id,
        fa.account_type
),
budget_monthly AS (
    SELECT
        month_start_date,
        department_id,
        category_id,
        region_id,
        account_type,
        SUM(budget_amount) AS total_budget
    FROM staging.fact_budget
    GROUP BY
        month_start_date,
        department_id,
        category_id,
        region_id,
        account_type
)
SELECT
    COALESCE(a.month_start_date, b.month_start_date) AS month_start_date,
    COALESCE(a.department_id, b.department_id) AS department_id,
    COALESCE(a.category_id, b.category_id) AS category_id,
    COALESCE(a.region_id, b.region_id) AS region_id,
    COALESCE(a.account_type, b.account_type) AS account_type,

    COALESCE(a.total_actual, 0) AS total_actual,
    COALESCE(b.total_budget, 0) AS total_budget,

    COALESCE(a.total_actual, 0) - COALESCE(b.total_budget, 0) AS variance_amount,

    CASE
        WHEN COALESCE(b.total_budget, 0) = 0 THEN NULL
        ELSE
            100.0 * (
                COALESCE(a.total_actual, 0) - COALESCE(b.total_budget, 0)
            ) / COALESCE(b.total_budget, 0)
    END AS variance_pct,

    CASE
        WHEN COALESCE(a.account_type, b.account_type) = 'Revenue'
             AND COALESCE(a.total_actual, 0) - COALESCE(b.total_budget, 0) >= 0
            THEN 'Favorable'

        WHEN COALESCE(a.account_type, b.account_type) = 'Revenue'
             AND COALESCE(a.total_actual, 0) - COALESCE(b.total_budget, 0) < 0
            THEN 'Unfavorable'

        WHEN COALESCE(a.account_type, b.account_type) = 'Expense'
             AND COALESCE(a.total_actual, 0) - COALESCE(b.total_budget, 0) <= 0
            THEN 'Favorable'

        WHEN COALESCE(a.account_type, b.account_type) = 'Expense'
             AND COALESCE(a.total_actual, 0) - COALESCE(b.total_budget, 0) > 0
            THEN 'Unfavorable'

        ELSE 'Check'
    END AS variance_status
FROM actual_monthly a
FULL OUTER JOIN budget_monthly b
    ON a.month_start_date = b.month_start_date
    AND a.department_id = b.department_id
    AND a.category_id = b.category_id
    AND a.region_id = b.region_id
    AND a.account_type = b.account_type;
GO


--create department, category, and monthly summary views
CREATE OR ALTER VIEW finance.vw_department_variance AS
SELECT
    d.department_name,
    d.department_group,
    v.account_type,
    SUM(v.total_actual) AS total_actual,
    SUM(v.total_budget) AS total_budget,
    SUM(v.variance_amount) AS variance_amount,
    CASE
        WHEN SUM(v.total_budget) = 0 THEN NULL
        ELSE 100.0 * SUM(v.variance_amount) / SUM(v.total_budget)
    END AS variance_pct
FROM finance.vw_monthly_budget_vs_actual v
INNER JOIN staging.dim_department d
    ON v.department_id = d.department_id
GROUP BY
    d.department_name,
    d.department_group,
    v.account_type;
GO

CREATE OR ALTER VIEW finance.vw_category_variance AS
SELECT
    c.category_name,
    c.category_group,
    c.account_type,
    SUM(v.total_actual) AS total_actual,
    SUM(v.total_budget) AS total_budget,
    SUM(v.variance_amount) AS variance_amount,
    CASE
        WHEN SUM(v.total_budget) = 0 THEN NULL
        ELSE 100.0 * SUM(v.variance_amount) / SUM(v.total_budget)
    END AS variance_pct
FROM finance.vw_monthly_budget_vs_actual v
INNER JOIN staging.dim_category c
    ON v.category_id = c.category_id
GROUP BY
    c.category_name,
    c.category_group,
    c.account_type;
GO

CREATE OR ALTER VIEW finance.vw_monthly_summary AS
SELECT
    v.month_start_date,
    dt.year,
    dt.quarter,
    dt.month_number,
    dt.month_name,
    dt.year_month,
    v.account_type,
    SUM(v.total_actual) AS total_actual,
    SUM(v.total_budget) AS total_budget,
    SUM(v.variance_amount) AS variance_amount,
    CASE
        WHEN SUM(v.total_budget) = 0 THEN NULL
        ELSE 100.0 * SUM(v.variance_amount) / SUM(v.total_budget)
    END AS variance_pct
FROM finance.vw_monthly_budget_vs_actual v
INNER JOIN staging.dim_date dt
    ON v.month_start_date = dt.date
GROUP BY
    v.month_start_date,
    dt.year,
    dt.quarter,
    dt.month_number,
    dt.month_name,
    dt.year_month,
    v.account_type;
GO

--Monthly P&L view
CREATE OR ALTER VIEW finance.vw_monthly_pnl AS
SELECT
    v.month_start_date,
    dt.year,
    dt.quarter,
    dt.month_number,
    dt.month_name,
    dt.year_month,

    SUM(CASE WHEN v.account_type = 'Revenue' THEN v.total_actual ELSE 0 END) AS actual_revenue,
    SUM(CASE WHEN v.account_type = 'Revenue' THEN v.total_budget ELSE 0 END) AS budget_revenue,

    SUM(CASE WHEN v.account_type = 'Expense' THEN v.total_actual ELSE 0 END) AS actual_expense,
    SUM(CASE WHEN v.account_type = 'Expense' THEN v.total_budget ELSE 0 END) AS budget_expense,

    SUM(CASE WHEN v.account_type = 'Revenue' THEN v.total_actual ELSE 0 END)
    - SUM(CASE WHEN v.account_type = 'Expense' THEN v.total_actual ELSE 0 END) AS actual_net_result,

    SUM(CASE WHEN v.account_type = 'Revenue' THEN v.total_budget ELSE 0 END)
    - SUM(CASE WHEN v.account_type = 'Expense' THEN v.total_budget ELSE 0 END) AS budget_net_result,

    (
        SUM(CASE WHEN v.account_type = 'Revenue' THEN v.total_actual ELSE 0 END)
        - SUM(CASE WHEN v.account_type = 'Expense' THEN v.total_actual ELSE 0 END)
    )
    -
    (
        SUM(CASE WHEN v.account_type = 'Revenue' THEN v.total_budget ELSE 0 END)
        - SUM(CASE WHEN v.account_type = 'Expense' THEN v.total_budget ELSE 0 END)
    ) AS net_result_variance
FROM finance.vw_monthly_budget_vs_actual v
INNER JOIN staging.dim_date dt
    ON v.month_start_date = dt.date
GROUP BY
    v.month_start_date,
    dt.year,
    dt.quarter,
    dt.month_number,
    dt.month_name,
    dt.year_month;
GO



-- Unfavorable variances view
CREATE OR ALTER VIEW finance.vw_unfavorable_variances AS
SELECT
    v.month_start_date,
    dt.year,
    dt.quarter,
    dt.month_number,
    dt.month_name,
    dt.year_month,
    d.department_name,
    d.department_group,
    c.category_name,
    c.category_group,
    r.region_name,
    v.account_type,
    v.total_actual,
    v.total_budget,
    v.variance_amount,
    v.variance_pct,
    ABS(v.variance_amount) AS abs_variance_amount,
    v.variance_status
FROM finance.vw_monthly_budget_vs_actual v
INNER JOIN staging.dim_date dt
    ON v.month_start_date = dt.date
INNER JOIN staging.dim_department d
    ON v.department_id = d.department_id
INNER JOIN staging.dim_category c
    ON v.category_id = c.category_id
INNER JOIN staging.dim_region r
    ON v.region_id = r.region_id
WHERE v.variance_status = 'Unfavorable';
GO



--Budget utilization view
CREATE OR ALTER VIEW finance.vw_budget_utilization AS
SELECT
    v.month_start_date,
    dt.year,
    dt.quarter,
    dt.month_number,
    dt.month_name,
    dt.year_month,
    d.department_name,
    c.category_name,
    c.category_group,
    r.region_name,
    v.account_type,
    v.total_actual,
    v.total_budget,
    CASE
        WHEN v.total_budget = 0 THEN NULL
        ELSE 100.0 * v.total_actual / v.total_budget
    END AS budget_utilization_pct,
    v.variance_amount,
    v.variance_pct,
    v.variance_status
FROM finance.vw_monthly_budget_vs_actual v
INNER JOIN staging.dim_date dt
    ON v.month_start_date = dt.date
INNER JOIN staging.dim_department d
    ON v.department_id = d.department_id
INNER JOIN staging.dim_category c
    ON v.category_id = c.category_id
INNER JOIN staging.dim_region r
    ON v.region_id = r.region_id;
GO



--YTD Budget vs Actual view
CREATE OR ALTER VIEW finance.vw_ytd_budget_vs_actual AS
SELECT
    v.month_start_date,
    dt.year,
    dt.month_number,
    dt.month_name,
    dt.year_month,
    v.account_type,

    SUM(v.total_actual) OVER (
        PARTITION BY dt.year, v.account_type
        ORDER BY v.month_start_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS actual_ytd,

    SUM(v.total_budget) OVER (
        PARTITION BY dt.year, v.account_type
        ORDER BY v.month_start_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS budget_ytd,

    SUM(v.variance_amount) OVER (
        PARTITION BY dt.year, v.account_type
        ORDER BY v.month_start_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS variance_ytd
FROM finance.vw_monthly_summary v
INNER JOIN staging.dim_date dt
    ON v.month_start_date = dt.date;
GO


--Validate reporting views
SELECT TOP 20 *
FROM finance.vw_monthly_budget_vs_actual
ORDER BY month_start_date, department_id, category_id, region_id;


--
SELECT *
FROM finance.vw_monthly_summary
ORDER BY month_start_date, account_type;

--
SELECT TOP 10 *
FROM finance.vw_department_variance
ORDER BY ABS(variance_amount) DESC;


--
SELECT TOP 10 *
FROM finance.vw_category_variance
ORDER BY ABS(variance_amount) DESC;


SELECT TOP 20 *
FROM finance.vw_monthly_pnl
ORDER BY month_start_date;

SELECT TOP 20 *
FROM finance.vw_unfavorable_variances
ORDER BY abs_variance_amount DESC;

SELECT TOP 20 *
FROM finance.vw_budget_utilization
ORDER BY budget_utilization_pct DESC;

SELECT TOP 20 *
FROM finance.vw_ytd_budget_vs_actual
ORDER BY month_start_date, account_type;