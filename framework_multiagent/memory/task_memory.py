"""
Task Memory using SQLite
Persistent storage for tasks and execution history
"""
import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Tuple, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH

class TaskMemory:
    def __init__(self, db_path: str = DATABASE_PATH):
        """Initialize task memory with SQLite database"""
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    task_data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    result TEXT,
                    error_message TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)
            conn.commit()

    def add_task(self, task_type: str, task_data: Dict[str, Any]) -> int:
        """Add a new task to memory"""
        with self.lock:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (task_type, task_data) VALUES (?, ?)",
                    (task_type, json.dumps(task_data))
                )
                task_id = cursor.lastrowid
                conn.commit()
                
                # Log the task creation
                self.log_action(task_id, "created", f"Task {task_type} added to queue")
                
                print(f"📝 Task {task_id} added: {task_type}")
                return task_id

    def get_pending_tasks(self) -> List[Tuple[int, str, Dict[str, Any]]]:
        """Get all pending tasks"""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, task_type, task_data FROM tasks WHERE status = 'pending' ORDER BY created_at"
            )
            results = []
            for row in cursor.fetchall():
                task_id, task_type, task_data_str = row
                task_data = json.loads(task_data_str)
                results.append((task_id, task_type, task_data))
            return results

    def mark_task_completed(self, task_id: int, result: str = None):
        """Mark a task as completed"""
        with self.lock:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute(
                    "UPDATE tasks SET status = 'completed', updated_at = CURRENT_TIMESTAMP, result = ? WHERE id = ?",
                    (result, task_id)
                )
                conn.commit()
                
                self.log_action(task_id, "completed", result or "Task completed successfully")
                print(f"✅ Task {task_id} completed")

    def mark_task_failed(self, task_id: int, error_message: str):
        """Mark a task as failed"""
        with self.lock:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute(
                    "UPDATE tasks SET status = 'failed', updated_at = CURRENT_TIMESTAMP, error_message = ? WHERE id = ?",
                    (error_message, task_id)
                )
                conn.commit()
                
                self.log_action(task_id, "failed", error_message)
                print(f"❌ Task {task_id} failed: {error_message}")

    def log_action(self, task_id: int, action: str, details: str = None):
        """Log an action for a task"""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.execute(
                "INSERT INTO execution_log (task_id, action, details) VALUES (?, ?, ?)",
                (task_id, action, details)
            )
            conn.commit()

    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task history"""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, task_type, task_data, status, created_at, updated_at, result, error_message
                FROM tasks 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'task_type': row[1],
                    'task_data': json.loads(row[2]),
                    'status': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'result': row[6],
                    'error_message': row[7]
                })
            return results

    def get_stats(self) -> Dict[str, int]:
        """Get task execution statistics"""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            cursor = conn.cursor()
            
            # Get counts by status
            cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM tasks")
            total = cursor.fetchone()[0]
            
            return {
                'total': total,
                'pending': status_counts.get('pending', 0),
                'completed': status_counts.get('completed', 0),
                'failed': status_counts.get('failed', 0)
            }

    def clear_completed_tasks(self, older_than_days: int = 7):
        """Clear old completed tasks"""
        with self.lock:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute("""
                    DELETE FROM tasks 
                    WHERE status = 'completed' 
                    AND updated_at < datetime('now', '-{} days')
                """.format(older_than_days))
                conn.commit()
                print(f"🧹 Cleared completed tasks older than {older_than_days} days")

# Global memory instance
memory = TaskMemory()