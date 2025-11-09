"""Database layer for job persistence using SQLite"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager


class Database:
    """SQLite database manager for job queue"""
    
    def __init__(self, db_path: str = "queuectl.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT,
                    next_retry_at TEXT
                )
            """)
            
            # Configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            
            # Workers table (for tracking active workers)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    pid INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    last_heartbeat TEXT NOT NULL
                )
            """)
            
            # Initialize default config
            cursor.execute("""
                INSERT OR IGNORE INTO config (key, value) VALUES
                ('max_retries', '3'),
                ('backoff_base', '2')
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper transaction handling"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def create_job(self, job_id: str, command: str, max_retries: int = 3) -> Dict:
        """Create a new job"""
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (id, command, state, attempts, max_retries, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (job_id, command, "pending", 0, max_retries, now, now))
            conn.commit()
        
        return self.get_job(job_id)
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def update_job(self, job_id: str, **kwargs):
        """Update job fields"""
        now = datetime.utcnow().isoformat() + "Z"
        kwargs['updated_at'] = now
        
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [job_id]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE jobs SET {set_clause} WHERE id = ?", values)
            conn.commit()
    
    def get_pending_job(self) -> Optional[Dict]:
        """Get next pending job (with locking)"""
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # First, move failed jobs back to pending if retry time has passed
            cursor.execute("""
                UPDATE jobs 
                SET state = 'pending', next_retry_at = NULL
                WHERE state = 'failed' 
                AND next_retry_at IS NOT NULL 
                AND next_retry_at <= ?
            """, (now,))
            
            # Use row-level locking to prevent duplicate processing
            cursor.execute("""
                SELECT * FROM jobs 
                WHERE state = 'pending' 
                ORDER BY created_at ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                job = dict(row)
                # Lock the job by updating state
                cursor.execute("""
                    UPDATE jobs SET state = 'processing' WHERE id = ?
                """, (job['id'],))
                conn.commit()
                return job
        return None
    
    def list_jobs(self, state: Optional[str] = None) -> List[Dict]:
        """List jobs, optionally filtered by state"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if state:
                cursor.execute("SELECT * FROM jobs WHERE state = ? ORDER BY created_at DESC", (state,))
            else:
                cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_job_stats(self) -> Dict:
        """Get statistics about job states"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT state, COUNT(*) as count 
                FROM jobs 
                GROUP BY state
            """)
            rows = cursor.fetchall()
            stats = {row['state']: row['count'] for row in rows}
            return stats
    
    def get_config(self, key: str, default: str = None) -> str:
        """Get configuration value"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row['value']
        return default
    
    def set_config(self, key: str, value: str):
        """Set configuration value"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)
            """, (key, value))
            conn.commit()
    
    def register_worker(self, worker_id: str, pid: int):
        """Register a worker"""
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO workers (worker_id, pid, started_at, last_heartbeat)
                VALUES (?, ?, ?, ?)
            """, (worker_id, pid, now, now))
            conn.commit()
    
    def update_worker_heartbeat(self, worker_id: str):
        """Update worker heartbeat"""
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workers SET last_heartbeat = ? WHERE worker_id = ?
            """, (now, worker_id))
            conn.commit()
    
    def get_active_workers(self) -> List[Dict]:
        """Get list of active workers"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workers ORDER BY started_at ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def remove_worker(self, worker_id: str):
        """Remove a worker"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM workers WHERE worker_id = ?", (worker_id,))
            conn.commit()

