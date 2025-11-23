-- Dashboard Data Export
-- Purpose: Consolidate data for Tableau/Power BI
-- Run this to generate the main dataset for visualization

SELECT 
    -- Customer Dimensions
    cp.customer_id,
    cp.age,
    cp.gender,
    cp.income,
    cp.employment_type,
    cp.credit_score,
    CASE 
        WHEN cp.credit_score >= 750 THEN '750+ (Excellent)'
        WHEN cp.credit_score >= 700 THEN '700-749 (Good)'
        WHEN cp.credit_score >= 650 THEN '650-699 (Fair)'
        ELSE '<650 (High Risk)'
    END AS credit_score_bucket,
    
    -- Loan Dimensions
    la.loan_id,
    la.loan_type,
    la.loan_amount,
    la.interest_rate,
    la.loan_status,
    
    -- Payment Metrics (Aggregated)
    COUNT(rh.payment_id) AS total_installments,
    SUM(CASE WHEN rh.payment_status = 'On Time' THEN 1 ELSE 0 END) AS on_time_count,
    SUM(CASE WHEN rh.payment_status = 'Late' THEN 1 ELSE 0 END) AS late_count,
    SUM(CASE WHEN rh.payment_status = 'Missed' THEN 1 ELSE 0 END) AS missed_count,
    MAX(rh.days_past_due) AS max_days_past_due,
    
    -- Calculated Risk Metrics
    ROUND(SUM(CASE WHEN rh.payment_status = 'On Time' THEN 1 ELSE 0 END) / COUNT(rh.payment_id), 2) AS repayment_score,
    
    -- Debt to Income Ratio (Monthly)
    ROUND(la.monthly_installment / (cp.income / 12), 2) AS dti_ratio

FROM customer_profile cp
JOIN loan_application la ON cp.customer_id = la.customer_id
JOIN repayment_history rh ON la.loan_id = rh.loan_id
WHERE la.loan_status = 'Approved'
GROUP BY 
    cp.customer_id, cp.age, cp.gender, cp.income, cp.employment_type, cp.credit_score,
    la.loan_id, la.loan_type, la.loan_amount, la.interest_rate, la.loan_status, la.monthly_installment;
