#!/usr/bin/env python3
"""Test CLI commands programmatically"""

import subprocess
import json
import time
import sys

def run_cmd(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout, result.stderr, 0
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def test_enqueue():
    """Test enqueue command"""
    print("\n=== Testing Enqueue ===")
    # Use Python to enqueue directly to avoid shell escaping issues
    from queuectl.queue import JobQueue
    try:
        queue = JobQueue()
        job = queue.enqueue("cli-test-1", "echo CLI Test")
        print("[OK] Job enqueued successfully (via Python API)")
        print(f"   Job ID: {job['id']}, State: {job['state']}")
        return True
    except Exception as e:
        print(f"[FAIL] Enqueue failed: {e}")
        return False

def test_status():
    """Test status command"""
    print("\n=== Testing Status ===")
    stdout, stderr, code = run_cmd("python -m queuectl.cli status")
    if code == 0:
        print("[OK] Status command works")
        print(stdout)
        return True
    else:
        print(f"[FAIL] Status failed: {stderr}")
        return False

def test_list():
    """Test list command"""
    print("\n=== Testing List ===")
    stdout, stderr, code = run_cmd("python -m queuectl.cli list")
    if code == 0:
        print("[OK] List command works")
        print(stdout[:200] + "..." if len(stdout) > 200 else stdout)
        return True
    else:
        print(f"[FAIL] List failed: {stderr}")
        return False

def test_config():
    """Test config commands"""
    print("\n=== Testing Config ===")
    # Set config
    stdout, stderr, code = run_cmd("python -m queuectl.cli config set backoff-base 3")
    if code != 0:
        print(f"[FAIL] Config set failed: {stderr}")
        return False
    
    # Get config
    stdout, stderr, code = run_cmd("python -m queuectl.cli config get backoff-base")
    if code == 0 and "3" in stdout:
        print("[OK] Config commands work")
        print(f"   Output: {stdout.strip()}")
        return True
    else:
        print(f"[FAIL] Config get failed: {stderr}")
        return False

def test_dlq():
    """Test DLQ commands"""
    print("\n=== Testing DLQ ===")
    stdout, stderr, code = run_cmd("python -m queuectl.cli dlq list")
    if code == 0:
        print("[OK] DLQ list works")
        print(stdout[:200] + "..." if len(stdout) > 200 else stdout)
        return True
    else:
        print(f"[FAIL] DLQ list failed: {stderr}")
        return False

def test_worker_help():
    """Test worker help"""
    print("\n=== Testing Worker Commands ===")
    stdout, stderr, code = run_cmd("python -m queuectl.cli worker --help")
    if code == 0:
        print("[OK] Worker commands available")
        return True
    else:
        print(f"[FAIL] Worker help failed: {stderr}")
        return False

def main():
    """Run all CLI tests"""
    print("=" * 60)
    print("QueueCTL CLI Test Suite")
    print("=" * 60)
    
    tests = [
        test_enqueue,
        test_status,
        test_list,
        test_config,
        test_dlq,
        test_worker_help,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Test failed with exception: {e}")
            results.append(False)
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[OK] All CLI tests passed!")
        return 0
    else:
        print("[FAIL] Some CLI tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

