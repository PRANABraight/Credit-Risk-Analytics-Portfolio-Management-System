# Interview Guide: The STAR Method

**Project**: Credit Risk Stratification & Repayment Cohort Analysis
**Role**: Operations Analyst @ CRED

---

## 1. The "Elevator Pitch" (30 Seconds)
> "I built an end-to-end credit risk analysis system using Python, MySQL, and Tableau. I analyzed customer repayment behaviors to identify risk segments and operational bottlenecks. By using cohort analysis and window functions, I moved beyond simple default rates to understand *payment velocity*—how quickly customers pay back over time. The final output is a dashboard that segments users into 4 risk tiers, allowing operations teams to prioritize interventions."

---

## 2. STAR Responses (Deep Dives)

### Situation (The Context)
"In fintech operations, the biggest challenge isn't just predicting who will default, but knowing *when* to intervene. Generic credit scores (like CIBIL) are lagging indicators. I wanted to build a leading indicator system that detects behavioral changes before a default happens."

### Task (The Challenge)
"My goal was to analyze a dataset of loan applications and payment histories to answer three operational questions:
1. Are newer customer cohorts riskier than older ones?
2. Which customers are showing early warning signs of 'slipping'?
3. What is the recovery rate for missed payments after 7 days?"

### Action (The Technical Execution)
**Data Engineering**:
- "I set up a MySQL database with a normalized 3-table schema (Customers, Loans, Repayments) to handle the many-to-one relationships."
- "I used Python for ETL to clean the data, handling missing income values by imputing medians based on employment type."

**Advanced SQL**:
- "I didn't just use `GROUP BY`. I used **Window Functions** (`LAG`, `ROW_NUMBER`) to track payment streaks."
- "For the Cohort Analysis, I used `DATE_FORMAT` and self-joins to track how a specific vintage of customers performed over months 1 through 24."

**Visualization**:
- "I built a Tableau dashboard with a 'Risk Matrix' scatter plot (Credit Score vs. Debt-to-Income) to visually cluster high-risk users."

### Result (The Impact)
- "The analysis successfully segmented the portfolio into 4 clear risk tiers."
- "I found a counter-intuitive insight: Customers with 'Self-Employed' status actually had a *faster* recovery rate (paid within 3 days of missing) compared to 'Salaried' employees who missed payments."
- "The 'Early Warning' query identified ~5% of 'Prime' customers who had missed their most recent payment, a critical segment for soft operational outreach."

---

## 3. Technical Questions & Answers

**Q: Why did you use a relational database instead of just Pandas?**
A: "While Pandas is great for exploration, SQL is the language of operations. In a real CRED environment, data lives in warehouses like Redshift or Snowflake. I wanted to demonstrate that I can write optimized queries (using indexes and CTEs) that scale to millions of rows, which is essential for an Ops Analyst role."

**Q: How did you handle the Cohort Analysis?**
A: "I grouped customers by their `account_created_date` (the cohort) and then calculated the `months_since_acquisition` for every payment. This allows us to compare apples-to-apples: 'How did Jan 2023 customers perform in their 3rd month vs. how Feb 2023 customers performed in their 3rd month?'"

**Q: What would you do differently with more data?**
A: "I would add a 'Behavioral Score' that updates in real-time based on app interactions (e.g., checking balance, contacting support). This would improve the predictive power of the risk tiers."

---

## 4. SQL "Whiteboard" Explanations

**The "Slipping Customer" Logic:**
```sql
-- I used LAG() to look back at previous rows
LAG(payment_status, 1) OVER (PARTITION BY customer_id ORDER BY due_date)
```
"This allows me to say: 'If the previous 3 payments were ON TIME, but the current one is LATE, flag this customer.'"

**The Cohort Logic:**
```sql
-- Calculating vintage
TIMESTAMPDIFF(MONTH, account_created_date, due_date)
```
"This normalizes the timeline so we can compare customers who joined at different times."
