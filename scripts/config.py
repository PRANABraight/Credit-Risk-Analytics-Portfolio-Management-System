"""
Configuration module for loading environment variables
Handles database credentials and API keys securely
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration class for database and API credentials"""
    
    # MySQL Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    # Sanitize database name (replace hyphens with underscores to avoid SQL syntax errors)
    DB_NAME = os.getenv('DB_NAME', 'credit_risk_db').replace('-', '_')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # Kaggle API Configuration (optional)
    KAGGLE_USERNAME = os.getenv('KAGGLE_USERNAME', '')
    KAGGLE_KEY = os.getenv('KAGGLE_KEY', '')
    
    @classmethod
    def get_db_config(cls) -> dict:
        """
        Returns database configuration as a dictionary
        
        Returns:
            dict: Database connection parameters
        """
        return {
            'host': cls.DB_HOST,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
            'port': cls.DB_PORT
        }
    
    @classmethod
    def validate_db_config(cls) -> bool:
        """
        Validates that required database configuration is present
        
        Returns:
            bool: True if configuration is valid
        """
        if not cls.DB_PASSWORD:
            print("⚠️  Warning: DB_PASSWORD is empty. Update your .env file.")
            return False
        
        return True
    
    @classmethod
    def validate_kaggle_config(cls) -> bool:
        """
        Validates that Kaggle API credentials are present
        
        Returns:
            bool: True if Kaggle credentials are configured
        """
        return bool(cls.KAGGLE_USERNAME and cls.KAGGLE_KEY)


# Create a singleton instance
config = Config()


if __name__ == "__main__":
    # Test configuration loading
    print("=" * 60)
    print("CONFIGURATION TEST")
    print("=" * 60)
    
    print(f"\nDatabase Configuration:")
    print(f"  Host: {config.DB_HOST}")
    print(f"  User: {config.DB_USER}")
    print(f"  Password: {'*' * len(config.DB_PASSWORD) if config.DB_PASSWORD else '(empty)'}")
    print(f"  Database: {config.DB_NAME}")
    print(f"  Port: {config.DB_PORT}")
    
    print(f"\nKaggle Configuration:")
    print(f"  Username: {config.KAGGLE_USERNAME or '(not set)'}")
    print(f"  API Key: {'*' * 20 if config.KAGGLE_KEY else '(not set)'}")
    
    print(f"\nValidation:")
    print(f"  DB Config Valid: {config.validate_db_config()}")
    print(f"  Kaggle Config Valid: {config.validate_kaggle_config()}")
