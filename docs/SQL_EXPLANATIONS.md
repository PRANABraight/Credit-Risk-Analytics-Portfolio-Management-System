# SQL Query Explanations

Detailed breakdown of the complex SQL queries used in this project.

## 1. Cohort Analysis (`sql/queries/cohort_analysis.sql`)

**Concept**: Vintage Analysis
**Goal**: See if the quality of new customers is improving or deteriorating over time.

**Key Techniques**:
- **CTEs (Common Table Expressions)**: Used `customer_cohorts` and `payment_performance` to break the problem into logical steps.
- **Date Manipulation**: `DATE_FORMAT` to truncate dates to the month level.
- **Join Logic**: Joining `repayment_history` -> `loan_application` -> `customer_profile` to link payments back to the customer's join date.

**Interpretation**:
- Rows = Cohort Month (When they joined)
- Columns = Months on Book (0, 1, 2...)
- Values = Repayment Rate %
- *Red Flag*: If the values in column "Month 1" are dropping for recent cohorts, it means acquisition quality is falling.

---

## 2. Risk Stratification (`sql/queries/risk_stratification.sql`)

**Concept**: Behavioral Segmentation
**Goal**: Create actionable buckets for operations teams (e.g., "Call Tier 4 first").

**Key Techniques**:
- **Conditional Aggregation**: `SUM(CASE WHEN ...)` to count specific events (late payments) per customer.
- **CASE Logic**: The complex `CASE WHEN` statement acts as the business rule engine to assign tiers.
- **Derived Metrics**: Calculated `days_since_last_miss` to differentiate between someone who missed a payment 2 years ago vs. yesterday.

**Business Logic**:
- **Tier 1 (Prime)**: Never missed, never late. (Automated credit limit increases)
- **Tier 2 (Standard)**: Occasional delays < 7 days. (No action needed)
- **Tier 3 (Subprime)**: Frequent delays. (SMS reminders)
- **Tier 4 (High Risk)**: Serious delinquency. (Call center priority)

---

## 3. Operational Bottleneck (`sql/queries/operational_bottleneck.sql`)

**Concept**: Pattern Recognition / Early Warning
**Goal**: Find "Good" customers who are turning "Bad".

**Key Techniques**:
- **Window Functions**: `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` to rank payments from newest to oldest.
- **Pivoting**: transforming rows (Payment 1, Payment 2) into columns (`last_payment`, `payment_minus_1`) to compare them in a single row.

**Why this is "The CRED Query"**:
- CRED focuses on high-trust users. A high-trust user doesn't default overnight; they "slip".
- This query specifically finds that "slip" moment: `On Time` -> `On Time` -> `On Time` -> `LATE`.
- This is the highest ROI segment for intervention because they have the capacity to pay but might have just forgotten.

---

## 4. Recovery Rate (`sql/queries/recovery_rate.sql`)

**Concept**: Cure Rate Analysis
**Goal**: Estimate cash flow from delinquent accounts.

**Key Techniques**:
- **Date Differences**: `DATEDIFF(actual_paid_date, due_date)` to measure the "Days to Pay".
- **Bucketing**: Grouping days into bins (0-7 days, 8-30 days, 30+ days).

**Interpretation**:
- If `recovery_rate_7d_pct` is 80%, it means 80% of people who miss a due date will pay within a week without much chasing.
- This tells the Ops team: "Don't panic until Day 8."
