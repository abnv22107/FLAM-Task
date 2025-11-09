"""Worker process implementation with graceful shutdown"""

import os
import signal
import sys
import time
import threading
import platform
from typing import Optional
from .queue import JobQueue


class Worker:
    """Worker process that processes jobs from the queue"""
    
    def __init__(self, worker_id: str, db_path: str = "queuectl.db"):
        self.worker_id = worker_id
        self.queue = JobQueue(db_path)
        self.running = False
        self.current_job = None
        self.thread = None
        self.pid = os.getpid()
    
    def start(self):
        """Start the worker"""
        self.running = True
        self.queue.db.register_worker(self.worker_id, self.pid)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        if platform.system() != 'Windows':
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start worker loop in a thread
        self.thread = threading.Thread(target=self._work_loop, daemon=False)
        self.thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                self.queue.db.update_worker_heartbeat(self.worker_id)
        except KeyboardInterrupt:
            self.stop()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stop()
    
    def stop(self):
        """Stop the worker gracefully"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for current job to finish (with timeout)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=30)
        
        # Cleanup
        self.queue.db.remove_worker(self.worker_id)
    
    def _work_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                # Get next job
                job = self.queue.get_next_job()
                
                if job:
                    self.current_job = job
                    self.queue.execute_job(job)
                    self.current_job = None
                else:
                    # No jobs available, wait a bit
                    time.sleep(1)
                
                # Update heartbeat
                self.queue.db.update_worker_heartbeat(self.worker_id)
                
            except Exception as e:
                print(f"Worker {self.worker_id} error: {e}", file=sys.stderr)
                time.sleep(1)


class WorkerManager:
    """Manages multiple worker processes"""
    
    def __init__(self, db_path: str = "queuectl.db"):
        self.db_path = db_path
        self.workers = {}
    
    def start_workers(self, count: int):
        """Start multiple worker processes"""
        import multiprocessing
        
        processes = []
        for i in range(count):
            worker_id = f"worker-{os.getpid()}-{i}"
            p = multiprocessing.Process(
                target=self._worker_process,
                args=(worker_id, self.db_path)
            )
            p.start()
            processes.append(p)
            self.workers[worker_id] = p
        
        return processes
    
    @staticmethod
    def _worker_process(worker_id: str, db_path: str):
        """Worker process entry point"""
        worker = Worker(worker_id, db_path)
        try:
            worker.start()
        except Exception as e:
            print(f"Worker {worker_id} failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    def stop_workers(self):
        """Stop all workers gracefully"""
        import multiprocessing
        import platform
        from .database import Database
        
        db = Database(self.db_path)
        active_workers = db.get_active_workers()
        
        for worker_info in active_workers:
            try:
                pid = worker_info['pid']
                if platform.system() == 'Windows':
                    # On Windows, use taskkill or terminate
                    os.kill(pid, signal.SIGTERM if hasattr(signal, 'SIGTERM') else signal.SIGINT)
                else:
                    os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, OSError, AttributeError):
                # Process already dead or signal not available
                pass
        
        # Clean up worker records
        for worker_info in active_workers:
            db.remove_worker(worker_info['worker_id'])
        
        # Wait a bit for graceful shutdown
        time.sleep(2)

