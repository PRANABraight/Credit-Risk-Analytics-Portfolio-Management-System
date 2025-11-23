"""
KPI Models and Metrics for Operational Analytics
Tracks key business metrics including user activity, process efficiency, and performance trends
"""

-- ============================================================================
-- 1. DAILY OPERATIONAL KPIs
-- ============================================================================

-- Daily Activity Metrics
CREATE OR REPLACE VIEW vw_daily_kpis AS
SELECT 
    DATE(actual_paid_date) AS activity_date,
    COUNT(DISTINCT rh.loan_id) AS active_loans,
    COUNT(*) AS total_payments,
    SUM(CASE WHEN payment_status = 'On Time' THEN 1 ELSE 0 END) AS on_time_payments,
    SUM(CASE WHEN payment_status = 'Late' THEN 1 ELSE 0 END) AS late_payments,
    SUM(CASE WHEN payment_status = 'Missed' THEN 1 ELSE 0 END) AS missed_payments,
    SUM(amount_paid) AS total_revenue,
    AVG(days_past_due) AS avg_days_past_due,
    -- Performance Trend
    ROUND(100.0 * SUM(CASE WHEN payment_status = 'On Time' THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_rate_pct
FROM repayment_history rh
WHERE actual_paid_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAYS)
GROUP BY DATE(actual_paid_date)
ORDER BY activity_date DESC;

-- ============================================================================
-- 2. PROCESS EFFICIENCY METRICS
-- ============================================================================

-- Collection Efficiency (Time to collect after due date)
CREATE OR REPLACE VIEW vw_collection_efficiency AS
SELECT 
    CASE 
        WHEN days_past_due = 0 THEN 'On Time'
        WHEN days_past_due BETWEEN 1 AND 7 THEN '1-7 Days'
        WHEN days_past_due BETWEEN 8 AND 30 THEN '8-30 Days'
        WHEN days_past_due > 30 THEN '30+ Days'
    END AS collection_bucket,
    COUNT(*) AS payment_count,
    SUM(amount_paid) AS total_collected,
    AVG(days_past_due) AS avg_collection_time,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct_of_total
FROM repayment_history
WHERE actual_paid_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAYS)
GROUP BY collection_bucket
ORDER BY 
    CASE collection_bucket
        WHEN 'On Time' THEN 1
        WHEN '1-7 Days' THEN 2
        WHEN '8-30 Days' THEN 3
        WHEN '30+ Days' THEN 4
    END;

-- ============================================================================
-- 3. USER ACTIVITY TRACKING
-- ============================================================================

-- Customer Engagement Score (based on payment behavior)
CREATE OR REPLACE VIEW vw_customer_engagement AS
WITH customer_metrics AS (
    SELECT 
        cp.customer_id,
        cp.credit_score,
        cp.employment_type,
        COUNT(rh.payment_id) AS total_payments,
        SUM(CASE WHEN rh.payment_status = 'On Time' THEN 1 ELSE 0 END) AS on_time_count,
        AVG(rh.days_past_due) AS avg_delay,
        MAX(rh.actual_paid_date) AS last_payment_date,
        DATEDIFF(CURDATE(), MAX(rh.actual_paid_date)) AS days_since_last_payment
    FROM customer_profile cp
    JOIN loan_application la ON cp.customer_id = la.customer_id
    JOIN repayment_history rh ON la.loan_id = rh.loan_id
    GROUP BY cp.customer_id, cp.credit_score, cp.employment_type
)
SELECT 
    customer_id,
    credit_score,
    employment_type,
    total_payments,
    on_time_count,
    ROUND(100.0 * on_time_count / total_payments, 2) AS on_time_rate,
    avg_delay,
    days_since_last_payment,
    -- Engagement Score (0-100)
    LEAST(100, GREATEST(0, 
        50 + 
        (on_time_count * 2) - 
        (avg_delay * 5) - 
        (days_since_last_payment * 0.5)
    )) AS engagement_score,
    CASE 
        WHEN days_since_last_payment > 60 THEN 'Inactive'
        WHEN days_since_last_payment > 30 THEN 'At Risk'
        ELSE 'Active'
    END AS activity_status
FROM customer_metrics
ORDER BY engagement_score DESC;

-- ============================================================================
-- 4. PERFORMANCE TRENDS (Week-over-Week)
-- ============================================================================

-- Weekly Performance Comparison
CREATE OR REPLACE VIEW vw_weekly_performance_trends AS
WITH weekly_stats AS (
    SELECT 
        YEARWEEK(actual_paid_date) AS year_week,
        DATE(DATE_SUB(actual_paid_date, INTERVAL WEEKDAY(actual_paid_date) DAY)) AS week_start,
        COUNT(*) AS total_payments,
        SUM(CASE WHEN payment_status = 'On Time' THEN 1 ELSE 0 END) AS on_time_payments,
        SUM(amount_paid) AS total_revenue,
        AVG(days_past_due) AS avg_days_late
    FROM repayment_history
    WHERE actual_paid_date >= DATE_SUB(CURDATE(), INTERVAL 12 WEEK)
    GROUP BY year_week, week_start
),
trends AS (
    SELECT 
        *,
        LAG(total_payments) OVER (ORDER BY year_week) AS prev_week_payments,
        LAG(total_revenue) OVER (ORDER BY year_week) AS prev_week_revenue,
        LAG(on_time_payments) OVER (ORDER BY year_week) AS prev_week_on_time
    FROM weekly_stats
)
SELECT 
    week_start,
    total_payments,
    on_time_payments,
    ROUND(100.0 * on_time_payments / total_payments, 2) AS on_time_rate,
    total_revenue,
    avg_days_late,
    -- Week-over-Week Changes
    ROUND(100.0 * (total_payments - prev_week_payments) / NULLIF(prev_week_payments, 0), 2) AS wow_payment_change_pct,
    ROUND(100.0 * (total_revenue - prev_week_revenue) / NULLIF(prev_week_revenue, 0), 2) AS wow_revenue_change_pct,
    ROUND(100.0 * (on_time_payments - prev_week_on_time) / NULLIF(prev_week_on_time, 0), 2) AS wow_on_time_change_pct
FROM trends
WHERE prev_week_payments IS NOT NULL
ORDER BY week_start DESC;

-- ============================================================================
-- 5. EXECUTIVE SUMMARY KPIs (Single Row Dashboard)
-- ============================================================================

CREATE OR REPLACE VIEW vw_executive_kpis AS
SELECT 
    -- Portfolio Overview
    (SELECT COUNT(DISTINCT customer_id) FROM customer_profile) AS total_customers,
    (SELECT COUNT(*) FROM loan_application WHERE loan_status = 'Approved') AS active_loans,
    (SELECT SUM(loan_amount) FROM loan_application) AS total_portfolio_value,
    
    -- Current Month Performance
    (SELECT COUNT(*) FROM repayment_history 
     WHERE MONTH(actual_paid_date) = MONTH(CURDATE()) 
     AND YEAR(actual_paid_date) = YEAR(CURDATE())) AS mtd_payments,
    
    (SELECT SUM(amount_paid) FROM repayment_history 
     WHERE MONTH(actual_paid_date) = MONTH(CURDATE()) 
     AND YEAR(actual_paid_date) = YEAR(CURDATE())) AS mtd_revenue,
    
    -- Quality Metrics
    (SELECT ROUND(100.0 * SUM(CASE WHEN payment_status = 'On Time' THEN 1 ELSE 0 END) / COUNT(*), 2)
     FROM repayment_history 
     WHERE actual_paid_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAYS)) AS on_time_rate_30d,
    
    (SELECT ROUND(AVG(days_past_due), 1)
     FROM repayment_history 
     WHERE actual_paid_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAYS)) AS avg_delay_30d,
    
    -- Risk Indicators
    (SELECT COUNT(DISTINCT customer_id) 
     FROM customer_profile cp
     JOIN loan_application la ON cp.customer_id = la.customer_id
     JOIN repayment_history rh ON la.loan_id = rh.loan_id
     WHERE rh.days_past_due > 30
     AND rh.actual_paid_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAYS)) AS high_risk_customers,
    
    -- Growth Metrics
    (SELECT COUNT(*) FROM loan_application 
     WHERE MONTH(application_date) = MONTH(CURDATE()) 
     AND YEAR(application_date) = YEAR(CURDATE())) AS new_loans_mtd,
    
    CURDATE() AS report_date;
