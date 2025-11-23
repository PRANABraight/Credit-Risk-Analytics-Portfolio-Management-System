-- Recovery Rate Analysis
-- Purpose: Calculate the probability of recovering a missed payment
-- Business Value: Helps forecast bad debt and set collection team targets

WITH missed_payments AS (
    -- 1. Identify all payments that were ever missed (past due date)
    SELECT 
        payment_id,
        due_date,
        actual_paid_date,
        amount_paid,
        installment_amount,
        DATEDIFF(actual_paid_date, due_date) AS days_to_pay
    FROM repayment_history
    WHERE due_date < CURRENT_DATE
      AND (actual_paid_date > due_date OR actual_paid_date IS NULL)
)

SELECT 
    COUNT(*) AS total_missed_instances,
    
    -- Recovered within 7 days (Cure Rate)
    SUM(CASE WHEN days_to_pay <= 7 THEN 1 ELSE 0 END) AS recovered_7d,
    ROUND(100.0 * SUM(CASE WHEN days_to_pay <= 7 THEN 1 ELSE 0 END) / COUNT(*), 1) AS recovery_rate_7d_pct,
    
    -- Recovered within 30 days
    SUM(CASE WHEN days_to_pay <= 30 THEN 1 ELSE 0 END) AS recovered_30d,
    ROUND(100.0 * SUM(CASE WHEN days_to_pay <= 30 THEN 1 ELSE 0 END) / COUNT(*), 1) AS recovery_rate_30d_pct,
    
    -- Never Recovered (Default)
    SUM(CASE WHEN days_to_pay IS NULL OR days_to_pay > 90 THEN 1 ELSE 0 END) AS defaulted,
    ROUND(100.0 * SUM(CASE WHEN days_to_pay IS NULL OR days_to_pay > 90 THEN 1 ELSE 0 END) / COUNT(*), 1) AS default_rate_pct

FROM missed_payments;
