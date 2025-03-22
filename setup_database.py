"""Database setup script for apartment search application."""
import os
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path

from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize the database with required tables and indexes."""
    logger.info("Setting up database...")
    
    # Validate DB URL
    if not config.DATABASE_URL:
        raise ValueError("DATABASE_URL not found in environment variables")
    
    # Validate SQL file exists
    sql_file_path = Path('create_tables.sql')
    if not sql_file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(config.DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Read and execute SQL file
        with open(sql_file_path, 'r') as file:
            sql_commands = file.read()
            cur.execute(sql_commands)
        
        logger.info("Database setup completed successfully!")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    try:
        setup_database()
        print("Database setup completed successfully!")
    except Exception as e:
        print(f"Setup failed: {e}")
        exit(1)