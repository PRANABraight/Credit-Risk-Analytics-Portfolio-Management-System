-- Operational Bottleneck: Early Warning System
-- Purpose: Identify customers showing specific deterioration patterns
-- Business Value: "The CRED Query" - finding high-trust users who are slipping

WITH payment_sequence AS (
    -- 1. Number payments sequentially for each customer
    SELECT 
        la.customer_id,
        rh.due_date,
        rh.payment_status,
        ROW_NUMBER() OVER (PARTITION BY la.customer_id ORDER BY rh.due_date DESC) AS payment_rank_desc
    FROM repayment_history rh
    JOIN loan_application la ON rh.loan_id = la.loan_id
    WHERE rh.due_date <= CURRENT_DATE
),

recent_behavior AS (
    -- 2. Pivot the last 4 payments to columns
    SELECT 
        customer_id,
        MAX(CASE WHEN payment_rank_desc = 1 THEN payment_status END) AS last_payment,
        MAX(CASE WHEN payment_rank_desc = 2 THEN payment_status END) AS payment_minus_1,
        MAX(CASE WHEN payment_rank_desc = 3 THEN payment_status END) AS payment_minus_2,
        MAX(CASE WHEN payment_rank_desc = 4 THEN payment_status END) AS payment_minus_3
    FROM payment_sequence
    WHERE payment_rank_desc <= 4
    GROUP BY customer_id
)

-- 3. Identify the "Slipping" Pattern
-- Pattern: Was good (On Time) for previous 3 months, but missed/late most recently
SELECT 
    rb.customer_id,
    cp.credit_score,
    cp.employment_type,
    rb.last_payment AS current_status,
    'Deteriorating' AS risk_flag
FROM recent_behavior rb
JOIN customer_profile cp ON rb.customer_id = cp.customer_id
WHERE 
    -- The "Good" History
    rb.payment_minus_1 = 'On Time' AND
    rb.payment_minus_2 = 'On Time' AND
    rb.payment_minus_3 = 'On Time'
    -- The "Bad" Recent Event
    AND rb.last_payment IN ('Late', 'Missed')
ORDER BY cp.credit_score DESC;
