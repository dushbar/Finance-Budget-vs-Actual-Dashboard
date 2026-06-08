"""
Finance Budget vs Actual Dashboard Dataset Generator

Creates a realistic synthetic finance dataset for a Budget vs Actual Power BI + SQL project.

Outputs:
- dim_date.csv
- dim_department.csv
- dim_category.csv
- dim_region.csv
- fact_budget.csv
- fact_actuals.csv
- fact_budget_dirty.csv
- fact_actuals_dirty.csv
- dq_issue_manifest.csv

Recommended use:
1. Use clean files for the first version of the dashboard.
2. Use dirty files later for SQL data-quality validation checks.
"""

from pathlib import Path
import numpy as np
import pandas as pd


# -----------------------------
# Configuration
# -----------------------------

SEED = 42
START_DATE = "2023-01-01"
END_DATE = "2025-12-31"

OUTPUT_DIR = Path("data/raw")

np.random.seed(SEED)


# -----------------------------
# Helper functions
# -----------------------------

def month_start(date_series: pd.Series) -> pd.Series:
    return date_series.values.astype("datetime64[M]")


def safe_round_amount(x: float) -> float:
    return round(float(x), 2)


def make_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Dimensions
# -----------------------------

def create_dim_date(start_date: str, end_date: str) -> pd.DataFrame:
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    df = pd.DataFrame({"date": dates})
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["date"].dt.year
    df["quarter"] = "Q" + df["date"].dt.quarter.astype(str)
    df["month_number"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["month_start_date"] = df["date"].values.astype("datetime64[M]")
    df["day_of_month"] = df["date"].dt.day
    df["day_name"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)

    return df


def create_dim_department() -> pd.DataFrame:
    data = [
        (1, "Sales", "Commercial"),
        (2, "Marketing", "Commercial"),
        (3, "Operations", "Operations"),
        (4, "Finance", "Corporate"),
        (5, "HR", "Corporate"),
        (6, "IT", "Corporate"),
        (7, "Customer Support", "Operations"),
    ]

    return pd.DataFrame(
        data,
        columns=["department_id", "department_name", "department_group"]
    )


def create_dim_category() -> pd.DataFrame:
    data = [
        (101, "Product Revenue", "Revenue", "Revenue"),
        (102, "Service Revenue", "Revenue", "Revenue"),
        (103, "Subscription Revenue", "Revenue", "Revenue"),

        (201, "Salary", "Expense", "People Cost"),
        (202, "Software", "Expense", "Technology"),
        (203, "Rent", "Expense", "Facilities"),
        (204, "Marketing Spend", "Expense", "Growth"),
        (205, "Travel", "Expense", "Operations"),
        (206, "Utilities", "Expense", "Facilities"),
        (207, "Training", "Expense", "People Cost"),
        (208, "Consulting", "Expense", "Professional Services"),
    ]

    return pd.DataFrame(
        data,
        columns=["category_id", "category_name", "account_type", "category_group"]
    )


def create_dim_region() -> pd.DataFrame:
    data = [
        (1, "North", 1.20),
        (2, "South", 1.05),
        (3, "East", 0.90),
        (4, "West", 1.15),
        (5, "Central", 0.80),
    ]

    return pd.DataFrame(
        data,
        columns=["region_id", "region_name", "region_weight"]
    )


# -----------------------------
# Budget generation
# -----------------------------

def create_budget(
    dim_date: pd.DataFrame,
    dim_department: pd.DataFrame,
    dim_category: pd.DataFrame,
    dim_region: pd.DataFrame,
) -> pd.DataFrame:

    months = (
        dim_date[["month_start_date", "year", "month_number", "year_month"]]
        .drop_duplicates()
        .sort_values("month_start_date")
        .reset_index(drop=True)
    )

    revenue_base = {
        "Product Revenue": 260_000,
        "Service Revenue": 120_000,
        "Subscription Revenue": 180_000,
    }

    expense_base = {
        "Salary": 95_000,
        "Software": 22_000,
        "Rent": 30_000,
        "Marketing Spend": 45_000,
        "Travel": 14_000,
        "Utilities": 9_000,
        "Training": 6_000,
        "Consulting": 18_000,
    }

    department_expense_weight = {
        "Sales": 1.15,
        "Marketing": 1.20,
        "Operations": 1.25,
        "Finance": 0.75,
        "HR": 0.65,
        "IT": 0.95,
        "Customer Support": 0.85,
    }

    allowed_expense_categories_by_department = {
        "Sales": ["Salary", "Software", "Travel", "Training", "Consulting"],
        "Marketing": ["Salary", "Software", "Marketing Spend", "Travel", "Training", "Consulting"],
        "Operations": ["Salary", "Software", "Rent", "Travel", "Utilities", "Training", "Consulting"],
        "Finance": ["Salary", "Software", "Training", "Consulting"],
        "HR": ["Salary", "Software", "Training", "Consulting"],
        "IT": ["Salary", "Software", "Training", "Consulting"],
        "Customer Support": ["Salary", "Software", "Rent", "Utilities", "Training"],
    }

    revenue_departments = ["Sales", "Customer Support"]

    # Month seasonality
    # Higher revenue in March, October, November, December.
    # Higher marketing spend in Q4.
    revenue_seasonality = {
        1: 0.92,
        2: 0.95,
        3: 1.12,
        4: 0.98,
        5: 1.00,
        6: 1.03,
        7: 0.97,
        8: 0.99,
        9: 1.05,
        10: 1.12,
        11: 1.22,
        12: 1.30,
    }

    marketing_seasonality = {
        1: 0.80,
        2: 0.85,
        3: 0.90,
        4: 0.95,
        5: 1.00,
        6: 1.05,
        7: 1.00,
        8: 1.05,
        9: 1.15,
        10: 1.35,
        11: 1.55,
        12: 1.45,
    }

    rows = []
    budget_id = 1

    departments = dim_department.to_dict("records")
    categories = dim_category.to_dict("records")
    regions = dim_region.to_dict("records")

    for _, month in months.iterrows():
        year = int(month["year"])
        month_num = int(month["month_number"])
        month_start_date = month["month_start_date"]

        year_growth = 1 + (year - 2023) * 0.08

        for region in regions:
            region_id = region["region_id"]
            region_weight = region["region_weight"]

            # Revenue budget
            for category in categories:
                if category["account_type"] != "Revenue":
                    continue

                category_name = category["category_name"]

                for department in departments:
                    department_name = department["department_name"]

                    if department_name not in revenue_departments:
                        continue

                    dept_revenue_weight = 1.00 if department_name == "Sales" else 0.22

                    base = revenue_base[category_name]
                    budget_amount = (
                        base
                        * region_weight
                        * dept_revenue_weight
                        * revenue_seasonality[month_num]
                        * year_growth
                        * np.random.normal(1.0, 0.03)
                    )

                    rows.append({
                        "budget_id": budget_id,
                        "month_start_date": month_start_date,
                        "department_id": department["department_id"],
                        "category_id": category["category_id"],
                        "region_id": region_id,
                        "account_type": "Revenue",
                        "budget_amount": safe_round_amount(max(budget_amount, 0)),
                    })
                    budget_id += 1

            # Expense budget
            for department in departments:
                department_name = department["department_name"]

                for category in categories:
                    if category["account_type"] != "Expense":
                        continue

                    category_name = category["category_name"]

                    if category_name not in allowed_expense_categories_by_department[department_name]:
                        continue

                    base = expense_base[category_name]
                    dept_weight = department_expense_weight[department_name]

                    if category_name == "Marketing Spend":
                        seasonal_multiplier = marketing_seasonality[month_num]
                    else:
                        seasonal_multiplier = 1.00

                    # Salary inflation year over year.
                    if category_name == "Salary":
                        category_growth = 1 + (year - 2023) * 0.07
                    elif category_name == "Software":
                        category_growth = 1 + (year - 2023) * 0.10
                    else:
                        category_growth = 1 + (year - 2023) * 0.04

                    # Corporate departments are less region-dependent.
                    if department["department_group"] == "Corporate":
                        region_expense_weight = 0.35
                    else:
                        region_expense_weight = region_weight

                    budget_amount = (
                        base
                        * dept_weight
                        * region_expense_weight
                        * seasonal_multiplier
                        * category_growth
                        * np.random.normal(1.0, 0.04)
                    )

                    rows.append({
                        "budget_id": budget_id,
                        "month_start_date": month_start_date,
                        "department_id": department["department_id"],
                        "category_id": category["category_id"],
                        "region_id": region_id,
                        "account_type": "Expense",
                        "budget_amount": safe_round_amount(max(budget_amount, 0)),
                    })
                    budget_id += 1

    return pd.DataFrame(rows)


# -----------------------------
# Actuals generation
# -----------------------------

def create_actuals(
    fact_budget: pd.DataFrame,
    dim_date: pd.DataFrame,
    dim_category: pd.DataFrame,
) -> pd.DataFrame:

    category_lookup = dim_category.set_index("category_id").to_dict("index")

    actual_rows = []
    actual_id = 1

    dates_by_month = {
        month: group["date"].tolist()
        for month, group in dim_date.groupby("month_start_date")
    }

    for _, budget_row in fact_budget.iterrows():
        month_start = budget_row["month_start_date"]
        dates = dates_by_month[month_start]

        category_id = budget_row["category_id"]
        category_name = category_lookup[category_id]["category_name"]
        account_type = budget_row["account_type"]
        budget_amount = float(budget_row["budget_amount"])

        # Controlled variance behavior by category.
        # Revenue categories can miss or exceed budget.
        # Expenses tend to overrun in Software, Marketing, Consulting, and Travel.
        if account_type == "Revenue":
            if category_name == "Subscription Revenue":
                actual_multiplier = np.random.normal(1.02, 0.06)
            elif category_name == "Product Revenue":
                actual_multiplier = np.random.normal(1.00, 0.11)
            else:
                actual_multiplier = np.random.normal(0.98, 0.09)

        else:
            if category_name == "Salary":
                actual_multiplier = np.random.normal(1.00, 0.025)
            elif category_name == "Software":
                actual_multiplier = np.random.normal(1.08, 0.08)
            elif category_name == "Marketing Spend":
                actual_multiplier = np.random.normal(1.12, 0.18)
            elif category_name == "Travel":
                actual_multiplier = np.random.normal(1.10, 0.20)
            elif category_name == "Consulting":
                actual_multiplier = np.random.normal(1.06, 0.12)
            else:
                actual_multiplier = np.random.normal(1.00, 0.06)

        actual_multiplier = max(actual_multiplier, 0.35)
        monthly_actual = budget_amount * actual_multiplier

        # Occasionally create a valid business case where a budget exists,
        # but no actual was recorded that month.
        if np.random.random() < 0.003:
            continue

        if account_type == "Revenue":
            avg_transaction_size = {
                "Product Revenue": 7_500,
                "Service Revenue": 5_000,
                "Subscription Revenue": 3_500,
            }[category_name]

            expected_transactions = max(8, int(monthly_actual / avg_transaction_size))
            n_transactions = np.random.poisson(expected_transactions)
            n_transactions = max(n_transactions, 5)

        else:
            if category_name == "Salary":
                n_transactions = np.random.randint(3, 8)
            elif category_name in ["Rent", "Utilities"]:
                n_transactions = np.random.randint(1, 4)
            elif category_name == "Software":
                n_transactions = np.random.randint(4, 12)
            elif category_name == "Marketing Spend":
                n_transactions = np.random.randint(8, 25)
            elif category_name == "Travel":
                n_transactions = np.random.randint(3, 16)
            else:
                n_transactions = np.random.randint(2, 10)

        selected_dates = np.random.choice(dates, size=n_transactions, replace=True)

        # Allocate the monthly actual amount across transactions.
        weights = np.random.dirichlet(np.ones(n_transactions))
        transaction_amounts = monthly_actual * weights

        for transaction_date, amount in zip(selected_dates, transaction_amounts):
            actual_rows.append({
                "actual_id": actual_id,
                "date": transaction_date,
                "department_id": budget_row["department_id"],
                "category_id": category_id,
                "region_id": budget_row["region_id"],
                "account_type": account_type,
                "actual_amount": safe_round_amount(amount),
            })
            actual_id += 1

    fact_actuals = pd.DataFrame(actual_rows)

    return fact_actuals


# -----------------------------
# Dirty data generation
# -----------------------------

def create_dirty_versions(
    fact_budget: pd.DataFrame,
    fact_actuals: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    dirty_budget = fact_budget.copy()
    dirty_actuals = fact_actuals.copy()

    issue_rows = []

    # 1. Duplicate budget rows
    duplicate_budget_rows = dirty_budget.sample(12, random_state=SEED)
    dirty_budget = pd.concat([dirty_budget, duplicate_budget_rows], ignore_index=True)

    issue_rows.append({
        "issue_type": "Duplicate budget rows",
        "table_name": "fact_budget_dirty",
        "expected_detection": "Group by month_start_date, department_id, category_id, region_id and find count > 1",
        "rows_affected": len(duplicate_budget_rows),
    })

    # 2. Zero budget rows
    zero_budget_indices = dirty_budget.sample(8, random_state=SEED + 1).index
    dirty_budget.loc[zero_budget_indices, "budget_amount"] = 0

    issue_rows.append({
        "issue_type": "Zero budget amount",
        "table_name": "fact_budget_dirty",
        "expected_detection": "WHERE budget_amount <= 0",
        "rows_affected": len(zero_budget_indices),
    })

    # 3. Actual rows with negative amount
    # This can represent reversals/refunds, but should be flagged and explained.
    negative_actual_indices = dirty_actuals.sample(15, random_state=SEED + 2).index
    dirty_actuals.loc[negative_actual_indices, "actual_amount"] = (
        dirty_actuals.loc[negative_actual_indices, "actual_amount"] * -1
    )

    issue_rows.append({
        "issue_type": "Negative actual amount",
        "table_name": "fact_actuals_dirty",
        "expected_detection": "WHERE actual_amount < 0",
        "rows_affected": len(negative_actual_indices),
    })

    # 4. Missing department_id
    missing_department_indices = dirty_actuals.sample(10, random_state=SEED + 3).index
    dirty_actuals.loc[missing_department_indices, "department_id"] = np.nan

    issue_rows.append({
        "issue_type": "Missing department_id in actuals",
        "table_name": "fact_actuals_dirty",
        "expected_detection": "WHERE department_id IS NULL",
        "rows_affected": len(missing_department_indices),
    })

    # 5. Actuals with no matching budget
    # Use a valid category/department/region combination but move date to a month that may not match budget pattern.
    no_budget_rows = dirty_actuals.sample(20, random_state=SEED + 4).copy()
    no_budget_rows["actual_id"] = range(
        int(dirty_actuals["actual_id"].max()) + 1,
        int(dirty_actuals["actual_id"].max()) + 1 + len(no_budget_rows)
    )
    no_budget_rows["date"] = pd.to_datetime("2025-12-31")
    no_budget_rows["actual_amount"] = no_budget_rows["actual_amount"].abs() * 1.5

    # Assign an unlikely but dimension-valid combination:
    # HR department receiving Product Revenue.
    no_budget_rows["department_id"] = 5
    no_budget_rows["category_id"] = 101
    no_budget_rows["account_type"] = "Revenue"

    dirty_actuals = pd.concat([dirty_actuals, no_budget_rows], ignore_index=True)

    issue_rows.append({
        "issue_type": "Actuals with no matching budget combination",
        "table_name": "fact_actuals_dirty",
        "expected_detection": "Monthly actual-budget full outer join where total_actual > 0 and total_budget = 0",
        "rows_affected": len(no_budget_rows),
    })

    issue_manifest = pd.DataFrame(issue_rows)

    return dirty_budget, dirty_actuals, issue_manifest


# -----------------------------
# Main
# -----------------------------

def main() -> None:
    make_dir(OUTPUT_DIR)

    print("Creating dimensions...")
    dim_date = create_dim_date(START_DATE, END_DATE)
    dim_department = create_dim_department()
    dim_category = create_dim_category()
    dim_region = create_dim_region()

    print("Creating monthly budget...")
    fact_budget = create_budget(
        dim_date=dim_date,
        dim_department=dim_department,
        dim_category=dim_category,
        dim_region=dim_region,
    )

    print("Creating daily actuals...")
    fact_actuals = create_actuals(
        fact_budget=fact_budget,
        dim_date=dim_date,
        dim_category=dim_category,
    )

    print("Creating dirty versions for SQL data-quality checks...")
    fact_budget_dirty, fact_actuals_dirty, dq_issue_manifest = create_dirty_versions(
        fact_budget=fact_budget,
        fact_actuals=fact_actuals,
    )

    # Save clean files
    dim_date.to_csv(OUTPUT_DIR / "dim_date.csv", index=False)
    dim_department.to_csv(OUTPUT_DIR / "dim_department.csv", index=False)
    dim_category.to_csv(OUTPUT_DIR / "dim_category.csv", index=False)
    dim_region.to_csv(OUTPUT_DIR / "dim_region.csv", index=False)
    fact_budget.to_csv(OUTPUT_DIR / "fact_budget.csv", index=False)
    fact_actuals.to_csv(OUTPUT_DIR / "fact_actuals.csv", index=False)

    # Save dirty files
    fact_budget_dirty.to_csv(OUTPUT_DIR / "fact_budget_dirty.csv", index=False)
    fact_actuals_dirty.to_csv(OUTPUT_DIR / "fact_actuals_dirty.csv", index=False)
    dq_issue_manifest.to_csv(OUTPUT_DIR / "dq_issue_manifest.csv", index=False)

    print("\nFiles created successfully.")
    print(f"Output folder: {OUTPUT_DIR.resolve()}")

    print("\nRow counts:")
    print(f"dim_date: {len(dim_date):,}")
    print(f"dim_department: {len(dim_department):,}")
    print(f"dim_category: {len(dim_category):,}")
    print(f"dim_region: {len(dim_region):,}")
    print(f"fact_budget: {len(fact_budget):,}")
    print(f"fact_actuals: {len(fact_actuals):,}")
    print(f"fact_budget_dirty: {len(fact_budget_dirty):,}")
    print(f"fact_actuals_dirty: {len(fact_actuals_dirty):,}")

    print("\nDate range:")
    print(f"Actuals min date: {fact_actuals['date'].min()}")
    print(f"Actuals max date: {fact_actuals['date'].max()}")

    print("\nBudget summary:")
    print(
        fact_budget
        .groupby("account_type")["budget_amount"]
        .sum()
        .round(2)
    )

    print("\nActual summary:")
    print(
        fact_actuals
        .groupby("account_type")["actual_amount"]
        .sum()
        .round(2)
    )

    print("\nDirty data issue manifest:")
    print(dq_issue_manifest)


if __name__ == "__main__":
    main()