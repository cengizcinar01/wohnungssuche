import psycopg2
from datetime import datetime
from typing import Dict, List, Optional, Union

class DatabaseHelper:
    def __init__(self):
        from dotenv import load_dotenv
        import os
        
        # Load environment variables
        load_dotenv()
        
        # Get Database URL from environment
        self.DB_URL = os.getenv('DATABASE_URL')
        if not self.DB_URL:
            raise ValueError("DATABASE_URL not found in environment variables")
            
        self.conn = None
        self.cur = None

    def connect(self):
        """Establish database connection"""
        if not self.conn:
            self.conn = psycopg2.connect(self.DB_URL)
            self.cur = self.conn.cursor()

    def disconnect(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cur = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def save_listing(self, listing_data: Dict[str, Union[str, float, int]]) -> int:
        """
        Save a new listing to the database
        Returns the ID of the inserted listing
        """
        self.connect()
        try:
            # Use provided status or default to 'new'
            status = listing_data.get('status', 'new')
            
            # Insert fields including status
            self.cur.execute("""
                INSERT INTO listings (
                    listing_id, title, price, size, rooms, 
                    location, url, status, description
                ) VALUES (
                    %(listing_id)s, %(title)s, %(price)s, %(size)s, %(rooms)s,
                    %(location)s, %(url)s, %(status)s, %(description)s
                ) RETURNING id
            """, {**listing_data, 'status': status})
            
            listing_id = self.cur.fetchone()[0]
            self.conn.commit()
            return listing_id
            
        except Exception as e:
            self.conn.rollback()
            raise e

    def listing_exists(self, listing_id: str) -> bool:
        """Check if a listing already exists in the database"""
        self.connect()
        self.cur.execute("SELECT EXISTS(SELECT 1 FROM listings WHERE listing_id = %s)", (listing_id,))
        return self.cur.fetchone()[0]

    def mark_listing_processed(self, listing_id: str):
        """Mark a listing as processed"""
        self.connect()
        try:
            self.cur.execute("""
                UPDATE listings 
                SET processed_at = %s 
                WHERE listing_id = %s
            """, (datetime.now(), listing_id))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def mark_listing_error(self, listing_id: str, error_message: str):
        """Mark a listing as having an error"""
        self.connect()
        try:
            self.cur.execute("""
                UPDATE listings 
                SET status = 'error', processed_at = %s, description = %s 
                WHERE listing_id = %s
            """, (datetime.now(), f"Error: {error_message}", listing_id))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def close(self):
        """Close the database connection"""
        self.disconnect()