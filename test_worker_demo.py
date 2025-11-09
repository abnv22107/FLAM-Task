#!/usr/bin/env python3
"""Test worker functionality"""

import time
import sys
from queuectl.queue import JobQueue
from queuectl.worker import Worker

def test_worker():
    """Test worker processing jobs"""
    print("=" * 60)
    print("Worker Functionality Test")
    print("=" * 60)
    
    # Clean up
    import os
    if os.path.exists("queuectl.db"):
        os.remove("queuectl.db")
    
    # Create queue and enqueue jobs
    print("\n1. Enqueueing test jobs...")
    queue = JobQueue()
    
    # Successful job
    queue.enqueue("worker-test-1", "echo Worker Test Success")
    print("   [OK] Job 'worker-test-1' enqueued")
    
    # Another successful job
    queue.enqueue("worker-test-2", "echo Worker Test Success 2")
    print("   [OK] Job 'worker-test-2' enqueued")
    
    # Check initial status
    print("\n2. Initial status:")
    stats = queue.get_stats()
    print(f"   Pending jobs: {stats['jobs'].get('pending', 0)}")
    
    # Process jobs manually (simulating worker)
    print("\n3. Processing jobs (simulating worker)...")
    job1 = queue.get_next_job()
    if job1:
        print(f"   Processing job: {job1['id']}")
        success = queue.execute_job(job1)
        if success:
            print(f"   [OK] Job '{job1['id']}' completed successfully")
        else:
            print(f"   [FAIL] Job '{job1['id']}' failed")
    
    job2 = queue.get_next_job()
    if job2:
        print(f"   Processing job: {job2['id']}")
        success = queue.execute_job(job2)
        if success:
            print(f"   [OK] Job '{job2['id']}' completed successfully")
        else:
            print(f"   [FAIL] Job '{job2['id']}' failed")
    
    # Check final status
    print("\n4. Final status:")
    stats = queue.get_stats()
    print(f"   Completed jobs: {stats['jobs'].get('completed', 0)}")
    print(f"   Pending jobs: {stats['jobs'].get('pending', 0)}")
    
    # Verify jobs are completed
    job1_final = queue.db.get_job("worker-test-1")
    job2_final = queue.db.get_job("worker-test-2")
    
    if job1_final and job1_final['state'] == 'completed':
        print("   [OK] Job 'worker-test-1' is completed")
    else:
        print("   [FAIL] Job 'worker-test-1' not completed")
        return False
    
    if job2_final and job2_final['state'] == 'completed':
        print("   [OK] Job 'worker-test-2' is completed")
    else:
        print("   [FAIL] Job 'worker-test-2' not completed")
        return False
    
    print("\n" + "=" * 60)
    print("[OK] Worker functionality test passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_worker()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

