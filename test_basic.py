#!/usr/bin/env python3
"""Basic test to verify queuectl functionality"""

import json
import sys
from queuectl.queue import JobQueue
from queuectl.database import Database

def test_basic():
    """Test basic functionality"""
    print("Testing basic QueueCTL functionality...")
    
    # Clean up
    import os
    if os.path.exists("queuectl.db"):
        os.remove("queuectl.db")
    
    # Test 1: Enqueue job
    print("\n1. Testing job enqueue...")
    queue = JobQueue()
    job = queue.enqueue("test-job-1", "echo Hello World")
    assert job['state'] == 'pending'
    assert job['id'] == 'test-job-1'
    print("   [OK] Job enqueued successfully")
    
    # Test 2: Get job
    print("\n2. Testing job retrieval...")
    job = queue.db.get_job("test-job-1")
    assert job is not None
    assert job['command'] == 'echo Hello World'
    print("   [OK] Job retrieved successfully")
    
    # Test 3: Execute job
    print("\n3. Testing job execution...")
    job = queue.get_next_job()
    assert job is not None
    success = queue.execute_job(job)
    assert success == True
    job = queue.db.get_job("test-job-1")
    assert job['state'] == 'completed'
    print("   [OK] Job executed successfully")
    
    # Test 4: Failed job with retry
    print("\n4. Testing failed job retry...")
    job = queue.enqueue("test-job-2", "exit 1", max_retries=2)
    job = queue.get_next_job()
    success = queue.execute_job(job)
    assert success == False
    job = queue.db.get_job("test-job-2")
    assert job['state'] == 'failed'
    assert job['attempts'] == 1
    print("   [OK] Failed job handled correctly")
    
    # Test 5: Configuration
    print("\n5. Testing configuration...")
    queue.set_config("max_retries", "5")
    value = queue.get_config("max_retries")
    assert value == "5"
    print("   [OK] Configuration works")
    
    # Test 6: DLQ
    print("\n6. Testing DLQ...")
    # Exhaust retries - job already failed once, need 2 more failures to reach max_retries=2
    # But wait, max_retries=2 means it will try 2 times total, so after 1 failure it needs 1 more
    # Actually, attempts starts at 0, so:
    # - First failure: attempts = 1, state = failed
    # - Second failure: attempts = 2, should move to dead (since attempts >= max_retries)
    
    # Get the failed job and execute it again to exhaust retries
    import time
    # Wait a bit for backoff (or just get it if backoff passed)
    time.sleep(3)  # Wait for backoff (2^1 = 2 seconds)
    job = queue.get_next_job()
    if job and job['id'] == 'test-job-2':
        queue.execute_job(job)
    
    job = queue.db.get_job("test-job-2")
    # After second failure, should be in dead state
    if job['state'] != 'dead':
        # If still failed, try one more time
        time.sleep(5)  # Wait for longer backoff
        job = queue.get_next_job()
        if job and job['id'] == 'test-job-2':
            queue.execute_job(job)
        job = queue.db.get_job("test-job-2")
    
    assert job['state'] == 'dead', f"Expected 'dead', got '{job['state']}'"
    dlq_jobs = queue.get_dlq_jobs()
    assert len(dlq_jobs) > 0
    print("   [OK] DLQ works correctly")
    
    # Test 7: Retry from DLQ
    print("\n7. Testing DLQ retry...")
    success = queue.retry_dead_job("test-job-2")
    assert success == True
    job = queue.db.get_job("test-job-2")
    assert job['state'] == 'pending'
    assert job['attempts'] == 0
    print("   [OK] DLQ retry works")
    
    print("\n" + "="*50)
    print("All basic tests passed! [OK]")
    print("="*50)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(test_basic())
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

