# SQL Query Cheat Sheet for CRED Interview

Quick reference for the most important SQL concepts used in this project.

---

## 1. Common Table Expressions (CTEs)

**Purpose**: Break complex queries into readable steps

```sql
WITH customer_cohorts AS (
    SELECT 
        customer_id,
        DATE_FORMAT(account_created_date, '%Y-%m-01') AS cohort_month
    FROM customer_profile
)
SELECT * FROM customer_cohorts;
```

**Interview Tip**: "I used CTEs to make my queries modular and easier to debug. Each CTE represents a logical step in the analysis."

---

## 2. Window Functions

### ROW_NUMBER() - Rank rows within a partition

```sql
SELECT 
    customer_id,
    payment_status,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY due_date DESC) AS payment_rank
FROM repayment_history;
```

**Use Case**: "I used ROW_NUMBER to identify the most recent payment for each customer."

### LAG() - Access previous row's value

```sql
SELECT 
    customer_id,
    payment_status,
    LAG(payment_status, 1) OVER (PARTITION BY customer_id ORDER BY due_date) AS prev_payment
FROM repayment_history;
```

**Use Case**: "LAG helped me detect behavioral changes by comparing current vs. previous payment status."

---

## 3. Conditional Aggregation

```sql
SELECT 
    customer_id,
    COUNT(*) AS total_payments,
    SUM(CASE WHEN payment_status = 'On Time' THEN 1 ELSE 0 END) AS on_time_count,
    SUM(CASE WHEN payment_status = 'Late' THEN 1 ELSE 0 END) AS late_count
FROM repayment_history
GROUP BY customer_id;
```

**Interview Tip**: "Instead of multiple queries, I used CASE WHEN to calculate multiple metrics in one pass."

---

## 4. Date Functions

### TIMESTAMPDIFF - Calculate months between dates

```sql
SELECT 
    customer_id,
    TIMESTAMPDIFF(MONTH, account_created_date, CURRENT_DATE) AS months_on_book
FROM customer_profile;
```

### DATE_FORMAT - Truncate to month

```sql
SELECT 
    DATE_FORMAT(account_created_date, '%Y-%m-01') AS cohort_month
FROM customer_profile;
```

---

## 5. JOINs for Relational Analysis

```sql
SELECT 
    cp.customer_id,
    cp.credit_score,
    la.loan_amount,
    rh.payment_status
FROM customer_profile cp
JOIN loan_application la ON cp.customer_id = la.customer_id
JOIN repayment_history rh ON la.loan_id = rh.loan_id
WHERE rh.payment_status = 'Late';
```

**Interview Tip**: "I designed a normalized schema with foreign keys to demonstrate understanding of relational databases."

---

## 6. Subqueries for Percentages

```sql
SELECT 
    risk_tier,
    customer_count,
    ROUND(100.0 * customer_count / (SELECT COUNT(*) FROM customer_profile), 2) AS pct_of_total
FROM (
    SELECT 
        CASE WHEN credit_score >= 750 THEN 'Prime' ELSE 'Standard' END AS risk_tier,
        COUNT(*) AS customer_count
    FROM customer_profile
    GROUP BY risk_tier
) AS tier_counts;
```

---

## 7. Performance Optimization

### Use Indexes

```sql
CREATE INDEX idx_customer_credit ON customer_profile(credit_score);
CREATE INDEX idx_payment_status ON repayment_history(payment_status);
```

### Avoid SELECT *

```sql
-- Bad
SELECT * FROM repayment_history;

-- Good
SELECT loan_id, payment_status, days_past_due FROM repayment_history;
```

---

## Interview Questions You Should Be Ready For

**Q: "Why did you use a CTE instead of a subquery?"**
A: "CTEs improve readability and can be referenced multiple times. They also make debugging easier because I can test each CTE independently."

**Q: "How would you optimize this query for 10 million rows?"**
A: "I would add indexes on frequently filtered columns (payment_status, due_date), use EXPLAIN to check the query plan, and consider partitioning the repayment_history table by date."

**Q: "What's the difference between WHERE and HAVING?"**
A: "WHERE filters rows before aggregation, HAVING filters after. For example, WHERE filters individual payments, but HAVING filters customers after we've counted their payments."

---

## Pro Tips for the Interview

1. **Explain Your Thinking**: Don't just write SQL, explain WHY you chose that approach
2. **Mention Trade-offs**: "I used a CTE here for readability, but in production with huge data, I might materialize this as a temp table"
3. **Show Iteration**: "My first version used a subquery, but I refactored to a CTE for better performance"
4. **Business Context**: Always tie technical choices back to business value ("This query helps ops teams prioritize collection calls")
