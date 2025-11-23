# Tableau Dashboard Design Blueprint

## Dashboard Title: Credit Risk & Operational Intelligence Center
**Target Audience**: Operations Managers, Risk Analysts
**Refresh Frequency**: Daily

---

## Page 1: Executive Overview (The "Morning Coffee" View)

### 1. KPI Header (Top Row)
| Metric | Visualization | Calculation |
|--------|---------------|-------------|
| **Portfolio Health** | Big Number + Sparkline | `1 - (Missed Payments / Total Payments)` |
| **Total Outstanding** | Big Number | `SUM(Loan Amount)` |
| **Delinquency Rate** | Big Number + Indicator (Red/Green) | `% of Loans with Days Past Due > 0` |
| **MoM Growth** | Big Number | `(Current Month Loans - Prev Month) / Prev Month` |

### 2. Cohort Repayment Heatmap (Centerpiece)
- **Chart Type**: Heatmap / Highlight Table
- **Rows**: Acquisition Month (e.g., Jan 2023, Feb 2023...)
- **Columns**: Months Since Acquisition (Month 1, Month 2, Month 3...)
- **Color**: Repayment Rate % (Green = 100%, Red < 90%)
- **Insight**: "Are we acquiring riskier customers lately?" (Look for redder rows at the bottom)

### 3. Risk Tier Distribution (Right Panel)
- **Chart Type**: Donut Chart
- **Segments**: Prime, Standard, Subprime, High Risk
- **Tooltip**: Avg Credit Score, Avg Income per Tier

---

## Page 2: Risk Deep Dive (The "Analyst" View)

### 1. The "Risk Matrix" (Scatter Plot)
- **X-Axis**: Credit Score
- **Y-Axis**: Debt-to-Income Ratio
- **Color**: Risk Tier
- **Size**: Loan Amount
- **Reference Lines**: 
  - Vertical at 750 (Prime Cutoff)
  - Horizontal at 40% DTI (Risk Threshold)

### 2. Delinquency by Loan Type
- **Chart Type**: Horizontal Bar Chart
- **Bars**: Personal, Home, Auto, Education
- **Measure**: % Late Payments
- **Sort**: Descending by Risk

### 3. Payment Velocity Analysis
- **Chart Type**: Line Chart
- **X-Axis**: Days Past Due (0 to 90)
- **Y-Axis**: % of Payments Recovered (Cumulative)
- **Lines**: Compare different Loan Types
- **Insight**: "Auto loans recover faster than Personal loans"

---

## Page 3: Operational Action List (The "Worklist" View)

### 1. High Priority Intervention List
- **Chart Type**: Detailed Table
- **Columns**: 
  - Customer ID
  - Days Past Due
  - Loan Amount
  - Last Contact Date
  - Risk Tier
- **Filter**: `Risk Tier = 'High Risk'` AND `Days Past Due > 0`

### 2. "Slipping" Customers (Early Warning)
- **Chart Type**: Table
- **Logic**: Customers who paid on time for 3 months but missed the most recent payment.
- **Action**: These need "Soft Reminder" emails, not collections calls.

---

## Interactive Filters (Global)
- **Date Range Slider**: Filter by Application Date
- **Employment Type**: Dropdown (Salaried, Self-Employed, etc.)
- **City/Region**: Map selection

## Color Palette (CRED Style)
- **Background**: Dark Mode (#1a1a1a)
- **Primary Accent**: CRED Gold (#f2c94c) or Blue (#2f80ed)
- **Risk Colors**:
  - Low Risk: #27ae60 (Green)
  - Medium Risk: #f2994a (Orange)
  - High Risk: #eb5757 (Red)
