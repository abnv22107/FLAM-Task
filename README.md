# QueueCTL - CLI-based Background Job Queue System

A production-grade CLI tool for managing background job queues with worker processes, automatic retries with exponential backoff, and Dead Letter Queue (DLQ) support.

## 🚀 Features

- ✅ **Job Management**: Enqueue, list, and track background jobs
- ✅ **Worker Processes**: Run multiple workers in parallel
- ✅ **Automatic Retries**: Exponential backoff retry mechanism
- ✅ **Dead Letter Queue**: Handle permanently failed jobs
- ✅ **Persistence**: SQLite database for job storage across restarts
- ✅ **Configuration**: Configurable retry count and backoff base
- ✅ **Graceful Shutdown**: Workers finish current jobs before exiting
- ✅ **Job Locking**: Prevents duplicate job processing

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd FLAM-Task
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the package** (optional, for global access):
   ```bash
   pip install -e .
   ```

   Or use directly with:
   ```bash
   python -m queuectl.cli <command>
   ```

## 📖 Usage

### Basic Commands

#### Enqueue a Job

```bash
queuectl enqueue '{"id":"job1","command":"echo Hello World"}'
```

Or with max retries:
```bash
queuectl enqueue '{"id":"job2","command":"sleep 2","max_retries":5}'
```

#### Start Workers

Start a single worker:
```bash
queuectl worker start --count 1
```

Start multiple workers:
```bash
queuectl worker start --count 3
```

Press `Ctrl+C` to stop workers gracefully.

#### Stop Workers

```bash
queuectl worker stop
```

#### Check Status

```bash
queuectl status
```

Shows:
- Total jobs count
- Jobs by state (pending, processing, completed, failed, dead)
- Active workers and their details

#### List Jobs

List all jobs:
```bash
queuectl list
```

Filter by state:
```bash
queuectl list --state pending
queuectl list --state completed
queuectl list --state failed
```

#### Dead Letter Queue

List all jobs in DLQ:
```bash
queuectl dlq list
```

Retry a job from DLQ:
```bash
queuectl dlq retry job-id
```

#### Configuration

Set configuration:
```bash
queuectl config set max-retries 5
queuectl config set backoff-base 3
```

Get configuration:
```bash
queuectl config get max-retries
queuectl config get backoff-base
```

Get all configuration:
```bash
queuectl config get
```

## 🏗️ Architecture

### Job Lifecycle

```
pending → processing → completed
   ↓
failed → (retry with backoff) → pending → ...
   ↓
dead (DLQ)
```

### Components

1. **Database Layer** (`queuectl/database.py`)
   - SQLite-based persistence
   - Job state management
   - Worker tracking
   - Configuration storage

2. **Queue Manager** (`queuectl/queue.py`)
   - Job enqueueing
   - Job execution
   - Retry logic with exponential backoff
   - DLQ management

3. **Worker Processes** (`queuectl/worker.py`)
   - Multi-process worker execution
   - Job locking to prevent duplicates
   - Graceful shutdown handling

4. **CLI Interface** (`queuectl/cli.py`)
   - Command-line interface using Click
   - User-friendly output with tables

### Exponential Backoff

Failed jobs retry with exponential backoff:
```
delay = base ^ attempts (seconds)
```

Example with `backoff-base = 2`:
- Attempt 1: 2 seconds delay
- Attempt 2: 4 seconds delay
- Attempt 3: 8 seconds delay

### Job States

| State | Description |
|-------|-------------|
| `pending` | Waiting to be picked up by a worker |
| `processing` | Currently being executed |
| `completed` | Successfully executed |
| `failed` | Failed, but retryable (waiting for backoff) |
| `dead` | Permanently failed (moved to DLQ) |

## 🧪 Testing

### Quick Test

Run the basic test suite:

```bash
python test_basic.py
```

This validates core functionality:
1. Job enqueueing
2. Job execution
3. Failed job retry
4. Configuration management
5. DLQ functionality
6. DLQ retry

### Comprehensive Test Suite

Run the full test suite (requires workers to be running):

```bash
python test_queuectl.py
```

The comprehensive test suite validates:
1. Basic job enqueueing
2. Job completion
3. Failed job retry with backoff
4. Multiple workers processing jobs
5. Data persistence across restarts
6. DLQ retry functionality
7. Configuration management

### Manual Testing Examples

**Test 1: Successful Job**
```bash
# Terminal 1: Start worker
queuectl worker start --count 1

# Terminal 2: Enqueue job
queuectl enqueue '{"id":"test1","command":"echo Success"}'

# Check status
queuectl status
```

**Test 2: Failed Job with Retries**
```bash
# Enqueue a job that will fail
queuectl enqueue '{"id":"test2","command":"exit 1","max_retries":3}'

# Start worker and watch it retry
queuectl worker start --count 1

# After retries exhausted, check DLQ
queuectl dlq list
```

**Test 3: Multiple Workers**
```bash
# Enqueue multiple jobs
for i in {1..10}; do
  queuectl enqueue "{\"id\":\"job$i\",\"command\":\"echo Job $i\"}"
done

# Start 3 workers
queuectl worker start --count 3

# Monitor status
queuectl status
```

## 📁 Project Structure

```
FLAM-Task/
├── queuectl/
│   ├── __init__.py
│   ├── cli.py          # CLI interface
│   ├── database.py     # Database layer
│   ├── queue.py        # Queue manager
│   └── worker.py       # Worker processes
├── requirements.txt    # Dependencies
├── setup.py           # Package setup
├── test_queuectl.py   # Test suite
├── README.md          # This file
└── queuectl.db        # SQLite database (created on first run)
```

## ⚙️ Configuration

Default configuration:
- `max-retries`: 3
- `backoff-base`: 2

These can be changed using the `config` commands and will apply to new jobs.

## 🔒 Concurrency & Safety

- **Job Locking**: Database-level locking prevents duplicate job processing
- **Worker Isolation**: Each worker runs in a separate process
- **Graceful Shutdown**: Workers finish current jobs before exiting
- **Transaction Safety**: SQLite transactions ensure data consistency

## 📝 Assumptions & Trade-offs

### Assumptions

1. **Command Execution**: Jobs execute shell commands. Commands that don't exist or fail will trigger retries.
2. **Timeout**: Jobs have a 5-minute execution timeout.
3. **Database**: SQLite is used for simplicity and portability. For high-scale production, consider PostgreSQL or similar.
4. **Platform**: Works on Windows, Linux, and macOS.

### Trade-offs

1. **SQLite vs. PostgreSQL**: SQLite chosen for simplicity and zero-configuration. Suitable for single-machine deployments.
2. **Process-based Workers**: Using multiprocessing instead of threading for true parallelism and isolation.
3. **File-based Storage**: Database file (`queuectl.db`) is created in the current directory.
4. **No Web Dashboard**: CLI-only interface for simplicity. Web dashboard would be a bonus feature.

## 🐛 Troubleshooting

**Workers not processing jobs:**
- Check if workers are running: `queuectl status`
- Verify jobs are in pending state: `queuectl list --state pending`
- Check database file exists: `ls queuectl.db`

**Jobs stuck in processing:**
- Workers may have crashed. Restart workers: `queuectl worker stop && queuectl worker start --count 1`
- Manually reset job state if needed (requires database access)

**Database locked errors:**
- Ensure only one process accesses the database at a time
- Close any database viewers or other processes using the DB

## 🚧 Future Enhancements (Bonus Features)

Potential improvements:
- Job timeout handling (per-job timeout)
- Job priority queues
- Scheduled/delayed jobs (`run_at` field)
- Job output logging
- Metrics and execution statistics
- Minimal web dashboard for monitoring
- Job dependencies
- Job cancellation

## 📄 License

This project is created as part of a backend developer internship assignment.

## 👤 Author

Created as part of FLAM-Task assignment.

---

## 📹 Demo

### Quick Start Example

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Enqueue a job
python -m queuectl.cli enqueue '{"id":"demo1","command":"echo Hello World"}'

# 3. Check status
python -m queuectl.cli status

# 4. Start a worker (in a separate terminal)
python -m queuectl.cli worker start --count 1

# 5. Check status again (jobs should be processed)
python -m queuectl.cli status

# 6. List completed jobs
python -m queuectl.cli list --state completed
```

### Demo Scripts

- **Linux/Mac**: Run `bash examples/demo.sh`
- **Windows**: Run `powershell examples/demo.ps1`

A working CLI demo video can be found at: [Demo Link - To be added]

---

**Note**: This is a minimal production-grade implementation. For production use at scale, consider:
- Using a more robust database (PostgreSQL)
- Adding monitoring and alerting
- Implementing job priorities
- Adding job output storage
- Implementing job dependencies
- Adding a web dashboard

