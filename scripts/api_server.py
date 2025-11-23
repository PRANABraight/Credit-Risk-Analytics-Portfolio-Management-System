"""
Simple API Server - Working Version
Serves KPI data from MySQL database with proper error handling
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import pymysql
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import config

app = FastAPI(
    title="Credit Risk Analytics API",
    description="API for serving KPI data",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Get MySQL database connection"""
    try:
        db_config = config.get_db_config()
        return pymysql.connect(**db_config)
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

@app.get("/")
def root():
    """API health check"""
    return {
        "status": "healthy",
        "service": "Credit Risk Analytics API",
        "version": "1.0.0"
    }

@app.get("/api/v1/test")
def test_database():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customer_profile")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"status": "success", "customer_count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/v1/kpis/executive")
def get_executive_kpis() -> Dict[str, Any]:
    """Get executive summary KPIs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Simple query
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT customer_id) as total_customers,
                COUNT(*) as total_loans,
                SUM(loan_amount) as total_portfolio_value
            FROM loan_application
        """)
        loan_stats = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_payments,
                SUM(CASE WHEN payment_status = 'On Time' THEN 1 ELSE 0 END) as on_time_count,
                ROUND(AVG(days_past_due), 1) as avg_delay
            FROM repayment_history
            WHERE actual_paid_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        payment_stats = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        on_time_rate = round(100.0 * payment_stats['on_time_count'] / payment_stats['total_payments'], 2) if payment_stats['total_payments'] > 0 else 0
        
        return {
            "total_customers": loan_stats['total_customers'],
            "active_loans": loan_stats['total_loans'],
            "total_portfolio_value": float(loan_stats['total_portfolio_value'] or 0),
            "total_payments_30d": payment_stats['total_payments'],
            "on_time_rate_30d": on_time_rate,
            "avg_delay_30d": float(payment_stats['avg_delay'] or 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/v1/kpis/daily")
def get_daily_kpis(days: int = 30) -> List[Dict[str, Any]]:
    """Get daily operational KPIs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute(f"""
            SELECT 
                DATE(actual_paid_date) AS activity_date,
                COUNT(*) AS total_payments,
                SUM(CASE WHEN payment_status = 'On Time' THEN 1 ELSE 0 END) AS on_time_payments,
                SUM(amount_paid) AS total_revenue
            FROM repayment_history
            WHERE actual_paid_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
            GROUP BY DATE(actual_paid_date)
            ORDER BY activity_date DESC
            LIMIT 30
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert Decimal to float
        for row in results:
            if 'total_revenue' in row and row['total_revenue']:
                row['total_revenue'] = float(row['total_revenue'])
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/v1/risk/high-risk-customers")
def get_high_risk_customers(limit: int = 10) -> Dict[str, Any]:
    """Get list of high-risk customers"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute(f"""
            SELECT 
                cp.customer_id,
                cp.credit_score,
                cp.employment_type,
                COUNT(CASE WHEN rh.payment_status = 'Missed' THEN 1 END) AS missed_count,
                MAX(rh.days_past_due) AS max_days_late
            FROM customer_profile cp
            JOIN loan_application la ON cp.customer_id = la.customer_id
            JOIN repayment_history rh ON la.loan_id = rh.loan_id
            WHERE rh.days_past_due > 30
            GROUP BY cp.customer_id, cp.credit_score, cp.employment_type
            HAVING missed_count > 0
            ORDER BY max_days_late DESC, missed_count DESC
            LIMIT {limit}
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "count": len(results),
            "customers": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/v1/stats/payment-distribution")
def get_payment_distribution() -> Dict[str, Any]:
    """Get payment status distribution"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                payment_status,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM repayment_history), 2) as percentage
            FROM repayment_history
            GROUP BY payment_status
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "distribution": results,
            "total_payments": sum(r['count'] for r in results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("Starting Credit Risk Analytics API...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
