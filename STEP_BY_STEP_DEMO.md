# QueueCTL - Step-by-Step Manual Demo Guide

Follow these steps in your terminal to demonstrate QueueCTL working.

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clean Start
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
Remove-Item queuectl.db -ErrorAction SilentlyContinue
```

### Step 2: Check CLI Works
```powershell
python -m queuectl.cli --version
python -m queuectl.cli --help
```

### Step 3: Check Initial Status
```powershell
python -m queuectl.cli status
```
**Expected**: "No jobs in queue"

### Step 4: Enqueue a Job (Method 1 - Easiest)
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.enqueue('demo-1', 'echo Hello World'); print(f'Job {job[\"id\"]} enqueued!')"
```

### Step 5: Check Status
```powershell
python -m queuectl.cli status
```
**Expected**: 1 pending job

### Step 6: List Jobs
```powershell
python -m queuectl.cli list
```
**Expected**: See your job in pending state

### Step 7: Process the Job Manually
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); print(f'Processing: {job[\"id\"]}'); result = q.execute_job(job); print('Completed!' if result else 'Failed!')"
```

### Step 8: Check Status Again
```powershell
python -m queuectl.cli status
python -m queuectl.cli list --state completed
```
**Expected**: Job is now completed

---

## 📋 Complete Demonstration (15 Minutes)

### Part 1: Basic Job Processing

**1. Enqueue Multiple Jobs**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('job1', 'echo Job 1'); q.enqueue('job2', 'echo Job 2'); q.enqueue('job3', 'echo Job 3'); print('3 jobs enqueued!')"
```

**2. Check Status**
```powershell
python -m queuectl.cli status
```

**3. Process All Jobs**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.execute_job(q.get_next_job()) for _ in range(3) if q.get_next_job()]; print('All jobs processed!')"
```

**4. Verify Completion**
```powershell
python -m queuectl.cli status
python -m queuectl.cli list --state completed
```

---

### Part 2: Failed Jobs and Retries

**1. Enqueue a Job That Will Fail**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('fail-job', 'exit 1', max_retries=2); print('Failed job enqueued!')"
```

**2. Process It (It Will Fail)**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); print(f'Processing: {job[\"id\"]}'); result = q.execute_job(job); print('Failed!' if not result else 'Success!')"
```

**3. Check Failed Jobs**
```powershell
python -m queuectl.cli list --state failed
```

**4. Wait for Backoff (3 seconds)**
```powershell
Start-Sleep -Seconds 3
```

**5. Check if Job Moved Back to Pending**
```powershell
python -m queuectl.cli list --state pending
```

**6. Process It Again (Will Fail Again)**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); q.execute_job(job) if job else None"
```

**7. Check DLQ**
```powershell
python -m queuectl.cli dlq list
```
**Expected**: Job should be in DLQ after exhausting retries

---

### Part 3: DLQ Retry

**1. Retry Job from DLQ**
```powershell
python -m queuectl.cli dlq retry fail-job
```

**2. Verify It's Back in Pending**
```powershell
python -m queuectl.cli list --state pending
```

---

### Part 4: Configuration

**1. View Current Config**
```powershell
python -m queuectl.cli config get
```

**2. Change Max Retries**
```powershell
python -m queuectl.cli config set max-retries 5
```

**3. Verify Change**
```powershell
python -m queuectl.cli config get max-retries
```

**4. Change Backoff Base**
```powershell
python -m queuectl.cli config set backoff-base 3
python -m queuectl.cli config get
```

---

### Part 5: Worker Processes

**1. Enqueue Jobs for Worker**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.enqueue(f'worker-job-{i}', f'echo Worker Job {i}') for i in range(1, 4)]; print('3 jobs enqueued for worker!')"
```

**2. Start Worker (in NEW terminal window)**
Open a new PowerShell window:
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
python -m queuectl.cli worker start --count 1
```

**3. In Original Terminal, Check Status**
```powershell
python -m queuectl.cli status
```

**4. Wait a Few Seconds, Check Again**
```powershell
Start-Sleep -Seconds 5
python -m queuectl.cli status
python -m queuectl.cli list --state completed
```

**5. Stop Worker**
In the worker terminal, press `Ctrl+C`, or in main terminal:
```powershell
python -m queuectl.cli worker stop
```

---

## 🎯 Simple One-Liner Commands

### Enqueue Jobs
```powershell
# Single job
python -c "from queuectl.queue import JobQueue; JobQueue().enqueue('test1', 'echo Test')"

# Multiple jobs
python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.enqueue(f'job{i}', f'echo Job {i}') for i in range(1, 6)]"
```

### Process Jobs
```powershell
# Process one job
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); q.execute_job(job) if job else print('No jobs')"

# Process all pending jobs
python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.execute_job(job) for _ in range(10) if (job := q.get_next_job())]"
```

### Check Status
```powershell
python -m queuectl.cli status
python -m queuectl.cli list
python -m queuectl.cli list --state pending
python -m queuectl.cli list --state completed
```

---

## 📝 Recommended Demo Flow

For a presentation or demo, follow this order:

1. **Show Empty Queue**
   ```powershell
   python -m queuectl.cli status
   ```

2. **Enqueue Jobs**
   ```powershell
   python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.enqueue(f'demo{i}', f'echo Demo Job {i}') for i in range(1, 4)]"
   ```

3. **Show Pending Jobs**
   ```powershell
   python -m queuectl.cli status
   python -m queuectl.cli list --state pending
   ```

4. **Process Jobs**
   ```powershell
   python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.execute_job(job) for _ in range(3) if (job := q.get_next_job())]"
   ```

5. **Show Completed Jobs**
   ```powershell
   python -m queuectl.cli status
   python -m queuectl.cli list --state completed
   ```

6. **Show Failed Job Flow**
   ```powershell
   python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('fail-demo', 'exit 1', max_retries=2)"
   python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.execute_job(q.get_next_job())"
   python -m queuectl.cli list --state failed
   Start-Sleep -Seconds 3
   python -m queuectl.cli list --state pending
   ```

7. **Show DLQ**
   ```powershell
   python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.execute_job(q.get_next_job())"
   python -m queuectl.cli dlq list
   ```

8. **Show Configuration**
   ```powershell
   python -m queuectl.cli config get
   python -m queuectl.cli config set max-retries 5
   python -m queuectl.cli config get
   ```

---

## 🎬 Quick Demo Script

Run this for a complete automated demo:
```powershell
python full_demo.py
```

Then check results:
```powershell
python -m queuectl.cli status
python -m queuectl.cli list
python -m queuectl.cli dlq list
```

---

## 💡 Tips

1. **Use Python one-liners** - Easier than JSON escaping in PowerShell
2. **Check status frequently** - See how jobs change state
3. **Use two terminals** - One for workers, one for commands
4. **Start fresh** - Remove `queuectl.db` for clean demos
5. **Show progression** - Run status/list commands between steps

---

## 🔍 Troubleshooting

**Jobs not processing?**
- Check if jobs are in pending state
- Make sure workers are running (if using workers)
- Process manually with Python one-liner

**Can't see changes?**
- Wait a few seconds for database updates
- Run status command again
- Check different states: `list --state pending`, `list --state completed`

**JSON errors?**
- Use Python API directly instead of CLI enqueue
- Create Python scripts for complex operations

