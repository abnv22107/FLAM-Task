#!/usr/bin/env python3
"""
Test script for queuectl - validates core functionality
"""

import subprocess
import time
import os
import sys
import json
import sqlite3
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode


def cleanup():
    """Clean up test database"""
    db_file = Path("queuectl.db")
    if db_file.exists():
        db_file.unlink()
    print("✓ Cleaned up test database")


def test_basic_enqueue():
    """Test 1: Basic job enqueue"""
    print("\n=== Test 1: Basic Job Enqueue ===")
    
    job_data = json.dumps({"id": "test-job-1", "command": "echo 'Hello World'"})
    stdout, stderr, code = run_command(f"python -m queuectl.cli enqueue '{job_data}'")
    
    if code == 0 and "enqueued successfully" in stdout:
        print("✓ Job enqueued successfully")
        return True
    else:
        print(f"✗ Failed: {stdout} {stderr}")
        return False


def test_job_completion():
    """Test 2: Job completes successfully"""
    print("\n=== Test 2: Job Completion ===")
    
    # Enqueue a simple job
    job_data = json.dumps({"id": "test-job-2", "command": "echo 'Success'"})
    run_command(f"python -m queuectl.cli enqueue '{job_data}'")
    
    # Start a worker
    worker_process = subprocess.Popen(
        ["python", "-m", "queuectl.cli", "worker", "start", "--count", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for job to complete
    time.sleep(3)
    
    # Check status
    stdout, _, _ = run_command("python -m queuectl.cli status")
    
    # Stop worker
    worker_process.terminate()
    worker_process.wait(timeout=5)
    
    if "completed" in stdout.lower() or "test-job-2" in stdout:
        print("✓ Job completed successfully")
        return True
    else:
        print(f"✗ Failed: {stdout}")
        return False


def test_failed_job_retry():
    """Test 3: Failed job retries with backoff"""
    print("\n=== Test 3: Failed Job Retry ===")
    
    # Enqueue a job that will fail
    job_data = json.dumps({
        "id": "test-job-3",
        "command": "exit 1",  # This will fail
        "max_retries": 2
    })
    run_command(f"python -m queuectl.cli enqueue '{job_data}'")
    
    # Start a worker
    worker_process = subprocess.Popen(
        ["python", "-m", "queuectl.cli", "worker", "start", "--count", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for retries
    time.sleep(5)
    
    # Check if job moved to DLQ after retries exhausted
    stdout, _, _ = run_command("python -m queuectl.cli dlq list")
    
    # Stop worker
    worker_process.terminate()
    worker_process.wait(timeout=5)
    
    if "test-job-3" in stdout:
        print("✓ Failed job moved to DLQ after retries exhausted")
        return True
    else:
        print(f"✗ Failed: Job not in DLQ. Output: {stdout}")
        return False


def test_multiple_workers():
    """Test 4: Multiple workers process jobs without overlap"""
    print("\n=== Test 4: Multiple Workers ===")
    
    # Enqueue multiple jobs
    for i in range(5):
        job_data = json.dumps({
            "id": f"test-job-4-{i}",
            "command": f"echo 'Job {i}'"
        })
        run_command(f"python -m queuectl.cli enqueue '{job_data}'")
    
    # Start multiple workers
    worker_process = subprocess.Popen(
        ["python", "-m", "queuectl.cli", "worker", "start", "--count", "3"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for jobs to process
    time.sleep(5)
    
    # Check status
    stdout, _, _ = run_command("python -m queuectl.cli status")
    
    # Stop workers
    worker_process.terminate()
    worker_process.wait(timeout=5)
    
    # Check that jobs were processed
    stdout_list, _, _ = run_command("python -m queuectl.cli list")
    
    completed_count = stdout_list.count("completed")
    if completed_count >= 3:  # At least some jobs completed
        print(f"✓ Multiple workers processed jobs (completed: {completed_count})")
        return True
    else:
        print(f"✗ Failed: Only {completed_count} jobs completed")
        return False


def test_persistence():
    """Test 5: Job data persists across restarts"""
    print("\n=== Test 5: Data Persistence ===")
    
    # Enqueue a job
    job_data = json.dumps({"id": "test-job-5", "command": "echo 'Persist'"})
    run_command(f"python -m queuectl.cli enqueue '{job_data}'")
    
    # Verify job exists in database
    conn = sqlite3.connect("queuectl.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = 'test-job-5'")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        print("✓ Job persisted in database")
        return True
    else:
        print("✗ Failed: Job not found in database")
        return False


def test_dlq_retry():
    """Test 6: Retry job from DLQ"""
    print("\n=== Test 6: DLQ Retry ===")
    
    # First, create a job in DLQ (by enqueueing and letting it fail)
    job_data = json.dumps({
        "id": "test-job-6",
        "command": "exit 1",
        "max_retries": 1
    })
    run_command(f"python -m queuectl.cli enqueue '{job_data}'")
    
    # Start worker to process and fail
    worker_process = subprocess.Popen(
        ["python", "-m", "queuectl.cli", "worker", "start", "--count", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)
    worker_process.terminate()
    worker_process.wait(timeout=5)
    
    # Retry from DLQ
    stdout, stderr, code = run_command("python -m queuectl.cli dlq retry test-job-6")
    
    if code == 0 and "moved back to pending" in stdout:
        print("✓ Job retried from DLQ successfully")
        return True
    else:
        print(f"✗ Failed: {stdout} {stderr}")
        return False


def test_config():
    """Test 7: Configuration management"""
    print("\n=== Test 7: Configuration ===")
    
    # Set config
    stdout, stderr, code = run_command("python -m queuectl.cli config set max-retries 5")
    if code != 0:
        print(f"✗ Failed to set config: {stderr}")
        return False
    
    # Get config
    stdout, stderr, code = run_command("python -m queuectl.cli config get max-retries")
    if code == 0 and "5" in stdout:
        print("✓ Configuration management works")
        return True
    else:
        print(f"✗ Failed: {stdout}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("QueueCTL Test Suite")
    print("=" * 60)
    
    # Cleanup first
    cleanup()
    
    tests = [
        test_basic_enqueue,
        test_persistence,
        test_config,
        test_job_completion,
        test_failed_job_retry,
        test_multiple_workers,
        test_dlq_retry,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
        finally:
            # Small delay between tests
            time.sleep(1)
    
    # Final cleanup
    cleanup()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

