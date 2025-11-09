# QueueCTL Architecture

## Overview

QueueCTL is a CLI-based background job queue system built with Python. It provides a production-grade solution for managing background jobs with automatic retries, worker processes, and Dead Letter Queue (DLQ) support.

## System Architecture

### Component Diagram

```
┌─────────────┐
│   CLI       │  (queuectl/cli.py)
│  Interface  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Queue     │  (queuectl/queue.py)
│  Manager    │
└──────┬──────┘
       │
       ├──────────────┐
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│  Database   │  │   Worker    │  (queuectl/worker.py)
│   Layer     │  │  Processes  │
│(SQLite)     │  └─────────────┘
└─────────────┘
```

## Core Components

### 1. Database Layer (`queuectl/database.py`)

**Purpose**: Provides persistent storage for jobs, workers, and configuration.

**Key Features**:
- SQLite database for zero-configuration persistence
- Transaction-safe operations
- Row-level locking for job processing
- Worker tracking and heartbeat mechanism

**Database Schema**:
- `jobs`: Stores job information (id, command, state, attempts, etc.)
- `config`: Stores system configuration (max_retries, backoff_base)
- `workers`: Tracks active worker processes

**Key Methods**:
- `create_job()`: Create a new job
- `get_pending_job()`: Get next job with locking
- `update_job()`: Update job state and metadata
- `list_jobs()`: Query jobs by state
- `get_job_stats()`: Get statistics about job states

### 2. Queue Manager (`queuectl/queue.py`)

**Purpose**: Manages job lifecycle, execution, and retry logic.

**Key Features**:
- Job enqueueing with validation
- Job execution via subprocess
- Automatic retry with exponential backoff
- DLQ management

**Job Lifecycle**:
```
pending → processing → completed
   ↓
failed → (wait for backoff) → pending → ...
   ↓
dead (DLQ)
```

**Exponential Backoff**:
- Formula: `delay = base ^ attempts` seconds
- Default base: 2
- Example: 2s, 4s, 8s delays for attempts 1, 2, 3

**Key Methods**:
- `enqueue()`: Add job to queue
- `get_next_job()`: Get next job to process
- `execute_job()`: Execute job command
- `_handle_job_failure()`: Handle failures with retry logic
- `retry_dead_job()`: Retry job from DLQ

### 3. Worker Processes (`queuectl/worker.py`)

**Purpose**: Process jobs from the queue in parallel.

**Key Features**:
- Multi-process architecture for true parallelism
- Graceful shutdown (finishes current job before exit)
- Worker registration and heartbeat tracking
- Cross-platform signal handling

**Worker Architecture**:
- Each worker runs in a separate process
- Worker loop continuously polls for jobs
- Updates heartbeat to indicate liveness
- Handles SIGINT/SIGTERM for graceful shutdown

**Key Classes**:
- `Worker`: Single worker instance
- `WorkerManager`: Manages multiple worker processes

### 4. CLI Interface (`queuectl/cli.py`)

**Purpose**: Provides user-friendly command-line interface.

**Technology**: Click framework for CLI construction

**Commands**:
- `enqueue`: Add jobs to queue
- `worker start/stop`: Manage workers
- `status`: Show queue statistics
- `list`: List jobs by state
- `dlq list/retry`: Manage Dead Letter Queue
- `config get/set`: Manage configuration

## Data Flow

### Job Processing Flow

1. **Enqueue**: User enqueues job via CLI
   - Job created in database with state `pending`
   - Job stored with metadata (id, command, max_retries)

2. **Worker Picks Up Job**:
   - Worker queries for pending jobs
   - Database locks job by updating state to `processing`
   - Job returned to worker

3. **Job Execution**:
   - Worker executes command via subprocess
   - Captures exit code and output
   - Updates job state based on result

4. **Success Path**:
   - Job state → `completed`
   - Job marked with completion timestamp

5. **Failure Path**:
   - If attempts < max_retries:
     - Job state → `failed`
     - Calculate backoff delay
     - Set `next_retry_at` timestamp
   - If attempts >= max_retries:
     - Job state → `dead`
     - Job moved to DLQ

6. **Retry Logic**:
   - When worker queries for jobs, checks for failed jobs with expired `next_retry_at`
   - Automatically moves failed jobs back to `pending` when retry time arrives

## Concurrency & Safety

### Job Locking

- Database-level locking prevents duplicate processing
- State transition: `pending` → `processing` is atomic
- Only one worker can process a job at a time

### Worker Isolation

- Each worker runs in separate process
- No shared memory between workers
- Database provides coordination point

### Transaction Safety

- All database operations use transactions
- Rollback on errors
- Consistent state maintained

## Configuration

### Default Values

- `max-retries`: 3
- `backoff-base`: 2

### Configuration Storage

- Stored in SQLite `config` table
- Persists across restarts
- Can be changed via CLI

## Error Handling

### Job Execution Errors

- Command not found → Treated as failure
- Non-zero exit code → Treated as failure
- Timeout (5 minutes) → Treated as failure
- All errors trigger retry logic

### Worker Errors

- Worker crashes → Job remains in `processing` state
- Solution: Restart workers, manually reset stuck jobs if needed
- Worker heartbeat tracks liveness

### Database Errors

- Connection errors → Retry with backoff
- Lock timeouts → Retry query
- Transaction rollback on errors

## Scalability Considerations

### Current Limitations

- SQLite: Single-writer limitation
- File-based: Not suitable for distributed systems
- No job priorities
- No job dependencies

### Future Enhancements

- PostgreSQL for distributed deployments
- Redis for high-throughput scenarios
- Job priorities
- Scheduled jobs
- Job dependencies
- Web dashboard

## Testing Strategy

### Unit Tests

- `test_basic.py`: Core functionality tests
- Tests job lifecycle, retries, DLQ, configuration

### Integration Tests

- `test_queuectl.py`: Full system tests
- Tests with actual worker processes
- Tests persistence across restarts

### Manual Testing

- Demo scripts for interactive testing
- CLI command validation

## Deployment

### Requirements

- Python 3.7+
- SQLite (included with Python)
- Dependencies: click, tabulate

### Installation

```bash
pip install -r requirements.txt
pip install -e .  # Optional, for global access
```

### Usage

```bash
# Direct module execution
python -m queuectl.cli <command>

# Or if installed
queuectl <command>
```

## Design Decisions

### Why SQLite?

- Zero configuration
- File-based, easy to backup
- Sufficient for single-machine use
- Can migrate to PostgreSQL later

### Why Multiprocessing?

- True parallelism (unlike threading in Python)
- Process isolation
- Better for CPU-bound tasks
- Easier to scale

### Why Exponential Backoff?

- Standard retry strategy
- Prevents overwhelming failing systems
- Configurable base for flexibility

### Why CLI-only?

- Simple and lightweight
- No web server overhead
- Easy to integrate into scripts
- Web dashboard can be added later

## Security Considerations

### Command Execution

- Jobs execute shell commands
- **Risk**: Command injection if job data is untrusted
- **Mitigation**: Validate job input, sanitize commands

### Database Access

- File-based SQLite
- **Risk**: File permissions
- **Mitigation**: Set appropriate file permissions

### Worker Processes

- Workers run with same privileges as CLI
- **Risk**: Privilege escalation
- **Mitigation**: Run workers with limited privileges if needed

## Performance Characteristics

### Job Throughput

- Limited by SQLite write performance
- ~100-1000 jobs/second (depending on job duration)
- Can be improved with connection pooling

### Worker Scalability

- Linear scaling with number of workers
- Limited by database locking
- Optimal: 1-10 workers per SQLite instance

### Memory Usage

- Minimal per worker (~10-50MB)
- Database size: ~1KB per job
- Suitable for thousands of jobs

## Conclusion

QueueCTL provides a solid foundation for background job processing with:
- ✅ Persistent storage
- ✅ Automatic retries
- ✅ Worker parallelism
- ✅ Dead Letter Queue
- ✅ Graceful shutdown
- ✅ Configuration management

The architecture is designed for extensibility and can be enhanced with additional features as needed.

