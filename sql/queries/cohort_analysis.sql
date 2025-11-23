-- Cohort Analysis: Repayment Rates by Acquisition Month
-- Purpose: Analyze how repayment behavior changes for different customer vintages
-- Business Value: Identifies if newer customers are riskier than older ones (Vintage Analysis)

WITH customer_cohorts AS (
    -- 1. Define cohorts based on when the customer joined (Account Created Date)
    SELECT 
        customer_id,
        DATE_FORMAT(account_created_date, '%Y-%m-01') AS cohort_month
    FROM customer_profile
),

payment_performance AS (
    -- 2. Calculate performance for each payment
    SELECT 
        rh.loan_id,
        la.customer_id,
        rh.due_date,
        -- Calculate which "month on book" this payment represents
        TIMESTAMPDIFF(MONTH, cp.account_created_date, rh.due_date) AS months_since_acquisition,
        
        -- Define success metric (Paid on time or within grace period)
        CASE 
            WHEN rh.payment_status = 'On Time' THEN 1
            WHEN rh.days_past_due <= 7 THEN 1  -- 7 day grace period
            ELSE 0
        END AS is_successful_payment
    FROM repayment_history rh
    JOIN loan_application la ON rh.loan_id = la.loan_id
    JOIN customer_profile cp ON la.customer_id = cp.customer_id
    WHERE rh.due_date <= CURRENT_DATE
)

-- 3. Aggregate to get cohort performance
SELECT 
    cc.cohort_month,
    pp.months_since_acquisition,
    COUNT(*) AS total_payments_due,
    SUM(pp.is_successful_payment) AS successful_payments,
    
    -- The Key Metric: Repayment Rate %
    ROUND(100.0 * SUM(pp.is_successful_payment) / COUNT(*), 2) AS repayment_rate_pct
FROM customer_cohorts cc
JOIN payment_performance pp ON cc.customer_id = pp.customer_id
WHERE pp.months_since_acquisition >= 0 
  AND pp.months_since_acquisition <= 24 -- Look at first 2 years
GROUP BY cc.cohort_month, pp.months_since_acquisition
ORDER BY cc.cohort_month DESC, pp.months_since_acquisition ASC;
