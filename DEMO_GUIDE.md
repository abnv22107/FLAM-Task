# QueueCTL - Step-by-Step Terminal Demo Guide

This guide will walk you through demonstrating QueueCTL in your terminal, showing all the key features.

## Prerequisites

Make sure you're in the project directory:
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
```

## Step-by-Step Demo

### Step 1: Verify Installation

```powershell
# Check if dependencies are installed
python -m pip list | findstr "click tabulate"

# If not installed, run:
python -m pip install -r requirements.txt

# Verify CLI works
python -m queuectl.cli --version
```

**Expected Output:**
```
python -m queuectl.cli, version 1.0.0
```

---

### Step 2: Check Initial Status

```powershell
python -m queuectl.cli status
```

**Expected Output:**
```
=== Queue Status ===

Total Jobs: 0

No jobs in queue

Active Workers: 0
```

---

### Step 3: View Configuration

```powershell
python -m queuectl.cli config get
```

**Expected Output:**
```
+--------------+---------+
| Key          |   Value |
+==============+=========+
| max-retries  |       3 |
+--------------+---------+
| backoff-base |       2 |
+--------------+---------+
```

---

### Step 4: Enqueue Some Jobs

We'll use a Python script to avoid PowerShell JSON escaping issues. Create jobs programmatically:

```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('demo1', 'echo Hello from Job 1'); print('Job 1 enqueued')"
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('demo2', 'echo Hello from Job 2'); print('Job 2 enqueued')"
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('demo3', 'echo Hello from Job 3'); print('Job 3 enqueued')"
```

**Expected Output:**
```
Job 1 enqueued
Job 2 enqueued
Job 3 enqueued
```

---

### Step 5: Check Status After Enqueueing

```powershell
python -m queuectl.cli status
```

**Expected Output:**
```
=== Queue Status ===

Total Jobs: 3

Job States:
+-----------+---------+
| State     |   Count |
+===========+=========+
| pending   |       3 |
+-----------+---------+

Active Workers: 0
```

---

### Step 6: List Pending Jobs

```powershell
python -m queuectl.cli list --state pending
```

**Expected Output:**
```
+-------+----------------------+-----------+------------+---------------+...
| ID    | Command              | State     |   Attempts |   Max Retries |...
+=======+======================+===========+============+===============+...
| demo3 | echo Hello from Job 3| pending   |          0 |             3 |...
| demo2 | echo Hello from Job 2| pending   |          0 |             3 |...
| demo1 | echo Hello from Job 1| pending   |          0 |             3 |...
+-------+----------------------+-----------+------------+---------------+...
```

---

### Step 7: Process Jobs Manually (Simulate Worker)

```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); print(f'Processing: {job[\"id\"]}') if job else None; q.execute_job(job) if job else None; print('Job completed') if job and q.db.get_job(job['id'])['state'] == 'completed' else None"
```

Run this 3 times to process all jobs, or use a loop:

```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.execute_job(q.get_next_job()) for _ in range(3) if q.get_next_job()]; print('All jobs processed')"
```

---

### Step 8: Check Completed Jobs

```powershell
python -m queuectl.cli status
```

**Expected Output:**
```
=== Queue Status ===

Total Jobs: 3

Job States:
+-----------+---------+
| State     |   Count |
+===========+=========+
| completed |       3 |
+-----------+---------+

Active Workers: 0
```

```powershell
python -m queuectl.cli list --state completed
```

---

### Step 9: Test Failed Job with Retries

```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('failed-demo', 'exit 1', max_retries=2); print('Failed job enqueued')"
```

```powershell
python -m queuectl.cli status
```

**Expected Output:** Should show 1 pending job

---

### Step 10: Process Failed Job (First Failure)

```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); q.execute_job(job) if job else None; j = q.db.get_job('failed-demo'); print(f'State: {j[\"state\"]}, Attempts: {j[\"attempts\"]}') if j else None"
```

**Expected Output:**
```
State: failed, Attempts: 1
```

---

### Step 11: Wait for Backoff and Retry

```powershell
# Wait 3 seconds for backoff (2^1 = 2 seconds)
timeout /t 3

# Process again
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); q.execute_job(job) if job else None; j = q.db.get_job('failed-demo'); print(f'State: {j[\"state\"]}, Attempts: {j[\"attempts\"]}') if j else None"
```

**Expected Output:**
```
State: dead, Attempts: 2
```

The job moved to DLQ after exhausting retries!

---

### Step 12: Check DLQ

```powershell
python -m queuectl.cli dlq list
```

**Expected Output:**
```
+-------------+----------+------------+---------------+------------------+...
| ID          | Command  |   Attempts |   Max Retries | Error            |...
+=============+==========+============+===============+==================+...
| failed-demo | exit 1   |          2 |             2 | Command failed   |...
+-------------+----------+------------+---------------+------------------+...
```

---

### Step 13: Retry Job from DLQ

```powershell
python -m queuectl.cli dlq retry failed-demo
```

**Expected Output:**
```
Job 'failed-demo' moved back to pending queue
```

```powershell
python -m queuectl.cli status
```

**Expected Output:** Should show 1 pending job again

---

### Step 14: Test Configuration Changes

```powershell
python -m queuectl.cli config set max-retries 5
```

```powershell
python -m queuectl.cli config get max-retries
```

**Expected Output:**
```
max-retries: 5
```

```powershell
python -m queuectl.cli config get
```

---

### Step 15: Test with Actual Worker (Optional)

**Open a NEW terminal window** and run:

```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
python -m queuectl.cli worker start --count 1
```

**In the original terminal**, enqueue a job:

```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('worker-test', 'echo Processed by worker'); print('Job enqueued')"
```

Wait a few seconds, then check status:

```powershell
python -m queuectl.cli status
```

The worker should have processed the job!

**To stop the worker**, press `Ctrl+C` in the worker terminal, or run:

```powershell
python -m queuectl.cli worker stop
```

---

## Quick Demo Script

For a faster demo, you can use this Python script:

```powershell
python demo_manual.py
```

See `demo_manual.py` for the complete automated demo.

---

## Summary of Commands

| Action | Command |
|--------|---------|
| Check status | `python -m queuectl.cli status` |
| List jobs | `python -m queuectl.cli list` |
| List by state | `python -m queuectl.cli list --state pending` |
| View config | `python -m queuectl.cli config get` |
| Set config | `python -m queuectl.cli config set max-retries 5` |
| View DLQ | `python -m queuectl.cli dlq list` |
| Retry from DLQ | `python -m queuectl.cli dlq retry <job-id>` |
| Start worker | `python -m queuectl.cli worker start --count 1` |
| Stop worker | `python -m queuectl.cli worker stop` |

---

## Tips

1. **Enqueueing Jobs**: Use Python one-liners to avoid PowerShell JSON escaping issues
2. **Workers**: Run workers in a separate terminal to see them in action
3. **Status**: Check status frequently to see job state changes
4. **DLQ**: Jobs move to DLQ after exhausting max_retries
5. **Persistence**: All data persists in `queuectl.db` - jobs survive restarts

---

Enjoy demonstrating QueueCTL! 🚀

