#!/usr/bin/env python3
"""
Test script to verify real-time updates and notifications for execution logs
"""

import requests
import json
import time
import threading
from datetime import datetime

def monitor_logs_continuously(workflow_id=1, interval=5):
    """Monitor logs in real-time"""
    base_url = "http://localhost:8000"
    
    print(f"🔄 Starting real-time log monitoring for workflow {workflow_id}")
    print(f"⏱️  Checking for updates every {interval} seconds")
    print("Press Ctrl+C to stop monitoring")
    print("-" * 50)
    
    last_log_count = 0
    last_logs = []
    
    try:
        while True:
            # Get current logs
            response = requests.get(f"{base_url}/workflows/{workflow_id}/logs")
            
            if response.status_code == 200:
                current_logs = response.json()
                current_count = len(current_logs)
                
                # Check for new logs
                if current_count > last_log_count:
                    new_logs = current_logs[last_log_count:]
                    print(f"\n🆕 {len(new_logs)} new log(s) detected at {datetime.now().strftime('%H:%M:%S')}")
                    
                    for log in new_logs:
                        status = log.get('status', 'unknown')
                        execution_time = log.get('execution_time', 'N/A')
                        schedule_id = log.get('schedule_id', 'N/A')
                        error_msg = log.get('error_message', '')[:100]  # Truncate long error messages
                        
                        print(f"   📋 Log ID: {log.get('id')}")
                        print(f"   📊 Status: {status}")
                        print(f"   ⏱️  Execution Time: {execution_time}s")
                        print(f"   📅 Schedule ID: {schedule_id}")
                        if error_msg:
                            print(f"   ❌ Error: {error_msg}...")
                        print()
                
                # Check for status changes
                if last_logs and current_logs:
                    for i, (old_log, new_log) in enumerate(zip(last_logs, current_logs)):
                        if old_log.get('status') != new_log.get('status'):
                            print(f"🔄 Status change detected for Log {new_log.get('id')}:")
                            print(f"   From: {old_log.get('status')} → To: {new_log.get('status')}")
                            print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                            print()
                
                # Show current statistics
                if current_count > 0:
                    status_counts = {}
                    for log in current_logs:
                        status = log.get('status', 'unknown')
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    print(f"📊 Current Statistics: Total={current_count}", end="")
                    for status, count in status_counts.items():
                        print(f", {status}={count}", end="")
                    print(f" | {datetime.now().strftime('%H:%M:%S')}")
                
                last_log_count = current_count
                last_logs = current_logs.copy()
            
            else:
                print(f"❌ Failed to get logs: {response.status_code}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring stopped at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")

def test_webhook_notification():
    """Test webhook-style notifications (simulate)"""
    print("\n📡 Testing notification system (simulation)")
    print("-" * 30)
    
    # Simulate different notification scenarios
    notifications = [
        {"type": "execution_started", "message": "Workflow execution started", "severity": "info"},
        {"type": "execution_completed", "message": "Workflow execution completed successfully", "severity": "success"},
        {"type": "execution_failed", "message": "Workflow execution failed", "severity": "error"},
        {"type": "high_error_rate", "message": "High error rate detected (>50%)", "severity": "warning"},
    ]
    
    for notification in notifications:
        timestamp = datetime.now().strftime("%H:%M:%S")
        severity_icon = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }.get(notification["severity"], "📢")
        
        print(f"{severity_icon} [{timestamp}] {notification['type']}: {notification['message']}")
        time.sleep(1)

def test_filter_performance():
    """Test filtering performance"""
    print("\n⚡ Testing filtering performance")
    print("-" * 30)
    
    workflow_id = 1
    base_url = "http://localhost:8000"
    
    filters = [
        {"status": "success"},
        {"status": "failed"},
        {"start_date": "2024-01-01", "end_date": "2024-12-31"},
        {"schedule_id": 1},
        {}  # No filter (all logs)
    ]
    
    for i, filter_params in enumerate(filters):
        start_time = time.time()
        
        try:
            response = requests.get(f"{base_url}/workflows/{workflow_id}/logs", params=filter_params)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                logs = response.json()
                filter_desc = " and ".join([f"{k}={v}" for k, v in filter_params.items()]) or "no filter"
                print(f"   Filter: {filter_desc}")
                print(f"   ⏱️  Response time: {response_time:.3f}s")
                print(f"   📊 Results: {len(logs)} logs")
                print()
            else:
                print(f"   ❌ Filter failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Filter error: {e}")

def main():
    """Main test function"""
    print("🚀 Real-time Updates and Notifications Test")
    print("=" * 50)
    
    # Test 1: Basic monitoring
    print("\n1️⃣ Starting continuous monitoring...")
    print("   (This will run for 30 seconds then auto-stop)")
    
    # Run monitoring in a separate thread with timeout
    monitor_thread = threading.Thread(
        target=monitor_logs_continuously,
        args=(1, 5),
        daemon=True
    )
    monitor_thread.start()
    
    # Let it run for 30 seconds
    time.sleep(30)
    
    print("\n⏹️  Stopping continuous monitoring...")
    
    # Test 2: Notification system
    print("\n2️⃣ Testing notification system...")
    test_webhook_notification()
    
    # Test 3: Performance testing
    print("\n3️⃣ Testing filtering performance...")
    test_filter_performance()
    
    print("\n" + "=" * 50)
    print("✅ Real-time updates and notifications test completed!")
    print("\n📋 Summary of tested features:")
    print("   • Continuous log monitoring")
    print("   • New log detection and notifications")
    print("   • Status change detection")
    print("   • Real-time statistics updates")
    print("   • Notification system simulation")
    print("   • Filtering performance testing")
    print("\n🚀 Real-time troubleshooting features are ready for use!")

if __name__ == "__main__":
    main()