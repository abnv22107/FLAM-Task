# QueueCTL - Quick Terminal Demo (Copy-Paste Ready)

## Fast Demo - Copy and paste these commands in order

### 1. Setup & Check Status
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
python -m queuectl.cli status
python -m queuectl.cli config get
```

### 2. Enqueue Jobs (Using Python to avoid JSON escaping)
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('job1', 'echo Hello from Job 1'); print('Job 1 enqueued')"
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('job2', 'echo Hello from Job 2'); print('Job 2 enqueued')"
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('job3', 'echo Hello from Job 3'); print('Job 3 enqueued')"
```

### 3. Check Status
```powershell
python -m queuectl.cli status
python -m queuectl.cli list --state pending
```

### 4. Process Jobs
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); jobs = [q.get_next_job() for _ in range(3)]; [q.execute_job(j) for j in jobs if j]; print('All jobs processed')"
```

### 5. Check Completed Jobs
```powershell
python -m queuectl.cli status
python -m queuectl.cli list --state completed
```

### 6. Test Failed Job
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('failed-job', 'exit 1', max_retries=2); print('Failed job enqueued')"
python -m queuectl.cli status
```

### 7. Process Failed Job (First Failure)
```powershell
python -c "from queuectl.queue import JobQueue; q = JobQueue(); j = q.get_next_job(); q.execute_job(j) if j else None; result = q.db.get_job('failed-job'); print(f'State: {result[\"state\"]}, Attempts: {result[\"attempts\"]}') if result else None"
```

### 8. Wait and Retry (Wait 3 seconds)
```powershell
timeout /t 3
python -c "from queuectl.queue import JobQueue; q = JobQueue(); j = q.get_next_job(); q.execute_job(j) if j else None; result = q.db.get_job('failed-job'); print(f'State: {result[\"state\"]}, Attempts: {result[\"attempts\"]}') if result else None"
```

### 9. Check DLQ
```powershell
python -m queuectl.cli dlq list
python -m queuectl.cli status
```

### 10. Retry from DLQ
```powershell
python -m queuectl.cli dlq retry failed-job
python -m queuectl.cli status
```

### 11. Test Configuration
```powershell
python -m queuectl.cli config set max-retries 5
python -m queuectl.cli config get
```

---

## Interactive Demo (Recommended)

For a guided interactive demo, run:

```powershell
python demo_manual.py
```

This will walk you through all features step-by-step with explanations.

---

## Worker Demo (Two Terminals)

### Terminal 1 - Start Worker
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
python -m queuectl.cli worker start --count 1
```

### Terminal 2 - Enqueue Jobs
```powershell
cd C:\Users\arimb\OneDrive\Desktop\FLAM-Task
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('worker-job-1', 'echo Processed by worker'); print('Job enqueued')"
python -c "from queuectl.queue import JobQueue; q = JobQueue(); q.enqueue('worker-job-2', 'echo Another job'); print('Job enqueued')"
python -m queuectl.cli status
```

Watch Terminal 1 - the worker will process the jobs!

To stop worker: Press `Ctrl+C` in Terminal 1, or run:
```powershell
python -m queuectl.cli worker stop
```

---

## All CLI Commands Reference

```powershell
# Status
python -m queuectl.cli status

# List jobs
python -m queuectl.cli list
python -m queuectl.cli list --state pending
python -m queuectl.cli list --state completed
python -m queuectl.cli list --state failed
python -m queuectl.cli list --state dead

# Configuration
python -m queuectl.cli config get
python -m queuectl.cli config get max-retries
python -m queuectl.cli config set max-retries 5
python -m queuectl.cli config set backoff-base 3

# DLQ
python -m queuectl.cli dlq list
python -m queuectl.cli dlq retry <job-id>

# Workers
python -m queuectl.cli worker start --count 1
python -m queuectl.cli worker start --count 3
python -m queuectl.cli worker stop

# Help
python -m queuectl.cli --help
python -m queuectl.cli worker --help
```

---

## Tips

1. **Enqueueing**: Use Python one-liners to avoid PowerShell JSON escaping
2. **Workers**: Run in separate terminal to see real-time processing
3. **Status**: Check frequently to see state changes
4. **Persistence**: All data saved in `queuectl.db` - survives restarts

