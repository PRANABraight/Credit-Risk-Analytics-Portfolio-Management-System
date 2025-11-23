"""
ETL Pipeline for German Credit Data (UCI Repository)
Simpler dataset - good for quick setup and testing
Updated to use PyMySQL and environment variables for secure credential management
"""

import pandas as pd
import pymysql
from pymysql import Error
import numpy as np
from config import config
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import os
import traceback

# Explicitly load .env file
load_dotenv()


class GermanCreditETL:
    """ETL for German Credit dataset"""
    
    def __init__(self, db_config: dict = None):
        # Use environment variables from .env file if no config provided
        self.db_config = db_config or config.get_db_config()
        self.connection = None
        self.cursor = None
    
    def connect_db(self):
        """Connect to MySQL"""
        try:
            # Connect to server to create DB
            conn = pymysql.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.db_config['database']}`")
            cursor.close()
            conn.close()
            
            # Connect to database
            self.connection = pymysql.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            self.cursor = self.connection.cursor()
            print(f"[OK] Connected to MySQL: {self.db_config['database']}")
            return True
        except Error as e:
            print(f"[ERROR] Error: {e}")
            return False
    
    def create_schema(self):
        """Create 3-table schema"""
        print("\nCreating schema...")
        
        # Drop existing
        for table in ['repayment_history', 'loan_application', 'customer_profile']:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Customer profile
        self.cursor.execute("""
            CREATE TABLE customer_profile (
                customer_id INT PRIMARY KEY,
                age INT,
                gender VARCHAR(10),
                income DECIMAL(12, 2),
                employment_type VARCHAR(50),
                credit_score INT,
                account_created_date DATE,
                housing_status VARCHAR(20),
                job_type VARCHAR(50)
            ) ENGINE=InnoDB
        """)
        
        # Loan application
        self.cursor.execute("""
            CREATE TABLE loan_application (
                loan_id INT PRIMARY KEY,
                customer_id INT,
                loan_amount DECIMAL(12, 2),
                loan_type VARCHAR(50),
                interest_rate DECIMAL(5, 2),
                loan_term_months INT,
                application_date DATE,
                approval_date DATE,
                loan_status VARCHAR(20),
                monthly_installment DECIMAL(12, 2),
                FOREIGN KEY (customer_id) REFERENCES customer_profile(customer_id)
            ) ENGINE=InnoDB
        """)
        
        # Repayment history
        self.cursor.execute("""
            CREATE TABLE repayment_history (
                payment_id INT PRIMARY KEY AUTO_INCREMENT,
                loan_id INT,
                installment_number INT,
                installment_amount DECIMAL(12, 2),
                due_date DATE,
                actual_paid_date DATE,
                amount_paid DECIMAL(12, 2),
                payment_status VARCHAR(20),
                days_past_due INT,
                FOREIGN KEY (loan_id) REFERENCES loan_application(loan_id)
            ) ENGINE=InnoDB
        """)
        
        self.connection.commit()
        print("[OK] Schema created")
    
    def load_and_transform_german_credit(self, csv_file: str = None):
        """Load German Credit data and transform into 3 tables"""
        if csv_file is None:
            # Get path relative to script location
            script_dir = Path(__file__).parent.parent
            csv_file = script_dir / "data" / "processed" / "german_credit.csv"
        
        print(f"\nLoading data from {csv_file}...")
        
        try:
            df = pd.read_csv(csv_file)
        except FileNotFoundError:
            print(f"[ERROR] File not found: {csv_file}")
            print("Please run download_data.py first")
            return
            
        print(f"  Loaded {len(df)} records")
        
        # Generate customer profiles
        customers = self._create_customer_profiles(df)
        self._insert_customers(customers)
        
        # Generate loan applications
        loans = self._create_loan_applications(df)
        self._insert_loans(loans)
        
        # Generate payment history
        payments = self._create_payment_history(df, loans)
        self._insert_payments(payments)
    
    def _create_customer_profiles(self, df):
        """Transform to customer profiles"""
        print("\nCreating customer profiles...")
        
        customers = pd.DataFrame({
            'customer_id': range(1, len(df) + 1),
            'age': df['age'],
            'gender': np.random.choice(['Male', 'Female'], len(df), p=[0.52, 0.48]),
            'income': df['credit_amount'] * np.random.uniform(0.3, 0.6, len(df)),
            'employment_type': df['job'].map({
                1: 'Unemployed', 2: 'Unskilled', 3: 'Skilled', 4: 'Professional'
            }).fillna('Unknown'),
            'credit_score': self._map_german_to_credit_score(df),
            'account_created_date': self._generate_dates(len(df), -365*3, -30),
            'housing_status': df['housing'].map({
                1: 'Rent', 2: 'Own', 3: 'Free'
            }).fillna('Unknown'),
            'job_type': df['job'].map({
                1: 'Unemployed', 2: 'Unskilled', 3: 'Skilled Employee', 4: 'Management'
            }).fillna('Unknown')
        })
        
        # Fill any remaining NaN values
        customers = customers.fillna({
            'age': 30,
            'income': 0,
            'credit_score': 500,
            'employment_type': 'Unknown',
            'housing_status': 'Unknown',
            'job_type': 'Unknown'
        })
        
        return customers
    
    def _create_loan_applications(self, df):
        """Transform to loan applications"""
        print("Creating loan applications...")
        
        loans = pd.DataFrame({
            'loan_id': range(1, len(df) + 1),
            'customer_id': range(1, len(df) + 1),
            'loan_amount': df['credit_amount'],
            'loan_type': df['purpose'].map({
                0: 'Personal', 1: 'Auto', 2: 'Education', 3: 'Home',
                4: 'Business', 5: 'Personal', 6: 'Auto', 7: 'Personal',
                8: 'Education', 9: 'Home', 10: 'Personal'
            }).fillna('Personal'),
            'interest_rate': np.random.uniform(6, 18, len(df)),
            'loan_term_months': df['duration_months'],
            'application_date': self._generate_dates(len(df), -365*2, -60),
            'approval_date': None,
            'loan_status': df['credit_risk'].map({1: 'Approved', 2: 'Approved'}),
            'monthly_installment': None
        })
        
        loans['approval_date'] = pd.to_datetime(loans['application_date']) + \
                                 pd.to_timedelta(np.random.randint(1, 15, len(df)), unit='D')
        
        loans['monthly_installment'] = loans['loan_amount'] / loans['loan_term_months'] * \
                                       (1 + loans['interest_rate'] / 100 / 12)
        
        # Fill any NaN values
        loans = loans.fillna({
            'loan_type': 'Personal',
            'loan_status': 'Approved'
        })
        
        return loans
    
    def _create_payment_history(self, df, loans):
        """Generate payment history for each loan"""
        print("Creating payment history...")
        
        all_payments = []
        
        for idx, loan in loans.iterrows():
            risk = df.iloc[idx]['credit_risk']
            is_good_payer = (risk == 1)
            
            approval_date = pd.to_datetime(loan['approval_date'])
            
            for installment_num in range(1, int(loan['loan_term_months']) + 1):
                due_date = approval_date + timedelta(days=30 * installment_num)
                
                if is_good_payer:
                    status_choice = np.random.choice(
                        ['On Time', 'Late', 'Missed'], p=[0.90, 0.08, 0.02]
                    )
                else:
                    status_choice = np.random.choice(
                        ['On Time', 'Late', 'Missed'], p=[0.50, 0.30, 0.20]
                    )
                
                if status_choice == 'On Time':
                    days_late = np.random.randint(-2, 1)
                elif status_choice == 'Late':
                    days_late = np.random.randint(1, 45)
                else:
                    days_late = np.random.randint(45, 120)
                
                actual_paid_date = due_date + timedelta(days=int(days_late))
                
                if status_choice == 'Missed' and np.random.random() < 0.3:
                    amount_paid = loan['monthly_installment'] * np.random.uniform(0.3, 0.7)
                else:
                    amount_paid = loan['monthly_installment']
                
                all_payments.append({
                    'loan_id': loan['loan_id'],
                    'installment_number': installment_num,
                    'installment_amount': loan['monthly_installment'],
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'actual_paid_date': actual_paid_date.strftime('%Y-%m-%d'),
                    'amount_paid': amount_paid,
                    'payment_status': status_choice,
                    'days_past_due': max(0, days_late)
                })
        
        return pd.DataFrame(all_payments)
    
    def _map_german_to_credit_score(self, df):
        """Convert German data to credit scores"""
        base_score = 500
        
        checking_map = {'A11': 50, 'A12': 30, 'A13': 10, 'A14': -20}
        score_adjustment = df['status_checking_account'].map(checking_map).fillna(0)
        
        history_map = {
            'A30': -50, 'A31': -20, 'A32': 0, 'A33': 20, 'A34': 50
        }
        score_adjustment += df['credit_history'].map(history_map).fillna(0)
        score_adjustment += (df['age'] - 25) * 2
        
        score = base_score + score_adjustment + np.random.normal(100, 50, len(df))
        return score.clip(300, 850).astype(int)
    
    def _generate_dates(self, n, days_min, days_max):
        """Generate random dates"""
        reference = datetime.now()
        random_days = np.random.randint(days_min, days_max, n)
        return [(reference + timedelta(days=int(d))).strftime('%Y-%m-%d') for d in random_days]


    def _insert_customers(self, customers):
        """Insert customers into database"""
        print("\nInserting customer profiles...")
        
        query = """
            INSERT INTO customer_profile 
            (customer_id, age, gender, income, employment_type, credit_score, 
             account_created_date, housing_status, job_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = [tuple(row) for row in customers.values]
        self.cursor.executemany(query, data)
        self.connection.commit()
        print(f"[OK] Inserted {len(data)} customers")
    
    def _insert_loans(self, loans):
        """Insert loans into database"""
        print("Inserting loan applications...")
        
        query = """
            INSERT INTO loan_application 
            (loan_id, customer_id, loan_amount, loan_type, interest_rate, 
             loan_term_months, application_date, approval_date, loan_status, monthly_installment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = [tuple(row) for row in loans.values]
        self.cursor.executemany(query, data)
        self.connection.commit()
        print(f"[OK] Inserted {len(data)} loans")
    
    def _insert_payments(self, payments):
        """Insert payment history"""
        print("Inserting payment history...")
        
        query = """
            INSERT INTO repayment_history 
            (loan_id, installment_number, installment_amount, due_date, 
             actual_paid_date, amount_paid, payment_status, days_past_due)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = [tuple(row) for row in payments.values]
        
        # Insert in batches
        batch_size = 10000
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            self.cursor.executemany(query, batch)
            self.connection.commit()
            print(f"  Inserted {min(i+batch_size, len(data))}/{len(data)} payments")
        
        print(f"[OK] Inserted {len(data)} payment records")
    
    def verify_data(self):
        """Verify loaded data"""
        print("\n" + "=" * 70)
        print("DATA VERIFICATION")
        print("=" * 70)
        
        for table in ['customer_profile', 'loan_application', 'repayment_history']:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"{table}: {count:,} records")
        
        print("\n[OK] ETL Complete!")
    
    def close(self):
        """Close connection"""
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("\n[OK] Connection closed")


def main():
    """Main execution"""
    print("=" * 70)
    print("GERMAN CREDIT ETL PIPELINE")
    print("=" * 70)
    
    # Validate configuration
    if not config.validate_db_config():
        print("\n[WARNING] Please update your .env file with MySQL credentials")
        print("   Copy .env.example to .env and fill in DB_PASSWORD")
        return
    
    try:
        # Use config from environment variables (no hardcoded credentials!)
        etl = GermanCreditETL()
        
        if not etl.connect_db():
            print("\n[ERROR] Connection failed. Update db_config.")
            return
        
        etl.create_schema()
        etl.load_and_transform_german_credit()
        etl.verify_data()
        etl.close()
    except Exception:
        print("\n[FATAL] FATAL ERROR:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
