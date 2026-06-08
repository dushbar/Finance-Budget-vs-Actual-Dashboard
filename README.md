# Finance Budget vs Actual Dashboard

## Project Overview

This project is an end-to-end Finance Budget vs Actual Dashboard built using Python, SQL Server, Power BI, and DAX.
The dashboard is structurally complete. Final visual polish, spacing refinements, and formatting improvements are ongoing.

The dashboard analyzes financial performance by comparing actual revenue and expenses against budgeted values across months, departments, regions, and financial categories. The goal is to help finance teams identify budget overruns, revenue shortfalls, unfavorable variance drivers, and accountability areas across the organization.

The project simulates a realistic finance analytics workflow:

1. Synthetic finance dataset generation using Python
2. Data storage and validation in SQL Server
3. Creation of reporting views for Power BI
4. Data modeling and DAX measures in Power BI
5. Multi-page executive dashboard design
6. Variance analysis and drill-down reporting

---

## Business Problem

Finance leaders need to monitor whether departments, regions, and categories are performing in line with budget expectations.

Typical questions answered by this dashboard include:

- Is the company over or under budget overall?
- Which departments are driving unfavorable variance?
- Are revenue shortfalls or expense overruns causing the biggest issue?
- Which regions have the weakest budget performance?
- Which financial categories require management attention?
- How does variance change over time?
- Where should leadership focus corrective action?

---

## Tools Used

- **Python**: Synthetic data generation
- **SQL Server**: Data storage, staging tables, validation, reporting views
- **Power BI**: Dashboard development and data visualization
- **DAX**: Financial KPIs, variance measures, utilization metrics, ranking logic
- **Power Query**: Data type handling and model preparation

---

## Dataset

The dataset was synthetically generated to resemble a realistic corporate finance environment.

### Main tables

- `dim_date`
- `dim_department`
- `dim_category`
- `dim_region`
- `fact_budget`
- `fact_actuals`

### Dataset characteristics

- Multiple years of monthly financial data
- Revenue and expense categories
- Department-level and region-level budgeting
- Actual transaction-level financial records
- Budget data stored at monthly planning grain
- Actuals stored at detailed transaction grain

This structure allows realistic budget vs actual analysis using different levels of aggregation.

---

## SQL Server Workflow

The data was imported into SQL Server using a staging schema and then transformed into reporting-ready views.

### Schemas

- `staging`: Raw imported tables
- `finance`: Reporting views used in Power BI

### Validation checks included

- Row count validation
- Duplicate budget grain check
- Date table validation
- Actuals and budget reconciliation
- Dimension relationship checks

### Reporting views

The SQL views were designed to simplify Power BI modeling and support dashboard visuals such as:

- Monthly budget vs actual trends
- Department variance summaries
- Regional variance summaries
- Category-level variance analysis
- Unfavorable variance drill-down tables

---

## Dashboard Pages

## Page 1: Executive Finance Overview

This page provides a high-level summary of company-wide financial performance.

### Key visuals

- Actual Revenue
- Budget Revenue
- Actual Expense
- Budget Expense
- Actual Net Result
- Net Result Variance
- Financial line matrix
- Monthly Budget vs Actual Trend
- Top Category Variance Drivers
- Budget Utilization Gap by Department
- Top Department Variance Drivers
- Top Unfavorable Variance Details

![Executive Finance Overview](screenshots/01_executive_finance_overview.png)

---

## Page 2: Budget Variance Deep Dive

This page focuses on detailed variance analysis across departments and time.

### Key visuals

- Net Variance
- Revenue Variance
- Expense Variance
- Budget Utilization %
- Net Variance by Department
- Monthly Net Variance and Budget Utilization
- Revenue vs Expense Variance by Department
- Top Unfavorable Category Variance Drivers
- Department Variance by Region Matrix

![Budget Variance Deep Dive](screenshots/02_budget_variance_deep_dive.png)

---

## Page 3: Department Performance & Budget Accountability

This page identifies which departments are performing well or poorly against budget.

### Key visuals

- Net Variance
- Best Department
- Worst Department
- Expense Over-Budget Departments
- Department Budget Performance Summary Matrix
- Actual vs Budget Expense by Department
- Net Variance by Department
- Unfavorable Category Variance Drivers

![Department Performance](screenshots/03_department_performance.png)

---

## Page 4: Regional & Category Budget Performance

This page analyzes regional financial performance and category-level variance.

### Key visuals

- Net Variance
- Revenue Variance
- Expense Variance
- Worst Region
- Regional Budget Performance Summary Matrix
- Net Variance by Region
- Revenue vs Expense Variance by Region
- Category Variance by Region Matrix

![Regional and Category Performance](screenshots/04_regional_category_performance.png)

---

## Page 5: Variance Explorer

This page acts as an interactive drill-down page for investigating detailed variance drivers.

### Key visuals

- Variance summary KPIs
- Detailed variance table
- Department, region, category, and month slicers
- Variance driver breakdowns
- Unfavorable variance exploration

![Variance Explorer](screenshots/05_variance_explorer.png)

---

## Key DAX Measures

The dashboard uses DAX measures for financial analysis, including:

```DAX
Actual Revenue = 
CALCULATE (
    SUM ( fact_actuals[actual_amount] ),
    dim_category[category_type] = "Revenue"
)
