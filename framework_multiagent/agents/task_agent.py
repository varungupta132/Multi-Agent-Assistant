"""
Task Management Agent - Live Time Tracking with AI Estimation
Integrates with existing multi-agent framework for task monitoring and alerts
"""
from langchain_core.tools import tool
from datetime import datetime, timedelta
import json
import sqlite3
import threading
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH
from llm.message_generator import MessageGenerator

class TaskDatabase:
    """Database manager for tasks"""
    
    def __init__(self, db_path="tasks.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize task database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing table if it has wrong schema
        cursor.execute("DROP TABLE IF EXISTS tasks")
        
        cursor.execute('''
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                description TEXT,
                estimated_duration INTEGER,
                start_time TEXT,
                estimated_end_time TEXT,
                deadline TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                actual_duration INTEGER,
                alerts_sent TEXT DEFAULT ''
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Task database initialized: {self.db_path}")
    
    def add_task(self, task_name, description, estimated_duration, deadline=None):
        """Add new task to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_time = datetime.now().isoformat()
        estimated_end_time = (datetime.now() + timedelta(minutes=estimated_duration)).isoformat()
        
        cursor.execute('''
            INSERT INTO tasks (task_name, description, estimated_duration, start_time, estimated_end_time, deadline)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_name, description, estimated_duration, start_time, estimated_end_time, deadline))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Task added to database: ID {task_id}, Name: {task_name}")
        return task_id
    
    def get_active_tasks(self):
        """Get all active (pending) tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at DESC
        ''')
        
        tasks = cursor.fetchall()
        conn.close()
        
        print(f"📋 Retrieved {len(tasks)} active tasks from database")
        return tasks
    
    def update_task_status(self, task_id, status, completed_at=None):
        """Update task status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == 'completed' and completed_at:
            cursor.execute('''
                UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?
            ''', (status, completed_at, task_id))
        else:
            cursor.execute('''
                UPDATE tasks SET status = ? WHERE id = ?
            ''', (status, task_id))
        
        conn.commit()
        conn.close()
        print(f"✅ Task {task_id} status updated to: {status}")

class TaskTimeTracker:
    """Live time tracking for tasks"""
    
    def __init__(self):
        self.db = TaskDatabase()
        self.message_generator = MessageGenerator()
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start background monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_tasks, daemon=True)
            self.monitor_thread.start()
            print("🔄 Task monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("⏹️ Task monitoring stopped")
    
    def _monitor_tasks(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                self._check_task_alerts()
                
                # Check more frequently for short tasks
                active_tasks = self.db.get_active_tasks()
                has_short_tasks = any(
                    int(task[3]) <= 10 for task in active_tasks  # duration <= 10 minutes
                ) if active_tasks else False
                
                if has_short_tasks:
                    time.sleep(10)  # Check every 10 seconds for short tasks
                    print("⚡ Fast monitoring for short tasks (10s interval)")
                else:
                    time.sleep(30)  # Check every 30 seconds for longer tasks
                    print("🔄 Normal monitoring (30s interval)")
                    
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_task_alerts(self):
        """Check tasks for alerts and send notifications"""
        try:
            tasks = self.db.get_active_tasks()
            current_time = datetime.now()
            
            print(f"🔍 Checking {len(tasks)} tasks for alerts at {current_time.strftime('%H:%M:%S')}")
            
            for task in tasks:
                try:
                    # Unpack task data properly
                    if len(task) >= 11:  # Old format without alerts_sent
                        task_id, name, desc, duration, start_time, est_end, deadline, status, created, completed, actual = task[:11]
                    else:  # New format with alerts_sent
                        task_id, name, desc, duration, start_time, est_end, deadline, status, created, completed, actual, alerts_sent = task
                    
                    start_dt = datetime.fromisoformat(start_time)
                    est_end_dt = datetime.fromisoformat(est_end)
                    
                    # Calculate live timing
                    elapsed_minutes = (current_time - start_dt).total_seconds() / 60
                    remaining_minutes = (est_end_dt - current_time).total_seconds() / 60
                    
                    print(f"📋 Task '{name}': {remaining_minutes:.1f} minutes remaining")
                    
                    # Check for different alert conditions
                    if 0 < remaining_minutes <= 1:
                        # 1 minute warning (only send once)
                        alert_key = f"1min_{task_id}"
                        if not hasattr(self, '_sent_alerts'):
                            self._sent_alerts = set()
                        
                        if alert_key not in self._sent_alerts:
                            self._send_alert(name, f"⚠️ URGENT: Only 1 minute left for task '{name}'! Finish up quickly!")
                            self._sent_alerts.add(alert_key)
                    
                    elif 0 < remaining_minutes <= 5 and duration > 10:
                        # 5 minute warning for longer tasks
                        alert_key = f"5min_{task_id}"
                        if not hasattr(self, '_sent_alerts'):
                            self._sent_alerts = set()
                        
                        if alert_key not in self._sent_alerts:
                            self._send_alert(name, f"⚠️ Warning: 5 minutes left for task '{name}'. Start wrapping up!")
                            self._sent_alerts.add(alert_key)
                    
                    elif remaining_minutes <= 0:
                        # Time exceeded - send alert every time we check (but limit frequency)
                        exceeded_minutes = abs(remaining_minutes)
                        alert_key = f"exceeded_{task_id}"
                        
                        if not hasattr(self, '_sent_alerts'):
                            self._sent_alerts = set()
                        
                        if alert_key not in self._sent_alerts:
                            if exceeded_minutes < 1:
                                message = f"🔴 TIME UP! Task '{name}' time has finished! You should complete it now."
                            else:
                                message = f"🔴 OVERDUE! Task '{name}' exceeded by {int(exceeded_minutes)} minutes. Please complete ASAP!"
                            
                            self._send_alert(name, message)
                            self._sent_alerts.add(alert_key)
                            
                            # Mark as exceeded in database for UI
                            self.db.update_task_status(task_id, 'exceeded')
                
                except Exception as task_error:
                    print(f"❌ Error checking task {task_id}: {task_error}")
                    continue
                    
        except Exception as e:
            print(f"❌ Alert checking error: {e}")
    
    def _send_alert(self, task_name, message):
        """Send alert via existing communication agents"""
        try:
            print(f"📱 Sending alert: {message}")
            
            # Use existing WhatsApp agent for alerts
            from agents.whatsapp_agent import send_whatsapp_simple
            result = send_whatsapp_simple(
                to="",  # Uses default recipient
                user_request=f"Task time alert: {message}",
                message=""
            )
            print(f"✅ Alert sent successfully: {message}")
            return True
            
        except Exception as e:
            print(f"❌ Alert sending failed: {e}")
            
            # Fallback: try email alert
            try:
                from agents.email_agent import send_email
                email_result = send_email.invoke({
                    "to": "",  # Uses default recipient
                    "user_request": f"Task Alert: {message}",
                    "subject": f"Task Alert: {task_name}",
                    "body": message
                })
                print(f"📧 Fallback email alert sent: {message}")
                return True
            except Exception as email_error:
                print(f"❌ Email alert also failed: {email_error}")
                return False
    
    def get_live_task_data(self):
        """Get live task data with timing calculations"""
        try:
            tasks = self.db.get_active_tasks()
            current_time = datetime.now()
            live_tasks = []
            
            print(f"🔄 Processing {len(tasks)} active tasks for live data...")
            
            for task in tasks:
                try:
                    # Unpack task data properly
                    if len(task) >= 11:  # Old format without alerts_sent
                        task_id, name, desc, duration, start_time, est_end, deadline, status, created, completed, actual = task[:11]
                    else:  # New format with alerts_sent
                        task_id, name, desc, duration, start_time, est_end, deadline, status, created, completed, actual, alerts_sent = task
                    
                    print(f"🔄 Processing task ID {task_id}: {name}")
                    
                    start_dt = datetime.fromisoformat(start_time)
                    est_end_dt = datetime.fromisoformat(est_end)
                    
                    # Calculate live timing
                    elapsed_minutes = (current_time - start_dt).total_seconds() / 60
                    remaining_minutes = (est_end_dt - current_time).total_seconds() / 60
                    
                    # Determine status
                    if remaining_minutes > 30:
                        live_status = "🟢 On Track"
                    elif remaining_minutes > 0:
                        live_status = "🟡 At Risk"
                    else:
                        live_status = f"🔴 Exceeded by {int(abs(remaining_minutes))}m"
                    
                    # Format remaining time
                    if remaining_minutes > 0:
                        hours = int(remaining_minutes // 60)
                        mins = int(remaining_minutes % 60)
                        time_left = f"{hours}h {mins}m left" if hours > 0 else f"{mins}m left"
                    else:
                        time_left = f"Exceeded by {int(abs(remaining_minutes))}m"
                    
                    live_tasks.append({
                        'id': task_id,
                        'name': name,
                        'description': desc or '',
                        'start_time': start_dt.strftime('%I:%M %p'),
                        'estimated_end': est_end_dt.strftime('%I:%M %p'),
                        'elapsed_minutes': int(elapsed_minutes),
                        'remaining_minutes': int(remaining_minutes),
                        'time_left': time_left,
                        'live_status': live_status,
                        'progress_percentage': min(100, max(0, (elapsed_minutes / duration) * 100)) if duration > 0 else 0
                    })
                    
                except Exception as task_error:
                    print(f"❌ Error processing task: {task_error}")
                    print(f"   Task data: {task}")
                    continue
            
            print(f"✅ Successfully processed {len(live_tasks)} tasks")
            return live_tasks
            
        except Exception as e:
            print(f"❌ Error getting live task data: {e}")
            return []

# Global task tracker instance
task_tracker = TaskTimeTracker()

@tool
def parse_smart_task_input(user_input: str) -> dict:
    """
    Parse natural language task input and extract task details
    
    Args:
        user_input: Natural language input like "add ML assignment for 2 hours"
    
    Returns:
        Dictionary with parsed task details
    """
    try:
        print(f"🧠 Parsing smart input: {user_input[:100]}...")
        
        # Initialize defaults
        task_name = ""
        task_description = ""
        duration_minutes = 60  # Default 1 hour
        
        # Simple keyword extraction (fallback)
        user_lower = user_input.lower()
        
        # Extract duration from text
        import re
        
        # Look for time patterns (more precise for short durations)
        time_patterns = [
            # Minutes patterns (most specific first)
            (r'(\d+)\s*minutes?', lambda x: int(x)),
            (r'(\d+)\s*mins?', lambda x: int(x)),
            (r'(\d+)\s*m(?!\w)', lambda x: int(x)),
            (r'(\d+)\s*minute', lambda x: int(x)),
            (r'(\d+)\s*min', lambda x: int(x)),
            
            # Hours patterns
            (r'(\d+)\s*hours?', lambda x: int(x) * 60),
            (r'(\d+)\s*hrs?', lambda x: int(x) * 60),
            (r'(\d+)\s*h(?!\w)', lambda x: int(x) * 60),
            (r'(\d+\.5)\s*hours?', lambda x: int(float(x) * 60)),
            
            # Word patterns
            (r'\bone\s*minute\b', lambda x: 1),
            (r'\btwo\s*minutes?\b', lambda x: 2),
            (r'\bthree\s*minutes?\b', lambda x: 3),
            (r'\bfour\s*minutes?\b', lambda x: 4),
            (r'\bfive\s*minutes?\b', lambda x: 5),
            (r'\bten\s*minutes?\b', lambda x: 10),
            (r'\bfifteen\s*minutes?\b', lambda x: 15),
            (r'\btwenty\s*minutes?\b', lambda x: 20),
            (r'\bthirty\s*minutes?\b', lambda x: 30),
            (r'\bhalf\s*hour\b', lambda x: 30),
            (r'\bone\s*hour\b', lambda x: 60),
            (r'\btwo\s*hours?\b', lambda x: 120),
            (r'\bthree\s*hours?\b', lambda x: 180),
        ]
        
        # Try patterns in order (most specific first)
        for pattern, converter in time_patterns:
            match = re.search(pattern, user_lower)
            if match:
                try:
                    if 'one minute' in pattern or 'two minutes' in pattern or 'three minutes' in pattern:
                        duration_minutes = converter(None)
                    elif '\\d+' in pattern:
                        duration_minutes = converter(match.group(1))
                    else:
                        duration_minutes = converter(None)
                    
                    print(f"⏰ Extracted duration: {duration_minutes} minutes from pattern: {pattern}")
                    break
                except Exception as e:
                    print(f"⚠️ Pattern match failed: {e}")
                    continue
        
        # Try AI parsing for better results
        try:
            from llm.message_generator import MessageGenerator
            message_generator = MessageGenerator()
            
            parsing_prompt = f"""
            Parse this task request and extract EXACT details: "{user_input}"
            
            IMPORTANT: Pay special attention to the EXACT time mentioned!
            
            Extract:
            1. Task name (short, clear title)
            2. Task description (detailed, professional)  
            3. EXACT duration in minutes (be precise!)
            
            Format your response as:
            TASK_NAME: [clear task title]
            DESCRIPTION: [detailed professional description]
            DURATION: [exact number] minutes
            
            Examples:
            Input: "add task for 1 minute"
            TASK_NAME: Quick Task
            DESCRIPTION: Complete a quick task within one minute. Focus on efficiency and immediate completion.
            DURATION: 1 minutes
            
            Input: "finish work in 2 minutes"
            TASK_NAME: Finish Work
            DESCRIPTION: Complete any outstanding work tasks within 2 minutes. Focus on quick completion and quality delivery.
            DURATION: 2 minutes
            
            Input: "add ML assignment for 2 hours"
            TASK_NAME: Machine Learning Assignment
            DESCRIPTION: Complete the machine learning assignment including research, implementation, and documentation.
            DURATION: 120 minutes
            
            Input: "study for 30 minutes"
            TASK_NAME: Study Session
            DESCRIPTION: Focused study session covering key topics and concepts for effective learning.
            DURATION: 30 minutes
            
            CRITICAL: If the user says "1 minute" output "DURATION: 1 minutes"
            CRITICAL: If the user says "2 minutes" output "DURATION: 2 minutes"
            CRITICAL: If the user says "5 minutes" output "DURATION: 5 minutes"
            
            Your parsing:
            """
            
            response = message_generator.llm.invoke(parsing_prompt)
            
            # Parse AI response
            lines = response.strip().split('\n')
            ai_duration_found = False
            
            for line in lines:
                if 'TASK_NAME:' in line:
                    ai_name = line.split('TASK_NAME:')[-1].strip()
                    if ai_name and len(ai_name) > 3:
                        task_name = ai_name
                elif 'DESCRIPTION:' in line:
                    ai_desc = line.split('DESCRIPTION:')[-1].strip()
                    if ai_desc and len(ai_desc) > 10:
                        task_description = ai_desc
                elif 'DURATION:' in line:
                    try:
                        # Extract number more carefully
                        duration_text = line.split('DURATION:')[-1].strip()
                        ai_duration = int(''.join(filter(str.isdigit, duration_text)))
                        if 1 <= ai_duration <= 480:  # 1 minute to 8 hours
                            # If we already found a duration from regex, compare and use the more specific one
                            if duration_minutes == 60:  # Default value, use AI
                                duration_minutes = ai_duration
                                ai_duration_found = True
                                print(f"🤖 Using AI duration: {ai_duration} minutes")
                            elif abs(duration_minutes - ai_duration) <= 5:  # Close match, use regex
                                print(f"🎯 Regex and AI agree: {duration_minutes} minutes")
                            else:
                                # Prefer regex for short durations, AI for longer ones
                                if duration_minutes <= 10:
                                    print(f"🎯 Using regex for short duration: {duration_minutes} minutes")
                                else:
                                    duration_minutes = ai_duration
                                    ai_duration_found = True
                                    print(f"🤖 Using AI for longer duration: {ai_duration} minutes")
                    except Exception as parse_error:
                        print(f"⚠️ AI duration parsing failed: {parse_error}")
            
            if ai_duration_found:
                print(f"🤖 AI parsing successful with duration: {duration_minutes} minutes")
            else:
                print(f"🎯 Using regex duration: {duration_minutes} minutes")
            
        except Exception as ai_error:
            print(f"⚠️ AI parsing failed, using fallback: {ai_error}")
        
        # Fallback extraction if AI failed
        if not task_name:
            # Extract task name from input
            # Remove time-related words and common prefixes
            clean_input = user_input
            for remove_word in ['add', 'create', 'for', 'hours', 'hour', 'minutes', 'mins', 'h', 'm']:
                clean_input = re.sub(rf'\b{remove_word}\b', '', clean_input, flags=re.IGNORECASE)
            
            # Remove numbers and clean up
            clean_input = re.sub(r'\d+', '', clean_input)
            clean_input = re.sub(r'\s+', ' ', clean_input).strip()
            
            if clean_input:
                task_name = clean_input.title()
            else:
                task_name = "New Task"
        
        if not task_description:
            task_description = f"Complete the task: {task_name}"
        
        result = {
            "task_name": task_name,
            "task_description": task_description,
            "duration_minutes": duration_minutes,
            "original_input": user_input
        }
        
        print(f"✅ Parsed task: {task_name} ({duration_minutes}min)")
        return result
        
    except Exception as e:
        print(f"❌ Parsing error: {e}")
        return {
            "task_name": "New Task",
            "task_description": user_input,
            "duration_minutes": 60,
            "original_input": user_input,
            "error": str(e)
        }
    """
    Use AI to estimate how long a task will take to complete
    
    Args:
        task_description: Description of the task to estimate
    
    Returns:
        Dictionary with estimated duration and breakdown
    """
    try:
        print(f"🧠 Estimating duration for: {task_description[:50]}...")
        
        # Simple fallback estimation based on keywords
        duration = 60  # Default 1 hour
        breakdown = "Standard task estimation"
        confidence = "Medium"
        
        # Keyword-based estimation (fallback if AI fails)
        task_lower = task_description.lower()
        
        if any(word in task_lower for word in ['assignment', 'report', 'research', 'write', 'document']):
            if any(word in task_lower for word in ['page', 'pages', 'long', 'detailed']):
                duration = 120  # 2 hours for detailed writing
                breakdown = "Research (40min) + Writing (60min) + Review (20min)"
            else:
                duration = 90   # 1.5 hours for regular writing
                breakdown = "Research (30min) + Writing (45min) + Review (15min)"
        
        elif any(word in task_lower for word in ['code', 'program', 'develop', 'build', 'implement']):
            if any(word in task_lower for word in ['project', 'system', 'application']):
                duration = 180  # 3 hours for projects
                breakdown = "Planning (30min) + Coding (120min) + Testing (30min)"
            else:
                duration = 75   # 1.25 hours for simple coding
                breakdown = "Planning (15min) + Coding (45min) + Testing (15min)"
        
        elif any(word in task_lower for word in ['study', 'learn', 'read', 'review']):
            duration = 45   # 45 minutes for studying
            breakdown = "Reading (30min) + Notes (15min)"
        
        elif any(word in task_lower for word in ['meeting', 'call', 'discussion']):
            duration = 30   # 30 minutes for meetings
            breakdown = "Preparation (10min) + Meeting (20min)"
        
        elif any(word in task_lower for word in ['fix', 'debug', 'solve', 'troubleshoot']):
            duration = 60   # 1 hour for debugging
            breakdown = "Investigation (30min) + Fix (20min) + Test (10min)"
        
        # Try AI estimation if available
        try:
            from llm.message_generator import MessageGenerator
            message_generator = MessageGenerator()
            
            estimation_prompt = f"""
            Estimate how long this task will take: "{task_description}"
            
            Respond with only:
            DURATION: [number] minutes
            BREAKDOWN: [brief explanation]
            CONFIDENCE: [High/Medium/Low]
            
            Example:
            DURATION: 90 minutes
            BREAKDOWN: Research (30min) + Writing (45min) + Review (15min)
            CONFIDENCE: High
            """
            
            response = message_generator.llm.invoke(estimation_prompt)
            
            # Parse AI response
            lines = response.strip().split('\n')
            for line in lines:
                if 'DURATION:' in line:
                    try:
                        ai_duration = int(''.join(filter(str.isdigit, line)))
                        if 5 <= ai_duration <= 480:  # Reasonable bounds
                            duration = ai_duration
                    except:
                        pass
                elif 'BREAKDOWN:' in line:
                    ai_breakdown = line.split('BREAKDOWN:')[-1].strip()
                    if ai_breakdown:
                        breakdown = ai_breakdown
                elif 'CONFIDENCE:' in line:
                    ai_confidence = line.split('CONFIDENCE:')[-1].strip()
                    if ai_confidence:
                        confidence = ai_confidence
            
            print(f"🤖 AI estimation successful: {duration} minutes")
            
        except Exception as ai_error:
            print(f"⚠️ AI estimation failed, using fallback: {ai_error}")
        
        result = {
            "estimated_duration": duration,
            "breakdown": breakdown,
            "confidence": confidence,
            "method": "AI + Fallback"
        }
        
        print(f"✅ Final estimation: {duration} minutes - {breakdown}")
        
        return result
        
    except Exception as e:
        print(f"❌ Estimation error: {e}")
        return {
            "estimated_duration": 60,
            "breakdown": "Default estimation (1 hour)",
            "confidence": "Low",
            "method": "Fallback only",
            "error": str(e)
        }

@tool
def create_task(task_name: str, task_description: str = "", deadline: str = "") -> str:
    """
    Create a new task with AI-estimated duration and start live tracking
    
    Args:
        task_name: Name of the task
        task_description: Detailed description of the task
        deadline: Optional deadline (format: YYYY-MM-DD HH:MM)
    
    Returns:
        Success message with task details
    """
    try:
        print(f"📝 Creating task: {task_name}")
        
        # Get AI estimation
        full_description = f"{task_name}. {task_description}".strip()
        estimation = estimate_task_duration.func(full_description)
        
        # Parse deadline
        deadline_dt = None
        if deadline:
            try:
                deadline_dt = datetime.strptime(deadline, '%Y-%m-%d %H:%M').isoformat()
            except:
                try:
                    # Try alternative format
                    deadline_dt = datetime.strptime(deadline, '%Y-%m-%dT%H:%M').isoformat()
                except:
                    print(f"⚠️ Invalid deadline format: {deadline}")
        
        # Add to database
        task_id = task_tracker.db.add_task(
            task_name=task_name,
            description=task_description,
            estimated_duration=estimation["estimated_duration"],
            deadline=deadline_dt
        )
        
        # Start monitoring if not already running
        task_tracker.start_monitoring()
        
        success_msg = f"""✅ Task created successfully!
        
📋 Task Details:
• ID: {task_id}
• Name: {task_name}
• Description: {task_description[:100]}{'...' if len(task_description) > 100 else ''}
• Estimated Duration: {estimation['estimated_duration']} minutes
• Breakdown: {estimation['breakdown']}
• Confidence: {estimation['confidence']}
• Method: {estimation.get('method', 'AI')}
• Live Tracking: ✅ Started
• Alerts: ✅ Enabled

🔄 The system will monitor this task and send WhatsApp alerts when:
• ⚠️ 10 minutes remaining
• ❌ Estimated time exceeded
• 📅 Deadline approaching"""
        
        print(success_msg)
        return success_msg
        
    except Exception as e:
        error_msg = f"❌ Task creation failed: {str(e)}"
        print(error_msg)
        print(f"🔍 Debug info: task_name='{task_name}', description='{task_description}', deadline='{deadline}'")
        return error_msg

@tool
def get_live_tasks() -> str:
    """
    Get all active tasks with live time tracking data
    
    Returns:
        Formatted string with live task information
    """
    try:
        live_tasks = task_tracker.get_live_task_data()
        
        if not live_tasks:
            return "📋 No active tasks found. Create a task to start tracking!"
        
        result = "📊 Live Task Dashboard\n" + "="*50 + "\n\n"
        
        for task in live_tasks:
            result += f"""📝 {task['name']}
⏰ Started: {task['start_time']} → Est. End: {task['estimated_end']}
⏳ Time Left: {task['time_left']}
📊 Status: {task['live_status']}
🔄 Progress: {task['progress_percentage']:.1f}%
{'─'*40}
"""
        
        result += f"\n🔄 Last updated: {datetime.now().strftime('%I:%M:%S %p')}"
        result += "\n💡 This data updates automatically every 30 seconds"
        
        print("📊 Live tasks retrieved")
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get live tasks: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def complete_task(task_id: int) -> str:
    """
    Mark a task as completed and stop tracking
    
    Args:
        task_id: ID of the task to complete
    
    Returns:
        Success message with completion details
    """
    try:
        completed_at = datetime.now().isoformat()
        task_tracker.db.update_task_status(task_id, 'completed', completed_at)
        
        success_msg = f"✅ Task {task_id} marked as completed at {datetime.now().strftime('%I:%M %p')}"
        print(success_msg)
        return success_msg
        
    except Exception as e:
        error_msg = f"❌ Failed to complete task: {str(e)}"
        print(error_msg)
        return error_msg

# Simple functions for direct use
def create_task_simple(task_name, description="", deadline=""):
    """Simple task creation function"""
    return create_task.func(task_name, description, deadline)

def get_live_tasks_simple():
    """Simple live tasks function"""
    return get_live_tasks.func()

def complete_task_simple(task_id):
    """Simple task completion function"""
    return complete_task.func(task_id)

# Test function
def test_task_agent():
    """Test the task agent functionality"""
    print("🧪 Testing Task Management Agent...")
    print("=" * 50)
    
    # Test task creation
    print("\n1. Creating test task...")
    result = create_task_simple(
        task_name="Complete ML Assignment",
        description="Finish the machine learning assignment on neural networks",
        deadline=""
    )
    print(result)
    
    # Test live tasks
    print("\n2. Getting live tasks...")
    live_tasks = get_live_tasks_simple()
    print(live_tasks)
    
    print("\n🎉 Task agent testing completed!")

if __name__ == "__main__":
    test_task_agent()

@tool
def create_smart_task(user_input: str, end_time: str = "") -> str:
    """
    Create a task from natural language input with smart parsing
    
    Args:
        user_input: Natural language like "add ML assignment for 2 hours"
        end_time: Optional end time (format: HH:MM), if not provided uses duration
    
    Returns:
        Success message with task details
    """
    try:
        print(f"🧠 Creating smart task from: {user_input}")
        
        # Parse the input
        parsed = parse_smart_task_input.func(user_input)
        
        # Calculate timing
        start_time = datetime.now()
        
        if end_time:
            # User provided end time
            try:
                end_hour, end_min = map(int, end_time.split(':'))
                end_dt = start_time.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
                
                # If end time is before start time, assume next day
                if end_dt <= start_time:
                    end_dt += timedelta(days=1)
                
                # Calculate duration
                duration_minutes = int((end_dt - start_time).total_seconds() / 60)
                
            except Exception as time_error:
                print(f"⚠️ Invalid end time format: {end_time}, using duration")
                duration_minutes = parsed["duration_minutes"]
                end_dt = start_time + timedelta(minutes=duration_minutes)
        else:
            # Use parsed duration
            duration_minutes = parsed["duration_minutes"]
            end_dt = start_time + timedelta(minutes=duration_minutes)
        
        # Add to database
        if not hasattr(task_tracker, 'db') or task_tracker.db is None:
            task_tracker.db = TaskDatabase()
        
        task_id = task_tracker.db.add_task(
            task_name=parsed["task_name"],
            description=parsed["task_description"],
            estimated_duration=duration_minutes,
            deadline=None
        )
        
        # Start monitoring
        task_tracker.start_monitoring()
        
        success_msg = f"""✅ Smart task created successfully!
        
📋 Task Details:
• ID: {task_id}
• Name: {parsed["task_name"]}
• Description: {parsed["task_description"]}
• Duration: {duration_minutes} minutes ({duration_minutes//60}h {duration_minutes%60}m)
• Start Time: {start_time.strftime('%I:%M %p')}
• End Time: {end_dt.strftime('%I:%M %p')}
• Original Input: "{user_input}"
• Live Tracking: ✅ Started
• Smart Alerts: ✅ Enabled

🤖 AI enhanced your task with professional details!
🔔 You'll get WhatsApp alerts when time is running out."""
        
        print(success_msg)
        return success_msg
        
    except Exception as e:
        error_msg = f"❌ Smart task creation failed: {str(e)}"
        print(error_msg)
        return error_msg

# Simple functions for direct use
def create_smart_task_simple(user_input, end_time=""):
    """Simple smart task creation function"""
    return create_smart_task.func(user_input, end_time)

def parse_smart_input_simple(user_input):
    """Simple parsing function"""
    return parse_smart_task_input.func(user_input)

@tool
def test_alert_system(task_name: str = "Test Task") -> str:
    """
    Test the alert system by sending a test alert
    
    Args:
        task_name: Name of the task for testing
    
    Returns:
        Success or error message
    """
    try:
        print(f"🧪 Testing alert system for task: {task_name}")
        
        # Send test alert
        success = task_tracker._send_alert(
            task_name, 
            f"🔔 TEST ALERT: This is a test notification for task '{task_name}'. Alert system is working!"
        )
        
        if success:
            result = f"✅ Test alert sent successfully for task: {task_name}"
        else:
            result = f"❌ Test alert failed for task: {task_name}"
        
        print(result)
        return result
        
    except Exception as e:
        error_msg = f"❌ Alert test failed: {str(e)}"
        print(error_msg)
        return error_msg

@tool  
def force_check_alerts() -> str:
    """
    Manually trigger alert checking for all active tasks
    
    Returns:
        Status message
    """
    try:
        print("🔍 Manually checking all tasks for alerts...")
        
        task_tracker._check_task_alerts()
        
        result = "✅ Manual alert check completed"
        print(result)
        return result
        
    except Exception as e:
        error_msg = f"❌ Manual alert check failed: {str(e)}"
        print(error_msg)
        return error_msg

# Simple functions for direct use
def test_alert_simple(task_name="Test Task"):
    """Simple alert test function"""
    return test_alert_system.func(task_name)

def force_check_alerts_simple():
    """Simple alert check function"""
    return force_check_alerts.func()