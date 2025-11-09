# QueueCTL - Quick Start Guide

## 🚀 Fastest Way to Demo (2 Minutes)

### Option 1: Automated Demo (Recommended)
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
python simple_demo.py
```

Then check results:
```powershell
python -m queuectl.cli status
python -m queuectl.cli list
python -m queuectl.cli config get
```

---

## 📝 Manual Step-by-Step Demo

### Step 1: Navigate to Project
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
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

### Step 4: Enqueue a Job
```powershell
python -c "from queuectl.queue import JobQueue; JobQueue().enqueue('demo1', 'echo Hello World')"
```

### Step 5: Check Status
```powershell
python -m queuectl.cli status
python -m queuectl.cli list
```

### Step 6: Process the Job
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); job = q.get_next_job(); q.execute_job(job) if job else None"
```

### Step 7: Verify Completion
```powershell
python -m queuectl.cli status
python -m queuectl.cli list --state completed
```

---

## 🎯 Complete Manual Demo (10 Minutes)

### Part A: Successful Jobs

**1. Enqueue 3 jobs:**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.enqueue(f'job{i}', f'echo Job {i}') for i in range(1, 4)]; print('3 jobs enqueued!')"
```

**2. Check status:**
```powershell
python -m queuectl.cli status
```

**3. Process all jobs:**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.execute_job(job) for _ in range(3) if (job := q.get_next_job())]"
```

**4. Verify:**
```powershell
python -m queuectl.cli status
python -m queuectl.cli list --state completed
```

### Part B: Failed Jobs & Retries

**1. Enqueue a failed job:**
```powershell
python -c "from queuectl.queue import JobQueue; JobQueue().enqueue('fail1', 'exit 1', max_retries=2)"
```

**2. Process it (will fail):**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.execute_job(q.get_next_job())"
```

**3. Check failed jobs:**
```powershell
python -m queuectl.cli list --state failed
```

**4. Wait for backoff (3 seconds):**
```powershell
Start-Sleep -Seconds 3
```

**5. Check if it moved back to pending:**
```powershell
python -m queuectl.cli list --state pending
```

**6. Process again (will fail and move to DLQ):**
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.execute_job(q.get_next_job())"
```

**7. Check DLQ:**
```powershell
python -m queuectl.cli dlq list
```

### Part C: DLQ Retry

**1. Retry from DLQ:**
```powershell
python -m queuectl.cli dlq retry fail1
```

**2. Verify:**
```powershell
python -m queuectl.cli list --state pending
```

### Part D: Configuration

**1. View config:**
```powershell
python -m queuectl.cli config get
```

**2. Change max retries:**
```powershell
python -m queuectl.cli config set max-retries 5
```

**3. Verify:**
```powershell
python -m queuectl.cli config get max-retries
```

---

## 📋 All Available Commands

### Status & Listing
```powershell
python -m queuectl.cli status
python -m queuectl.cli list
python -m queuectl.cli list --state pending
python -m queuectl.cli list --state completed
python -m queuectl.cli list --state failed
python -m queuectl.cli list --state dead
```

### Configuration
```powershell
python -m queuectl.cli config get
python -m queuectl.cli config get max-retries
python -m queuectl.cli config get backoff-base
python -m queuectl.cli config set max-retries 5
python -m queuectl.cli config set backoff-base 3
```

### Dead Letter Queue
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
# Single job
python -c "from queuectl.queue import JobQueue; JobQueue().enqueue('id', 'command')"

# Multiple jobs
python -c "from queuectl.queue import JobQueue; q = JobQueue(); [q.enqueue(f'job{i}', f'echo Job {i}') for i in range(1, 6)]"
```

---

## 💡 Tips

1. **Use `simple_demo.py`** for quick automated demo
2. **Use Python one-liners** to avoid JSON escaping issues
3. **Check status frequently** to see state changes
4. **Start fresh** by removing `queuectl.db` if needed
5. **Two terminals** - one for workers, one for commands

---

## 🎬 Presentation Flow

For a live demo, follow this order:

1. **Show empty queue** → `python -m queuectl.cli status`
2. **Enqueue jobs** → Python one-liner
3. **Show pending** → `python -m queuectl.cli list --state pending`
4. **Process jobs** → Python one-liner
5. **Show completed** → `python -m queuectl.cli list --state completed`
6. **Show failed job flow** → Enqueue failed job, process, show retry
7. **Show DLQ** → `python -m queuectl.cli dlq list`
8. **Show config** → `python -m queuectl.cli config get`
9. **Show worker** → Start worker in separate terminal

---

## ✅ Verification Checklist

After running the demo, verify:
- [ ] Jobs can be enqueued
- [ ] Jobs can be processed
- [ ] Failed jobs retry automatically
- [ ] Jobs move to DLQ after max retries
- [ ] Jobs can be retried from DLQ
- [ ] Configuration can be changed
- [ ] Status command shows correct counts
- [ ] List command shows jobs in correct states

---

**Ready to demo!** 🚀

