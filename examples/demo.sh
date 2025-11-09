#!/bin/bash
# Demo script for QueueCTL

echo "=== QueueCTL Demo ==="
echo ""

# Clean up any existing database
rm -f queuectl.db

echo "1. Enqueue some jobs..."
python -m queuectl.cli enqueue '{"id":"job1","command":"echo Hello from job1"}'
python -m queuectl.cli enqueue '{"id":"job2","command":"sleep 1 && echo Hello from job2"}'
python -m queuectl.cli enqueue '{"id":"job3","command":"echo Hello from job3"}'

echo ""
echo "2. Check status..."
python -m queuectl.cli status

echo ""
echo "3. List pending jobs..."
python -m queuectl.cli list --state pending

echo ""
echo "4. Start a worker in the background..."
python -m queuectl.cli worker start --count 1 &
WORKER_PID=$!

echo "Waiting for jobs to process..."
sleep 5

echo ""
echo "5. Check status again..."
python -m queuectl.cli status

echo ""
echo "6. List completed jobs..."
python -m queuectl.cli list --state completed

echo ""
echo "7. Test failed job with retries..."
python -m queuectl.cli enqueue '{"id":"failed-job","command":"exit 1","max_retries":2}'

sleep 8

echo ""
echo "8. Check DLQ..."
python -m queuectl.cli dlq list

echo ""
echo "9. Retry job from DLQ..."
python -m queuectl.cli dlq retry failed-job

echo ""
echo "10. Check configuration..."
python -m queuectl.cli config get

echo ""
echo "11. Set new configuration..."
python -m queuectl.cli config set max-retries 5

echo ""
echo "12. Final status..."
python -m queuectl.cli status

# Stop worker
kill $WORKER_PID 2>/dev/null
python -m queuectl.cli worker stop

echo ""
echo "=== Demo Complete ==="

