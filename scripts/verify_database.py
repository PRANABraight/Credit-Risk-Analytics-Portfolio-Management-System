"""
Database Verification Script
Run this to check if your database is set up correctly
"""

import pymysql
from config import config
from tabulate import tabulate


def verify_database():
    """Comprehensive database verification"""
    
    print("=" * 70)
    print("DATABASE VERIFICATION SCRIPT")
    print("=" * 70)
    
    # Check configuration
    print("\n1. Checking Configuration...")
    if not config.validate_db_config():
        print("   ✗ Configuration invalid. Please update .env file.")
        return False
    print("   ✓ Configuration valid")
    
    # Try to connect
    print("\n2. Testing Database Connection...")
    try:
        conn = pymysql.connect(**config.get_db_config())
        cursor = conn.cursor()
        print("   ✓ Successfully connected to MySQL")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False
    
    # Check if database exists
    print("\n3. Checking Database...")
    cursor.execute(f"SHOW DATABASES LIKE '{config.DB_NAME}'")
    if cursor.fetchone():
        print(f"   ✓ Database '{config.DB_NAME}' exists")
    else:
        print(f"   ✗ Database '{config.DB_NAME}' not found")
        print("   → Run: python scripts/etl_german_credit.py")
        return False
    
    # Check tables
    print("\n4. Checking Tables...")
    cursor.execute(f"USE {config.DB_NAME}")
    
    required_tables = ['customer_profile', 'loan_application', 'repayment_history']
    all_tables_exist = True
    
    for table in required_tables:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        if cursor.fetchone():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✓ {table}: {count:,} records")
        else:
            print(f"   ✗ {table}: NOT FOUND")
            all_tables_exist = False
    
    if not all_tables_exist:
        print("\n   → Run: python scripts/etl_german_credit.py")
        return False
    
    # Sample data quality checks
    print("\n5. Data Quality Checks...")
    
    # Check for NULL values in critical columns
    cursor.execute("""
        SELECT COUNT(*) FROM customer_profile 
        WHERE customer_id IS NULL OR credit_score IS NULL
    """)
    null_count = cursor.fetchone()[0]
    if null_count == 0:
        print("   ✓ No NULL values in critical customer columns")
    else:
        print(f"   ⚠️  Found {null_count} NULL values in customer data")
    
    # Check credit score range
    cursor.execute("""
        SELECT MIN(credit_score), MAX(credit_score), AVG(credit_score)
        FROM customer_profile
    """)
    min_score, max_score, avg_score = cursor.fetchone()
    if 300 <= min_score and max_score <= 850:
        print(f"   ✓ Credit scores in valid range: {min_score}-{max_score} (avg: {avg_score:.0f})")
    else:
        print(f"   ⚠️  Credit scores out of range: {min_score}-{max_score}")
    
    # Check payment status distribution
    cursor.execute("""
        SELECT payment_status, COUNT(*) as count
        FROM repayment_history
        GROUP BY payment_status
        ORDER BY count DESC
    """)
    
    print("\n6. Payment Status Distribution:")
    results = cursor.fetchall()
    table_data = [[status, f"{count:,}"] for status, count in results]
    print(tabulate(table_data, headers=["Status", "Count"], tablefmt="simple"))
    
    # Test a sample query
    print("\n7. Testing Sample Query (Risk Tiers)...")
    cursor.execute("""
        SELECT 
            CASE 
                WHEN credit_score >= 750 THEN 'Prime'
                WHEN credit_score >= 650 THEN 'Standard'
                WHEN credit_score >= 550 THEN 'Subprime'
                ELSE 'High Risk'
            END AS risk_tier,
            COUNT(*) as customer_count
        FROM customer_profile
        GROUP BY risk_tier
        ORDER BY customer_count DESC
    """)
    
    results = cursor.fetchall()
    table_data = [[tier, f"{count:,}"] for tier, count in results]
    print(tabulate(table_data, headers=["Risk Tier", "Customers"], tablefmt="simple"))
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ DATABASE VERIFICATION COMPLETE")
    print("=" * 70)
    print("\nYour database is ready for analysis!")
    print("Next steps:")
    print("  1. Run SQL queries: mysql -u root -p credit_risk_db < sql/queries/cohort_analysis.sql")
    print("  2. Build Tableau dashboard using visualization/dashboard_design.md")
    print("  3. Review docs/INTERVIEW_GUIDE.md for presentation prep")
    
    return True


if __name__ == "__main__":
    try:
        verify_database()
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that MySQL is running: net start MySQL80")
        print("  2. Verify .env file has correct DB_PASSWORD")
        print("  3. Run: python scripts/config.py to test configuration")
