"""
Follow-up Scheduler
Background worker that processes pending tasks automatically
"""
import time
import threading
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.task_memory import memory
from graph.agent_graph import execute_task

class TaskScheduler:
    def __init__(self, check_interval: int = 10):
        """
        Initialize the task scheduler
        
        Args:
            check_interval: How often to check for pending tasks (seconds)
        """
        self.check_interval = check_interval
        self.running = False
        self.thread = None

    def start(self):
        """Start the background scheduler"""
        if self.running:
            print("⚠️ Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        print(f"🔄 Task scheduler started (checking every {self.check_interval}s)")

    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("⏹️ Task scheduler stopped")

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                self._process_pending_tasks()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(self.check_interval)

    def _process_pending_tasks(self):
        """Process all pending tasks"""
        pending_tasks = memory.get_pending_tasks()
        
        if not pending_tasks:
            return
        
        print(f"\n📋 Processing {len(pending_tasks)} pending tasks...")
        
        for task_id, task_type, task_data in pending_tasks:
            try:
                print(f"\n🔄 Processing task {task_id}: {task_type}")
                
                # Execute the task using the agent graph
                result = execute_task(task_id, task_type, task_data)
                
                if result.get("error"):
                    print(f"❌ Task {task_id} failed: {result['error']}")
                else:
                    print(f"✅ Task {task_id} completed: {result.get('result', 'Success')}")
                
            except Exception as e:
                error_msg = f"Scheduler execution error: {str(e)}"
                print(f"❌ Task {task_id} failed: {error_msg}")
                memory.mark_task_failed(task_id, error_msg)

    def process_single_task(self, task_id: int, task_type: str, task_data: Dict[str, Any]):
        """Process a single task immediately"""
        try:
            print(f"\n⚡ Immediate execution of task {task_id}: {task_type}")
            result = execute_task(task_id, task_type, task_data)
            
            if result.get("error"):
                print(f"❌ Task {task_id} failed: {result['error']}")
                return False
            else:
                print(f"✅ Task {task_id} completed: {result.get('result', 'Success')}")
                return True
                
        except Exception as e:
            error_msg = f"Immediate execution error: {str(e)}"
            print(f"❌ Task {task_id} failed: {error_msg}")
            memory.mark_task_failed(task_id, error_msg)
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics"""
        stats = memory.get_stats()
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "task_stats": stats
        }

# Global scheduler instance
scheduler = TaskScheduler()

def start_scheduler():
    """Start the global scheduler"""
    scheduler.start()

def stop_scheduler():
    """Stop the global scheduler"""
    scheduler.stop()

def process_task_immediately(task_id: int, task_type: str, task_data: Dict[str, Any]) -> bool:
    """Process a task immediately without waiting for scheduler"""
    return scheduler.process_single_task(task_id, task_type, task_data)