"""Job queue manager with state management and retry logic"""

import subprocess
import time
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from .database import Database


class JobQueue:
    """Manages job queue operations"""
    
    def __init__(self, db_path: str = "queuectl.db"):
        self.db = Database(db_path)
    
    def enqueue(self, job_id: str, command: str, max_retries: Optional[int] = None) -> Dict:
        """Enqueue a new job"""
        if max_retries is None:
            max_retries = int(self.db.get_config("max_retries", "3"))
        
        # Check if job already exists
        existing = self.db.get_job(job_id)
        if existing:
            raise ValueError(f"Job with id '{job_id}' already exists")
        
        return self.db.create_job(job_id, command, max_retries)
    
    def get_next_job(self) -> Optional[Dict]:
        """Get next job to process"""
        return self.db.get_pending_job()
    
    def execute_job(self, job: Dict) -> bool:
        """Execute a job and return True if successful"""
        job_id = job['id']
        command = job['command']
        
        try:
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Success
                self.db.update_job(
                    job_id,
                    state="completed",
                    completed_at=datetime.utcnow().isoformat() + "Z"
                )
                return True
            else:
                # Failure
                self._handle_job_failure(job, result.stderr or result.stdout or "Command failed")
                return False
                
        except subprocess.TimeoutExpired:
            self._handle_job_failure(job, "Command execution timed out")
            return False
        except Exception as e:
            self._handle_job_failure(job, str(e))
            return False
    
    def _handle_job_failure(self, job: Dict, error_message: str):
        """Handle job failure with retry logic"""
        job_id = job['id']
        attempts = job['attempts'] + 1
        max_retries = job['max_retries']
        
        if attempts >= max_retries:
            # Move to DLQ
            self.db.update_job(
                job_id,
                state="dead",
                attempts=attempts,
                error_message=error_message,
                completed_at=datetime.utcnow().isoformat() + "Z"
            )
        else:
            # Schedule retry with exponential backoff
            backoff_base = float(self.db.get_config("backoff_base", "2"))
            delay_seconds = backoff_base ** attempts
            next_retry = datetime.utcnow() + timedelta(seconds=delay_seconds)
            
            self.db.update_job(
                job_id,
                state="failed",
                attempts=attempts,
                error_message=error_message,
                next_retry_at=next_retry.isoformat() + "Z"
            )
            
            # After backoff delay, move back to pending
            time.sleep(0.1)  # Small delay to ensure DB update
            # The job will be picked up again when next_retry_at is reached
    
    def retry_dead_job(self, job_id: str) -> bool:
        """Retry a job from DLQ"""
        job = self.db.get_job(job_id)
        if not job:
            return False
        
        if job['state'] != 'dead':
            raise ValueError(f"Job {job_id} is not in DLQ (current state: {job['state']})")
        
        # Reset job to pending
        self.db.update_job(
            job_id,
            state="pending",
            attempts=0,
            error_message=None,
            next_retry_at=None,
            completed_at=None
        )
        return True
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        stats = self.db.get_job_stats()
        workers = self.db.get_active_workers()
        
        return {
            "jobs": stats,
            "workers": len(workers),
            "worker_details": workers
        }
    
    def list_jobs(self, state: Optional[str] = None) -> list:
        """List jobs, optionally filtered by state"""
        return self.db.list_jobs(state)
    
    def get_dlq_jobs(self) -> list:
        """Get all jobs in DLQ"""
        return self.db.list_jobs("dead")
    
    def get_config(self, key: str, default: str = None) -> str:
        """Get configuration value"""
        return self.db.get_config(key, default)
    
    def set_config(self, key: str, value: str):
        """Set configuration value"""
        self.db.set_config(key, value)

