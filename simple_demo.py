#!/usr/bin/env python3
"""Simple QueueCTL Demo - Easy to follow"""

from queuectl.queue import JobQueue
import time

print("\n" + "="*70)
print("QueueCTL Simple Demonstration")
print("="*70)

# Clean start
import os
if os.path.exists("queuectl.db"):
    os.remove("queuectl.db")
    print("\n[OK] Cleaned database for fresh start")

queue = JobQueue()

# Step 1: Enqueue successful jobs
print("\n[STEP 1] Enqueueing 3 successful jobs...")
queue.enqueue("job1", "echo Hello from Job 1")
queue.enqueue("job2", "echo Hello from Job 2")
queue.enqueue("job3", "echo Hello from Job 3")
print("   [OK] 3 jobs enqueued")

# Step 2: Show status
print("\n[STEP 2] Current status:")
stats = queue.get_stats()
print(f"   Pending jobs: {stats['jobs'].get('pending', 0)}")

# Step 3: Process jobs
print("\n[STEP 3] Processing jobs...")
for i in range(3):
    job = queue.get_next_job()
    if job:
        print(f"   Processing: {job['id']}")
        result = queue.execute_job(job)
        if result:
            print(f"   [OK] {job['id']} completed successfully")

# Step 4: Show final status
print("\n[STEP 4] Final status:")
stats = queue.get_stats()
print(f"   Completed jobs: {stats['jobs'].get('completed', 0)}")
print(f"   Pending jobs: {stats['jobs'].get('pending', 0)}")

# Step 5: Enqueue failed job
print("\n[STEP 5] Enqueueing a job that will fail...")
queue.enqueue("fail-job", "exit 1", max_retries=2)
print("   [OK] Failed job enqueued (max_retries=2)")

# Step 6: Process failed job
print("\n[STEP 6] Processing failed job (first attempt)...")
job = queue.get_next_job()
if job:
    result = queue.execute_job(job)
    job_after = queue.db.get_job("fail-job")
    print(f"   [FAIL] Job failed (attempt {job_after['attempts']}/{job_after['max_retries']})")
    print(f"   State: {job_after['state']}")

# Step 7: Wait and retry
print("\n[STEP 7] Waiting for backoff (3 seconds)...")
time.sleep(3)
print("   Retrying job...")
job = queue.get_next_job()
if job and job['id'] == 'fail-job':
    result = queue.execute_job(job)
    job_after = queue.db.get_job("fail-job")
    print(f"   [FAIL] Job failed again (attempt {job_after['attempts']}/{job_after['max_retries']})")
    if job_after['state'] == 'dead':
        print("   [OK] Job moved to Dead Letter Queue (DLQ)")

# Step 8: Show DLQ
print("\n[STEP 8] Dead Letter Queue:")
dlq_jobs = queue.get_dlq_jobs()
print(f"   Jobs in DLQ: {len(dlq_jobs)}")
if dlq_jobs:
    for job in dlq_jobs:
        print(f"   - {job['id']}")

# Step 9: Retry from DLQ
if dlq_jobs:
    print("\n[STEP 9] Retrying job from DLQ...")
    queue.retry_dead_job("fail-job")
    job_retried = queue.db.get_job("fail-job")
    print(f"   [OK] Job '{job_retried['id']}' reset to pending")
    print(f"   Attempts reset to: {job_retried['attempts']}")

# Final summary
print("\n" + "="*70)
print("DEMONSTRATION COMPLETE!")
print("="*70)
print("\nNext steps:")
print("  1. Run: python -m queuectl.cli status")
print("  2. Run: python -m queuectl.cli list")
print("  3. Run: python -m queuectl.cli dlq list")
print("  4. Run: python -m queuectl.cli config get")
print("\n")

