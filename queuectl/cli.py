"""CLI interface for queuectl"""

import click
import json
import sys
from tabulate import tabulate
from .queue import JobQueue
from .worker import WorkerManager
from .database import Database


@click.group()
@click.version_option(version="1.0.0")
def main():
    """QueueCTL - CLI-based background job queue system"""
    pass


@main.command()
@click.argument('job_data', type=str)
def enqueue(job_data):
    """Enqueue a new job
    
    JOB_DATA: JSON string with job details, e.g., '{"id":"job1","command":"sleep 2"}'
    """
    try:
        data = json.loads(job_data)
        job_id = data.get('id')
        command = data.get('command')
        max_retries = data.get('max_retries')
        
        if not job_id or not command:
            click.echo("Error: 'id' and 'command' are required fields", err=True)
            sys.exit(1)
        
        queue = JobQueue()
        job = queue.enqueue(job_id, command, max_retries)
        
        click.echo(f"Job '{job_id}' enqueued successfully")
        click.echo(f"  Command: {command}")
        click.echo(f"  State: {job['state']}")
        click.echo(f"  Max Retries: {job['max_retries']}")
        
    except json.JSONDecodeError:
        click.echo("Error: Invalid JSON format", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.group()
def worker():
    """Manage worker processes"""
    pass


@worker.command()
@click.option('--count', default=1, type=int, help='Number of workers to start')
def start(count):
    """Start one or more worker processes"""
    if count < 1:
        click.echo("Error: Worker count must be at least 1", err=True)
        sys.exit(1)
    
    click.echo(f"Starting {count} worker(s)...")
    
    manager = WorkerManager()
    processes = manager.start_workers(count)
    
    click.echo(f"Started {len(processes)} worker(s)")
    click.echo("Workers are running. Press Ctrl+C to stop.")
    
    try:
        # Keep main process alive
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nStopping workers...")
        manager.stop_workers()
        click.echo("Workers stopped")


@worker.command()
def stop():
    """Stop all running workers gracefully"""
    click.echo("Stopping all workers...")
    
    manager = WorkerManager()
    manager.stop_workers()
    
    click.echo("All workers stopped")


@main.command()
def status():
    """Show summary of all job states & active workers"""
    queue = JobQueue()
    stats = queue.get_stats()
    
    # Job statistics
    job_stats = stats['jobs']
    total_jobs = sum(job_stats.values())
    
    click.echo("=== Queue Status ===")
    click.echo(f"\nTotal Jobs: {total_jobs}")
    
    if job_stats:
        table_data = [[state, count] for state, count in sorted(job_stats.items())]
        click.echo("\nJob States:")
        click.echo(tabulate(table_data, headers=["State", "Count"], tablefmt="grid"))
    else:
        click.echo("\nNo jobs in queue")
    
    # Worker information
    worker_count = stats['workers']
    click.echo(f"\nActive Workers: {worker_count}")
    
    if stats['worker_details']:
        worker_data = [
            [w['worker_id'], w['pid'], w['started_at'], w['last_heartbeat']]
            for w in stats['worker_details']
        ]
        click.echo("\nWorker Details:")
        click.echo(tabulate(
            worker_data,
            headers=["Worker ID", "PID", "Started", "Last Heartbeat"],
            tablefmt="grid"
        ))


@main.command()
@click.option('--state', type=click.Choice(['pending', 'processing', 'completed', 'failed', 'dead']), 
              help='Filter jobs by state')
def list(state):
    """List jobs, optionally filtered by state"""
    queue = JobQueue()
    jobs = queue.list_jobs(state)
    
    if not jobs:
        state_msg = f" with state '{state}'" if state else ""
        click.echo(f"No jobs found{state_msg}")
        return
    
    # Prepare table data
    table_data = []
    for job in jobs:
        table_data.append([
            job['id'],
            job['command'][:50] + ('...' if len(job['command']) > 50 else ''),
            job['state'],
            job['attempts'],
            job['max_retries'],
            job['created_at'],
            job['updated_at']
        ])
    
    headers = ["ID", "Command", "State", "Attempts", "Max Retries", "Created At", "Updated At"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@main.group()
def dlq():
    """Manage Dead Letter Queue"""
    pass


@dlq.command()
def list():
    """List all jobs in Dead Letter Queue"""
    queue = JobQueue()
    jobs = queue.get_dlq_jobs()
    
    if not jobs:
        click.echo("No jobs in Dead Letter Queue")
        return
    
    table_data = []
    for job in jobs:
        error = job.get('error_message', 'N/A')
        if error and len(error) > 50:
            error = error[:50] + '...'
        
        table_data.append([
            job['id'],
            job['command'][:50] + ('...' if len(job['command']) > 50 else ''),
            job['attempts'],
            job['max_retries'],
            error,
            job['created_at']
        ])
    
    headers = ["ID", "Command", "Attempts", "Max Retries", "Error", "Created At"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@dlq.command()
@click.argument('job_id', type=str)
def retry(job_id):
    """Retry a job from Dead Letter Queue"""
    queue = JobQueue()
    
    try:
        success = queue.retry_dead_job(job_id)
        if success:
            click.echo(f"Job '{job_id}' moved back to pending queue")
        else:
            click.echo(f"Error: Job '{job_id}' not found", err=True)
            sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.group()
def config():
    """Manage configuration"""
    pass


@config.command('set')
@click.argument('key', type=str)
@click.argument('value', type=str)
def set_config(key, value):
    """Set a configuration value
    
    Examples:
        queuectl config set max-retries 5
        queuectl config set backoff-base 3
    """
    valid_keys = ['max-retries', 'backoff-base']
    
    if key not in valid_keys:
        click.echo(f"Error: Invalid config key. Valid keys: {', '.join(valid_keys)}", err=True)
        sys.exit(1)
    
    # Validate value
    if key == 'max-retries':
        try:
            int(value)
        except ValueError:
            click.echo("Error: max-retries must be an integer", err=True)
            sys.exit(1)
    elif key == 'backoff-base':
        try:
            float(value)
        except ValueError:
            click.echo("Error: backoff-base must be a number", err=True)
            sys.exit(1)
    
    # Map CLI key to DB key
    db_key = key.replace('-', '_')
    
    queue = JobQueue()
    queue.set_config(db_key, value)
    
    click.echo(f"Configuration '{key}' set to '{value}'")


@config.command('get')
@click.argument('key', type=str, required=False)
def get_config(key):
    """Get configuration value(s)"""
    queue = JobQueue()
    
    if key:
        valid_keys = ['max-retries', 'backoff-base']
        if key not in valid_keys:
            click.echo(f"Error: Invalid config key. Valid keys: {', '.join(valid_keys)}", err=True)
            sys.exit(1)
        
        db_key = key.replace('-', '_')
        value = queue.get_config(db_key)
        click.echo(f"{key}: {value}")
    else:
        # Show all config
        max_retries = queue.get_config('max_retries', '3')
        backoff_base = queue.get_config('backoff_base', '2')
        
        table_data = [
            ['max-retries', max_retries],
            ['backoff-base', backoff_base]
        ]
        click.echo(tabulate(table_data, headers=["Key", "Value"], tablefmt="grid"))


if __name__ == '__main__':
    main()

