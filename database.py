"""Database module for the apartment search application."""
import psycopg2
from psycopg2 import pool
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple
from contextlib import contextmanager
from config import config

class DatabaseManager:
    """Database manager with connection pooling."""
    
    def __init__(self, min_connections: int = 1, max_connections: int = 5):
        """Initialize the database manager with a connection pool."""
        self._pool = psycopg2.pool.SimpleConnectionPool(
            min_connections,
            max_connections,
            config.DATABASE_URL
        )
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool and return it when done."""
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self):
        """Get a connection and cursor from the pool and return them when done."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def close(self):
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()


class ListingRepository:
    """Repository for apartment listing data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with a database manager."""
        self.db_manager = db_manager
    
    def save_listing(self, listing_data: Dict[str, Any]) -> int:
        """
        Save a new listing to the database.
        Returns the ID of the inserted listing.
        """
        status = listing_data.get('status', 'new')
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO listings (
                    listing_id, title, price, size, rooms, 
                    location, url, status, description
                ) VALUES (
                    %(listing_id)s, %(title)s, %(price)s, %(size)s, %(rooms)s,
                    %(location)s, %(url)s, %(status)s, %(description)s
                ) RETURNING id
            """, {**listing_data, 'status': status})
            
            return cursor.fetchone()[0]
    
    def listing_exists(self, listing_id: str) -> bool:
        """Check if a listing already exists in the database."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM listings WHERE listing_id = %s)",
                (listing_id,)
            )
            return cursor.fetchone()[0]
    
    def mark_listing_processed(self, listing_id: str) -> None:
        """Mark a listing as processed."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute(
                "UPDATE listings SET processed_at = %s WHERE listing_id = %s",
                (datetime.now(), listing_id)
            )
    
    def mark_listing_error(self, listing_id: str, error_message: str) -> None:
        """Mark a listing as having an error."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute(
                "UPDATE listings SET status = 'error', processed_at = %s, description = %s WHERE listing_id = %s",
                (datetime.now(), f"Error: {error_message}", listing_id)
            )
    
    def get_listings(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get listings, optionally filtered by status."""
        query = "SELECT * FROM listings"
        params = []
        
        if status:
            query += " WHERE status = %s"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]