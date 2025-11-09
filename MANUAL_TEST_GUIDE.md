# QueueCTL - Manual Testing Guide

## Step-by-Step Terminal Demonstration

This guide will walk you through testing QueueCTL manually in your terminal.

---

## Prerequisites

1. Make sure you're in the project directory:
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
```

2. Verify dependencies are installed:
```powershell
pip list | findstr "click tabulate"
```

If not installed:
```powershell
pip install -r requirements.txt
```

---

## Step 1: Clean Start (Optional)

If you want to start fresh, remove the existing database:
```powershell
Remove-Item queuectl.db -ErrorAction SilentlyContinue
```

---

## Step 2: Check CLI Help

Verify the CLI is working:
```powershell
python -m queuectl.cli --help
```

You should see all available commands.

---

## Step 3: Check Current Status

See the current state of the queue:
```powershell
python -m queuectl.cli status
```

---

## Step 4: View Configuration

Check current configuration:
```powershell
python -m queuectl.cli config get
```

You should see:
- max-retries: 3
- backoff-base: 2

---

## Step 5: Enqueue Your First Job

**Method 1: Using Python directly (Easiest for Windows)**

Create a simple Python script to enqueue jobs:
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.enqueue('demo-1', 'echo Hello from QueueCTL'); print(f'Job {job[\"id\"]} enqueued!')"
```

**Method 2: Using a JSON file**

Create a file `job1.json`:
```json
{"id":"demo-1","command":"echo Hello from QueueCTL"}
```

Then run:
```powershell
$job = Get-Content job1.json -Raw; python -m queuectl.cli enqueue $job
```

**Method 3: Using Python script**

Create `enqueue_job.py`:
```python
from queuectl.queue import JobQueue
queue = JobQueue()
job = queue.enqueue("demo-1", "echo Hello from QueueCTL")
print(f"Job '{job['id']}' enqueued successfully!")
```

Run it:
```powershell
python enqueue_job.py
```

---

## Step 6: Check Status After Enqueueing

```powershell
python -m queuectl.cli status
```

You should see 1 pending job.

---

## Step 7: List All Jobs

```powershell
python -m queuectl.cli list
```

Or list only pending jobs:
```powershell
python -m queuectl.cli list --state pending
```

---

## Step 8: Enqueue More Jobs

Let's add a few more jobs to make it interesting:

```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('demo-2', 'echo Job 2 completed'); q.enqueue('demo-3', 'echo Job 3 completed'); print('2 more jobs enqueued!')"
```

Check status again:
```powershell
python -m queuectl.cli status
```

---

## Step 9: Process Jobs Manually (Without Workers)

You can process jobs manually to see them complete:

```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); print(f'Processing: {job[\"id\"]}'); q.execute_job(job); print('Job completed!')"
```

Run this a few times to process all jobs, then check status:
```powershell
python -m queuectl.cli status
python -m queuectl.cli list --state completed
```

---

## Step 10: Test Failed Jobs and Retries

Enqueue a job that will fail:
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.enqueue('failed-demo', 'exit 1', max_retries=2); print(f'Failed job enqueued: {job[\"id\"]}')"
```

Process it (it will fail):
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); print(f'Processing: {job[\"id\"]}'); result = q.execute_job(job); print(f'Result: {\"Success\" if result else \"Failed\"}')"
```

Check the job status:
```powershell
python -m queuectl.cli list --state failed
```

Wait a few seconds for backoff, then check if it moved back to pending:
```powershell
Start-Sleep -Seconds 3
python -m queuectl.cli list --state pending
```

---

## Step 11: Test Dead Letter Queue (DLQ)

To move a job to DLQ, we need to exhaust all retries. Let's create a script:

Create `test_dlq.py`:
```python
from queuectl.queue import JobQueue
import time

queue = JobQueue()

# Enqueue a job that will fail
queue.enqueue("dlq-test", "exit 1", max_retries=2)
print("Failed job enqueued with max_retries=2")

# Process and fail it multiple times
for i in range(3):
    job = queue.get_next_job()
    if job and job['id'] == 'dlq-test':
        print(f"Attempt {i+1}: Processing job...")
        queue.execute_job(job)
        job_after = queue.db.get_job("dlq-test")
        print(f"  State: {job_after['state']}, Attempts: {job_after['attempts']}")
        if job_after['state'] == 'dead':
            print("  Job moved to DLQ!")
            break
        time.sleep(3)  # Wait for backoff
```

Run it:
```powershell
python test_dlq.py
```

Check DLQ:
```powershell
python -m queuectl.cli dlq list
```

---

## Step 12: Retry from DLQ

Retry the job from DLQ:
```powershell
python -m queuectl.cli dlq retry dlq-test
```

Check if it's back in pending:
```powershell
python -m queuectl.cli list --state pending
```

---

## Step 13: Test Configuration Changes

Change max retries:
```powershell
python -m queuectl.cli config set max-retries 5
```

Verify the change:
```powershell
python -m queuectl.cli config get max-retries
```

Change backoff base:
```powershell
python -m queuectl.cli config set backoff-base 3
python -m queuectl.cli config get
```

---

## Step 14: Test Worker Processes (Advanced)

**Note**: Workers run in separate processes and need to be managed carefully.

### Start a Worker (in a separate terminal window)

Open a new PowerShell window and run:
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
python -m queuectl.cli worker start --count 1
```

The worker will keep running. Press `Ctrl+C` to stop it.

### In your main terminal, enqueue jobs:

```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('worker-test-1', 'echo Worker processed this'); q.enqueue('worker-test-2', 'echo Another job'); print('Jobs enqueued!')"
```

### Check status:

```powershell
python -m queuectl.cli status
```

You should see the worker processing jobs. After a few seconds, check again:
```powershell
python -m queuectl.cli status
python -m queuectl.cli list --state completed
```

### Stop the worker:

In the worker terminal, press `Ctrl+C`, or in main terminal:
```powershell
python -m queuectl.cli worker stop
```

---

## Step 15: Complete Demonstration Script

Create a complete demo script `full_demo.py`:

```python
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
print("   ✓ 3 successful jobs enqueued")

# 2. Enqueue a failed job
print("\n2. Enqueueing a failed job (will retry)...")
queue.enqueue("retry-job", "exit 1", max_retries=2)
print("   ✓ Failed job enqueued (max_retries=2)")

# 3. Process successful jobs
print("\n3. Processing successful jobs...")
for i in range(3):
    job = queue.get_next_job()
    if job and job['id'].startswith('success'):
        print(f"   Processing: {job['id']}")
        queue.execute_job(job)
        print(f"   ✓ {job['id']} completed")

# 4. Process failed job (first attempt)
print("\n4. Processing failed job (first attempt)...")
job = queue.get_next_job()
if job and job['id'] == 'retry-job':
    print(f"   Processing: {job['id']}")
    result = queue.execute_job(job)
    job_after = queue.db.get_job("retry-job")
    print(f"   ✗ Job failed (attempt {job_after['attempts']}/{job_after['max_retries']})")
    print(f"   State: {job_after['state']}")

# 5. Wait for backoff and retry
print("\n5. Waiting for backoff (3 seconds)...")
time.sleep(3)

job = queue.get_next_job()
if job and job['id'] == 'retry-job':
    print(f"   Retrying: {job['id']}")
    result = queue.execute_job(job)
    job_after = queue.db.get_job("retry-job")
    print(f"   ✗ Job failed again (attempt {job_after['attempts']}/{job_after['max_retries']})")
    if job_after['state'] == 'dead':
        print(f"   ✓ Job moved to DLQ")

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
    print(f"   - {job['id']}: {job['error_message'][:50]}")

# 8. Retry from DLQ
print("\n8. Retrying job from DLQ...")
queue.retry_dead_job("retry-job")
job_retried = queue.db.get_job("retry-job")
print(f"   ✓ Job '{job_retried['id']}' reset to pending")
print(f"   Attempts reset to: {job_retried['attempts']}")

print("\n" + "=" * 60)
print("Demonstration Complete!")
print("=" * 60)
print("\nRun 'python -m queuectl.cli status' to see current state")
```

Run the complete demo:
```powershell
python full_demo.py
```

Then check the results:
```powershell
python -m queuectl.cli status
python -m queuectl.cli list
python -m queuectl.cli dlq list
```

---

## Quick Reference Commands

### Status & Listing
```powershell
python -m queuectl.cli status
python -m queuectl.cli list
python -m queuectl.cli list --state pending
python -m queuectl.cli list --state completed
python -m queuectl.cli list --state failed
```

### Configuration
```powershell
python -m queuectl.cli config get
python -m queuectl.cli config get max-retries
python -m queuectl.cli config set max-retries 5
python -m queuectl.cli config set backoff-base 3
```

### DLQ
```powershell
python -m queuectl.cli dlq list
python -m queuectl.cli dlq retry <job-id>
```

### Workers
```powershell
python -m queuectl.cli worker start --count 1
python -m queuectl.cli worker stop
```

### Enqueue Jobs (Python)
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('job-id', 'command')"
```

---

## Tips for Demonstration

1. **Start Fresh**:** Remove `queuectl.db` to start with a clean state
2. **Use Python Scripts**: Easier than dealing with JSON escaping in PowerShell
3. **Two Terminals**: Use one for workers, one for commands
4. **Watch Status**: Run `status` command frequently to see changes
5. **Check Lists**: Use `list` with different states to see job progression

---

## Troubleshooting

**Problem**: JSON escaping issues in PowerShell
**Solution**: Use Python scripts or the Python API directly

**Problem**: Workers not processing jobs
**Solution**: Make sure workers are running and jobs are in pending state

**Problem**: Jobs stuck in processing
**Solution**: Restart workers or manually reset job state in database

**Problem**: Can't see changes
**Solution**: Wait a few seconds for database updates, then check status again

