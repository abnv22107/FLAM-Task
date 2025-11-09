#!/usr/bin/env python3
"""
Interactive manual demo script for QueueCTL
Run this to see a complete demonstration of all features
"""

import time
import sys
from queuectl.queue import JobQueue

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_step(step_num, description):
    """Print a step"""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 70)

def wait_for_user():
    """Wait for user to press Enter"""
    input("\nPress Enter to continue...")

def main():
    """Run the interactive demo"""
    print_section("QueueCTL - Interactive Demo")
    print("\nThis demo will show you all the features of QueueCTL.")
    print("Follow along and watch the job queue in action!")
    
    wait_for_user()
    
    # Clean up
    import os
    if os.path.exists("queuectl.db"):
        response = input("\nDatabase exists. Delete and start fresh? (y/n): ")
        if response.lower() == 'y':
            os.remove("queuectl.db")
            print("Database cleaned!")
    
    queue = JobQueue()
    
    # Step 1: Configuration
    print_step(1, "Viewing Configuration")
    print("\nCurrent configuration:")
    max_retries = queue.get_config("max_retries", "3")
    backoff_base = queue.get_config("backoff_base", "2")
    print(f"  Max Retries: {max_retries}")
    print(f"  Backoff Base: {backoff_base}")
    wait_for_user()
    
    # Step 2: Enqueue successful jobs
    print_step(2, "Enqueueing Successful Jobs")
    print("\nEnqueueing 3 jobs that will succeed...")
    queue.enqueue("demo-success-1", "echo 'Job 1 completed successfully'")
    print("  [OK] Job 'demo-success-1' enqueued")
    queue.enqueue("demo-success-2", "echo 'Job 2 completed successfully'")
    print("  [OK] Job 'demo-success-2' enqueued")
    queue.enqueue("demo-success-3", "echo 'Job 3 completed successfully'")
    print("  [OK] Job 'demo-success-3' enqueued")
    
    stats = queue.get_stats()
    print(f"\nCurrent status: {stats['jobs'].get('pending', 0)} pending jobs")
    wait_for_user()
    
    # Step 3: Process jobs
    print_step(3, "Processing Jobs (Simulating Worker)")
    print("\nProcessing jobs one by one...")
    for i in range(3):
        job = queue.get_next_job()
        if job:
            print(f"\n  Processing: {job['id']}")
            print(f"  Command: {job['command']}")
            success = queue.execute_job(job)
            if success:
                print(f"  [OK] Job '{job['id']}' completed successfully!")
            time.sleep(0.5)
    
    stats = queue.get_stats()
    print(f"\nCurrent status: {stats['jobs'].get('completed', 0)} completed jobs")
    wait_for_user()
    
    # Step 4: Failed job with retries
    print_step(4, "Testing Failed Job with Retries")
    print("\nEnqueueing a job that will fail (max_retries=2)...")
    queue.enqueue("demo-failed", "exit 1", max_retries=2)
    print("  [OK] Failed job 'demo-failed' enqueued")
    
    print("\nProcessing job (will fail)...")
    job = queue.get_next_job()
    if job:
        success = queue.execute_job(job)
        job_after = queue.db.get_job("demo-failed")
        print(f"  [FAIL] Job failed (as expected)")
        print(f"  State: {job_after['state']}")
        print(f"  Attempts: {job_after['attempts']}/{job_after['max_retries']}")
    wait_for_user()
    
    # Step 5: Wait for backoff and retry
    print_step(5, "Waiting for Exponential Backoff")
    backoff_base = float(queue.get_config("backoff_base", "2"))
    attempts = job_after['attempts']
    delay = backoff_base ** attempts
    print(f"\nExponential backoff: base^{attempts} = {backoff_base}^{attempts} = {delay} seconds")
    print(f"Waiting {delay} seconds for retry...")
    
    for i in range(int(delay)):
        print(f"  {i+1}...", end=" ", flush=True)
        time.sleep(1)
    print("\n")
    
    print("Retrying job...")
    job = queue.get_next_job()
    if job and job['id'] == 'demo-failed':
        success = queue.execute_job(job)
        job_after = queue.db.get_job("demo-failed")
        print(f"  State: {job_after['state']}")
        print(f"  Attempts: {job_after['attempts']}/{job_after['max_retries']}")
        
        if job_after['state'] == 'dead':
            print("  [OK] Job moved to Dead Letter Queue (DLQ)")
    wait_for_user()
    
    # Step 6: DLQ
    print_step(6, "Dead Letter Queue (DLQ)")
    dlq_jobs = queue.get_dlq_jobs()
    print(f"\nJobs in DLQ: {len(dlq_jobs)}")
    for job in dlq_jobs:
        print(f"  - {job['id']}: {job['command']}")
        print(f"    Attempts: {job['attempts']}, Error: {job.get('error_message', 'N/A')[:50]}")
    wait_for_user()
    
    # Step 7: Retry from DLQ
    print_step(7, "Retrying Job from DLQ")
    print("\nRetrying job from DLQ...")
    success = queue.retry_dead_job("demo-failed")
    if success:
        job_retried = queue.db.get_job("demo-failed")
        print(f"  [OK] Job moved back to pending")
        print(f"  State: {job_retried['state']}")
        print(f"  Attempts reset to: {job_retried['attempts']}")
    wait_for_user()
    
    # Step 8: Configuration changes
    print_step(8, "Changing Configuration")
    print("\nSetting max-retries to 5...")
    queue.set_config("max_retries", "5")
    new_value = queue.get_config("max_retries")
    print(f"  [OK] Max retries set to: {new_value}")
    wait_for_user()
    
    # Step 9: Final status
    print_step(9, "Final Status")
    stats = queue.get_stats()
    print("\nFinal queue statistics:")
    print(f"  Total Jobs: {sum(stats['jobs'].values())}")
    for state, count in sorted(stats['jobs'].items()):
        print(f"  {state.capitalize()}: {count}")
    print(f"  Active Workers: {stats['workers']}")
    
    print("\n" + "=" * 70)
    print("  Demo Complete!")
    print("=" * 70)
    print("\nYou can now use the CLI commands to interact with the queue:")
    print("  - python -m queuectl.cli status")
    print("  - python -m queuectl.cli list")
    print("  - python -m queuectl.cli dlq list")
    print("  - python -m queuectl.cli worker start --count 1")
    print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

