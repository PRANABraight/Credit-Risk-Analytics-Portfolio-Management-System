"""
Quick Data Insights Generator
Runs SQL queries and displays key findings from your credit risk data
"""

import pymysql
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def run_query(cursor, query, description):
    """Run a query and display results"""
    print(f"\n{description}")
    print("-" * 70)
    cursor.execute(query)
    results = cursor.fetchall()
    
    if not results:
        print("No results found.")
        return
    
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    
    # Print header
    header = " | ".join(f"{col:15s}" for col in columns)
    print(header)
    print("-" * len(header))
    
    # Print rows (limit to 10)
    for i, row in enumerate(results[:10]):
        formatted_row = []
        for val in row:
            if isinstance(val, float):
                formatted_row.append(f"{val:15.2f}")
            elif isinstance(val, int):
                formatted_row.append(f"{val:15,d}")
            else:
                formatted_row.append(f"{str(val):15s}")
        print(" | ".join(formatted_row))
    
    if len(results) > 10:
        print(f"\n... and {len(results) - 10} more rows")
    
    print(f"\nTotal rows: {len(results)}")

def main():
    print_section("CREDIT RISK DATA INSIGHTS")
    
    # Connect to database
    print("\nConnecting to database...")
    conn = pymysql.connect(**config.get_db_config())
    cursor = conn.cursor()
    print("Connected!")
    
    # 1. Portfolio Overview
    print_section("1. PORTFOLIO OVERVIEW")
    
    run_query(cursor, """
        SELECT 
            COUNT(DISTINCT customer_id) as total_customers,
            COUNT(DISTINCT loan_id) as total_loans,
            ROUND(AVG(credit_score), 0) as avg_credit_score,
            ROUND(AVG(age), 1) as avg_age
        FROM customer_profile
        JOIN loan_application USING(customer_id)
    """, "Basic Statistics")
    
    run_query(cursor, """
        SELECT 
            loan_type,
            COUNT(*) as loan_count,
            ROUND(AVG(loan_amount), 2) as avg_amount,
            ROUND(SUM(loan_amount), 2) as total_amount
        FROM loan_application
        GROUP BY loan_type
        ORDER BY loan_count DESC
    """, "Loans by Type")
    
    # 2. Payment Performance
    print_section("2. PAYMENT PERFORMANCE")
    
    run_query(cursor, """
        SELECT 
            payment_status,
            COUNT(*) as payment_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM repayment_history
        GROUP BY payment_status
        ORDER BY payment_count DESC
    """, "Payment Status Distribution")
    
    run_query(cursor, """
        SELECT 
            ROUND(AVG(days_past_due), 1) as avg_days_late,
            MAX(days_past_due) as max_days_late,
            ROUND(AVG(CASE WHEN payment_status = 'On Time' THEN 1 ELSE 0 END) * 100, 2) as on_time_rate
        FROM repayment_history
    """, "Overall Performance Metrics")
    
    # 3. Risk Analysis
    print_section("3. RISK ANALYSIS")
    
    run_query(cursor, """
        SELECT 
            CASE 
                WHEN credit_score >= 700 THEN 'Prime'
                WHEN credit_score >= 650 THEN 'Standard'
                WHEN credit_score >= 600 THEN 'Subprime'
                ELSE 'High Risk'
            END as risk_tier,
            COUNT(DISTINCT customer_id) as customer_count,
            ROUND(AVG(credit_score), 0) as avg_score
        FROM customer_profile
        GROUP BY risk_tier
        ORDER BY avg_score DESC
    """, "Customer Risk Tiers")
    
    run_query(cursor, """
        SELECT 
            cp.customer_id,
            cp.credit_score,
            cp.employment_type,
            COUNT(CASE WHEN rh.payment_status = 'Missed' THEN 1 END) as missed_payments,
            COUNT(CASE WHEN rh.payment_status = 'Late' THEN 1 END) as late_payments,
            ROUND(AVG(rh.days_past_due), 1) as avg_days_late
        FROM customer_profile cp
        JOIN loan_application la USING(customer_id)
        JOIN repayment_history rh USING(loan_id)
        GROUP BY cp.customer_id, cp.credit_score, cp.employment_type
        HAVING missed_payments > 0
        ORDER BY missed_payments DESC, avg_days_late DESC
        LIMIT 10
    """, "Top 10 High-Risk Customers")
    
    # 4. Cohort Insights
    print_section("4. COHORT INSIGHTS")
    
    run_query(cursor, """
        SELECT 
            DATE_FORMAT(account_created_date, '%Y-%m') as cohort_month,
            COUNT(DISTINCT customer_id) as customers,
            ROUND(AVG(credit_score), 0) as avg_credit_score
        FROM customer_profile
        GROUP BY cohort_month
        ORDER BY cohort_month DESC
        LIMIT 6
    """, "Customer Cohorts by Month")
    
    # 5. Operational Metrics
    print_section("5. OPERATIONAL METRICS")
    
    run_query(cursor, """
        SELECT 
            employment_type,
            COUNT(DISTINCT customer_id) as customers,
            ROUND(AVG(income), 2) as avg_income,
            ROUND(AVG(credit_score), 0) as avg_credit_score
        FROM customer_profile
        GROUP BY employment_type
        ORDER BY customers DESC
    """, "Customers by Employment Type")
    
    run_query(cursor, """
        SELECT 
            housing_status,
            COUNT(*) as customers,
            ROUND(AVG(credit_score), 0) as avg_credit_score
        FROM customer_profile
        GROUP BY housing_status
        ORDER BY customers DESC
    """, "Customers by Housing Status")
    
    # 6. Key Findings Summary
    print_section("6. KEY FINDINGS SUMMARY")
    
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT cp.customer_id) as total_customers,
            COUNT(DISTINCT la.loan_id) as total_loans,
            ROUND(SUM(la.loan_amount), 2) as total_portfolio_value,
            ROUND(AVG(rh.days_past_due), 1) as avg_days_late,
            ROUND(100.0 * SUM(CASE WHEN rh.payment_status = 'On Time' THEN 1 ELSE 0 END) / COUNT(*), 2) as on_time_rate,
            COUNT(CASE WHEN rh.payment_status = 'Missed' THEN 1 END) as total_missed_payments
        FROM customer_profile cp
        JOIN loan_application la USING(customer_id)
        JOIN repayment_history rh USING(loan_id)
    """)
    
    result = cursor.fetchone()
    
    print("\n📊 EXECUTIVE SUMMARY:")
    print(f"  • Total Customers: {result[0]:,}")
    print(f"  • Total Loans: {result[1]:,}")
    print(f"  • Portfolio Value: ${result[2]:,.2f}")
    print(f"  • Average Days Late: {result[3]:.1f} days")
    print(f"  • On-Time Payment Rate: {result[4]:.1f}%")
    print(f"  • Total Missed Payments: {result[5]:,}")
    
    # Close connection
    cursor.close()
    conn.close()
    
    print_section("INSIGHTS COMPLETE")
    print("\nNext steps:")
    print("  1. Use these insights for your Tableau dashboard")
    print("  2. Reference these metrics in your interview")
    print("  3. Run: python scripts/api_server.py to serve this data via API")
    print("  4. Generate Excel report: python scripts/automated_reporting.py --daily")
    print()

if __name__ == "__main__":
    main()
