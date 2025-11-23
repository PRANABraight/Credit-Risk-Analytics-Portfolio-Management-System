-- Risk Stratification: Customer Segmentation
-- Purpose: Segment customers into risk tiers based on historical payment behavior
-- Business Value: Allows operations to prioritize collection efforts on high-risk segments

WITH customer_payment_stats AS (
    -- 1. Aggregate payment history per customer
    SELECT 
        la.customer_id,
        COUNT(rh.payment_id) AS total_payments,
        
        -- Count incidents
        SUM(CASE WHEN rh.payment_status = 'Late' THEN 1 ELSE 0 END) AS late_count,
        SUM(CASE WHEN rh.payment_status = 'Missed' THEN 1 ELSE 0 END) AS missed_count,
        
        -- Calculate average delay
        AVG(CASE WHEN rh.days_past_due > 0 THEN rh.days_past_due ELSE 0 END) AS avg_days_late,
        
        -- Find max delay (worst behavior)
        MAX(rh.days_past_due) AS max_days_late,
        
        -- Recency of bad behavior (Days since last missed payment)
        DATEDIFF(CURRENT_DATE, MAX(CASE WHEN rh.payment_status = 'Missed' THEN rh.due_date ELSE '2000-01-01' END)) AS days_since_last_miss
    FROM repayment_history rh
    JOIN loan_application la ON rh.loan_id = la.loan_id
    WHERE rh.due_date <= CURRENT_DATE
    GROUP BY la.customer_id
),

risk_scoring AS (
    -- 2. Apply business logic to define tiers
    SELECT 
        cp.customer_id,
        cp.credit_score,
        cp.income,
        cps.total_payments,
        cps.avg_days_late,
        cps.missed_count,
        
        CASE 
            -- Tier 1: Prime (Perfect payers)
            WHEN cps.missed_count = 0 AND cps.late_count = 0 THEN 'Tier 1 - Prime'
            
            -- Tier 2: Standard (Occasional minor slips)
            WHEN cps.missed_count = 0 AND cps.avg_days_late <= 7 THEN 'Tier 2 - Standard'
            
            -- Tier 3: Subprime (Frequent late payments or minor misses)
            WHEN cps.missed_count <= 2 OR cps.avg_days_late <= 30 THEN 'Tier 3 - Subprime'
            
            -- Tier 4: High Risk (Serious delinquency)
            ELSE 'Tier 4 - High Risk'
        END AS risk_tier
    FROM customer_profile cp
    JOIN customer_payment_stats cps ON cp.customer_id = cps.customer_id
)

-- 3. Final Output for Dashboard
SELECT 
    risk_tier,
    COUNT(*) AS customer_count,
    ROUND(AVG(credit_score), 0) AS avg_credit_score,
    ROUND(AVG(income), 0) AS avg_income,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM risk_scoring), 2) AS pct_of_portfolio
FROM risk_scoring
GROUP BY risk_tier
ORDER BY risk_tier;
