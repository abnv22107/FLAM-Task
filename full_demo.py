#!/usr/bin/env python3
"""Complete QueueCTL Demonstration"""

from queuectl.queue import JobQueue
import time

print("=" * 60)
print("QueueCTL Complete Demonstration")
print("=" * 60)

# Initialize
queue = JobQueue()

# 1. Enqueue successful jobs
print("\n1. Enqueueing successful jobs...")
queue.enqueue("success-1", "echo Success Job 1")
queue.enqueue("success-2", "echo Success Job 2")
queue.enqueue("success-3", "echo Success Job 3")
print("   [OK] 3 successful jobs enqueued")

# 2. Enqueue a failed job
print("\n2. Enqueueing a failed job (will retry)...")
queue.enqueue("retry-job", "exit 1", max_retries=2)
print("   [OK] Failed job enqueued (max_retries=2)")

# 3. Process successful jobs
print("\n3. Processing successful jobs...")
for i in range(3):
    job = queue.get_next_job()
    if job and job['id'].startswith('success'):
        print(f"   Processing: {job['id']}")
        queue.execute_job(job)
        print(f"   [OK] {job['id']} completed")

# 4. Process failed job (first attempt)
print("\n4. Processing failed job (first attempt)...")
job = queue.get_next_job()
if job and job['id'] == 'retry-job':
    print(f"   Processing: {job['id']}")
    result = queue.execute_job(job)
    job_after = queue.db.get_job("retry-job")
    print(f"   [FAIL] Job failed (attempt {job_after['attempts']}/{job_after['max_retries']})")
    print(f"   State: {job_after['state']}")

# 5. Wait for backoff and retry
print("\n5. Waiting for backoff (3 seconds)...")
time.sleep(3)

job = queue.get_next_job()
if job and job['id'] == 'retry-job':
    print(f"   Retrying: {job['id']}")
    result = queue.execute_job(job)
    job_after = queue.db.get_job("retry-job")
    print(f"   [FAIL] Job failed again (attempt {job_after['attempts']}/{job_after['max_retries']})")
    if job_after['state'] == 'dead':
        print(f"   [OK] Job moved to DLQ")

# 6. Show statistics
print("\n6. Final Statistics:")
stats = queue.get_stats()
print(f"   Total jobs: {sum(stats['jobs'].values())}")
for state, count in stats['jobs'].items():
    print(f"   {state}: {count}")

# 7. Show DLQ
print("\n7. Dead Letter Queue:")
dlq_jobs = queue.get_dlq_jobs()
print(f"   Jobs in DLQ: {len(dlq_jobs)}")
for job in dlq_jobs:
    error = job.get('error_message', 'N/A')
    if len(error) > 50:
        error = error[:50] + "..."
    print(f"   - {job['id']}: {error}")

# 8. Retry from DLQ
if dlq_jobs:
    print("\n8. Retrying job from DLQ...")
    queue.retry_dead_job("retry-job")
    job_retried = queue.db.get_job("retry-job")
    print(f"   [OK] Job '{job_retried['id']}' reset to pending")
    print(f"   Attempts reset to: {job_retried['attempts']}")

print("\n" + "=" * 60)
print("Demonstration Complete!")
print("=" * 60)
print("\nRun 'python -m queuectl.cli status' to see current state")
print("Run 'python -m queuectl.cli list' to see all jobs")

