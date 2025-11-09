#!/usr/bin/env python3
"""Test retry and DLQ functionality"""

import time
import sys
from queuectl.queue import JobQueue

def test_retry_dlq():
    """Test retry mechanism and DLQ"""
    print("=" * 60)
    print("Retry and DLQ Functionality Test")
    print("=" * 60)
    
    # Clean up
    import os
    if os.path.exists("queuectl.db"):
        os.remove("queuectl.db")
    
    queue = JobQueue()
    
    # Test 1: Failed job with retries
    print("\n1. Testing failed job with retries...")
    queue.enqueue("retry-test-1", "exit 1", max_retries=2)
    print("   [OK] Failed job enqueued (max_retries=2)")
    
    # Execute and fail
    job = queue.get_next_job()
    if job:
        success = queue.execute_job(job)
        assert success == False, "Job should fail"
        job_after = queue.db.get_job("retry-test-1")
        assert job_after['state'] == 'failed', f"Expected 'failed', got '{job_after['state']}'"
        assert job_after['attempts'] == 1, f"Expected 1 attempt, got {job_after['attempts']}"
        print("   [OK] Job failed and moved to 'failed' state")
        print(f"   [OK] Attempts: {job_after['attempts']}, Max Retries: {job_after['max_retries']}")
    
    # Wait for backoff and retry
    print("\n2. Waiting for backoff and retrying...")
    time.sleep(3)  # Wait for backoff (2^1 = 2 seconds)
    
    job = queue.get_next_job()
    if job and job['id'] == 'retry-test-1':
        success = queue.execute_job(job)
        assert success == False, "Job should fail again"
        job_after = queue.db.get_job("retry-test-1")
        print(f"   [OK] Job retried, attempts: {job_after['attempts']}")
        
        # After max retries, should be in DLQ
        if job_after['state'] == 'dead':
            print("   [OK] Job moved to DLQ after exhausting retries")
        else:
            # One more retry needed
            time.sleep(5)
            job = queue.get_next_job()
            if job and job['id'] == 'retry-test-1':
                queue.execute_job(job)
                job_after = queue.db.get_job("retry-test-1")
                assert job_after['state'] == 'dead', f"Expected 'dead', got '{job_after['state']}'"
                print("   [OK] Job moved to DLQ after exhausting retries")
    
    # Test 2: DLQ listing
    print("\n3. Testing DLQ listing...")
    dlq_jobs = queue.get_dlq_jobs()
    assert len(dlq_jobs) > 0, "DLQ should have jobs"
    print(f"   [OK] Found {len(dlq_jobs)} job(s) in DLQ")
    
    # Test 3: Retry from DLQ
    print("\n4. Testing retry from DLQ...")
    success = queue.retry_dead_job("retry-test-1")
    assert success == True, "Should be able to retry from DLQ"
    job_retried = queue.db.get_job("retry-test-1")
    assert job_retried['state'] == 'pending', f"Expected 'pending', got '{job_retried['state']}'"
    assert job_retried['attempts'] == 0, "Attempts should be reset"
    print("   [OK] Job retried from DLQ, reset to pending")
    print(f"   [OK] Attempts reset to: {job_retried['attempts']}")
    
    # Test 4: Configuration
    print("\n5. Testing configuration...")
    queue.set_config("max_retries", "5")
    max_retries = queue.get_config("max_retries")
    assert max_retries == "5", f"Expected '5', got '{max_retries}'"
    print("   [OK] Configuration works")
    
    print("\n" + "=" * 60)
    print("[OK] Retry and DLQ functionality test passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_retry_dlq()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

