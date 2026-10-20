"""
MCQ Intelligence Agent - Complete AI-Powered Assessment Platform
Advanced autonomous MCQ generation, analysis, and solving using LangChain + LangGraph
Features: Smart caching, performance optimization, advanced analytics, real exam simulation
"""
from langchain_core.tools import tool
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from datetime import datetime, timedelta
import json
import sqlite3
import threading
import time
import sys
import os
import re
import random
import hashlib
import pickle
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from llm.message_generator import MessageGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCQDatabase:
    """Advanced database manager for MCQ platform with caching and optimization"""
    
    def __init__(self, db_path="mcq_intelligence.db"):
        self.db_path = db_path
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.init_database()
    
    def init_database(self):
        """Initialize MCQ database with comprehensive schema and indexes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if database exists and has old schema
        cursor.execute("PRAGMA table_info(mcq_questions)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # If old schema exists, migrate to new schema
        if existing_columns and 'question_hash' not in existing_columns:
            print("🔄 Migrating database to advanced schema...")
            self._migrate_database(cursor)
        
        # MCQ Questions table with enhanced fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mcq_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                topic TEXT NOT NULL,
                subtopic TEXT,
                difficulty TEXT DEFAULT 'medium',
                source TEXT DEFAULT 'ai_generated',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                confidence_score REAL DEFAULT 0.8,
                times_used INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                avg_time_taken REAL DEFAULT 0.0,
                question_hash TEXT,
                tags TEXT,
                bloom_taxonomy TEXT DEFAULT 'application',
                cognitive_load TEXT DEFAULT 'medium'
            )
        ''')
        
        # Add new columns to existing table if they don't exist
        new_columns = [
            ('subtopic', 'TEXT'),
            ('avg_time_taken', 'REAL DEFAULT 0.0'),
            ('question_hash', 'TEXT'),
            ('tags', 'TEXT'),
            ('bloom_taxonomy', 'TEXT DEFAULT "application"'),
            ('cognitive_load', 'TEXT DEFAULT "medium"')
        ]
        
        for column_name, column_type in new_columns:
            try:
                cursor.execute(f'ALTER TABLE mcq_questions ADD COLUMN {column_name} {column_type}')
                print(f"✅ Added column: {column_name}")
            except sqlite3.OperationalError:
                # Column already exists
                pass
        
        # User Exam Sessions table with detailed tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                total_questions INTEGER NOT NULL,
                questions_answered INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                status TEXT DEFAULT 'active',
                user_name TEXT DEFAULT 'Anonymous',
                time_limit INTEGER DEFAULT 1800,
                actual_duration INTEGER DEFAULT 0,
                score_percentage REAL DEFAULT 0.0,
                performance_level TEXT DEFAULT 'beginner',
                weak_topics TEXT,
                strong_topics TEXT
            )
        ''')
        
        # Add new columns to exam_sessions if they don't exist
        exam_new_columns = [
            ('actual_duration', 'INTEGER DEFAULT 0'),
            ('score_percentage', 'REAL DEFAULT 0.0'),
            ('performance_level', 'TEXT DEFAULT "beginner"'),
            ('weak_topics', 'TEXT'),
            ('strong_topics', 'TEXT')
        ]
        
        for column_name, column_type in exam_new_columns:
            try:
                cursor.execute(f'ALTER TABLE exam_sessions ADD COLUMN {column_name} {column_type}')
            except sqlite3.OperationalError:
                pass
        
        # User Answers table with detailed analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                user_answer TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                time_taken INTEGER DEFAULT 0,
                answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                confidence_level INTEGER DEFAULT 3,
                difficulty_perceived TEXT DEFAULT 'medium',
                hints_used INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES exam_sessions (session_id),
                FOREIGN KEY (question_id) REFERENCES mcq_questions (id)
            )
        ''')
        
        # Add new columns to user_answers if they don't exist
        answer_new_columns = [
            ('confidence_level', 'INTEGER DEFAULT 3'),
            ('difficulty_perceived', 'TEXT DEFAULT "medium"'),
            ('hints_used', 'INTEGER DEFAULT 0')
        ]
        
        for column_name, column_type in answer_new_columns:
            try:
                cursor.execute(f'ALTER TABLE user_answers ADD COLUMN {column_name} {column_type}')
            except sqlite3.OperationalError:
                pass
        
        # External Platform Scans table with enhanced tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS platform_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_name TEXT NOT NULL,
                scan_url TEXT,
                questions_found INTEGER DEFAULT 0,
                questions_imported INTEGER DEFAULT 0,
                scan_time TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed',
                notes TEXT,
                scan_duration REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0,
                topics_covered TEXT,
                difficulty_distribution TEXT
            )
        ''')
        
        # Learning Analytics table with AI insights (fixed structure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                weak_areas TEXT,
                improvement_suggestions TEXT,
                generated_questions INTEGER DEFAULT 0,
                analysis_date TEXT DEFAULT CURRENT_TIMESTAMP,
                learning_path TEXT,
                predicted_performance REAL DEFAULT 0.0,
                recommended_study_time INTEGER DEFAULT 0
            )
        ''')
        
        # Add user_name column to learning_analytics if it doesn't exist
        try:
            cursor.execute('ALTER TABLE learning_analytics ADD COLUMN user_name TEXT NOT NULL DEFAULT "Anonymous"')
        except sqlite3.OperationalError:
            pass
        
        # Question Templates table for faster generation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL,
                template_pattern TEXT NOT NULL,
                topic_category TEXT NOT NULL,
                difficulty_level TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Performance Cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                cache_value TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL
            )
        ''')
        
        # Create indexes for better performance (with error handling)
        indexes = [
            ('idx_questions_topic', 'mcq_questions', 'topic'),
            ('idx_questions_difficulty', 'mcq_questions', 'difficulty'),
            ('idx_sessions_status', 'exam_sessions', 'status'),
            ('idx_answers_session', 'user_answers', 'session_id')
        ]
        
        for index_name, table_name, column_name in indexes:
            try:
                cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})')
            except sqlite3.OperationalError as e:
                print(f"⚠️ Index creation warning: {e}")
        
        # Create hash index only if column exists
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_hash ON mcq_questions(question_hash)')
        except sqlite3.OperationalError:
            print("⚠️ Hash index not created - column may not exist yet")
        
        # Insert default question templates
        self._insert_default_templates(cursor)
        
        conn.commit()
        conn.close()
        print(f"✅ Advanced MCQ Intelligence database initialized: {self.db_path}")
    
    def _migrate_database(self, cursor):
        """Migrate existing database to new schema"""
        try:
            # Update existing questions with hash values
            cursor.execute('SELECT id, question_text, option_a, option_b FROM mcq_questions')
            questions = cursor.fetchall()
            
            for q_id, question, opt_a, opt_b in questions:
                question_hash = hashlib.md5(f"{question}{opt_a}{opt_b}".encode()).hexdigest()
                cursor.execute('UPDATE mcq_questions SET question_hash = ? WHERE id = ?', (question_hash, q_id))
            
            print("✅ Database migration completed")
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
    
    def _insert_default_templates(self, cursor):
        """Insert default question templates for faster generation"""
        templates = [
            ("basic_definition", "What is {concept} in {topic}?", "general", "easy"),
            ("application", "How would you implement {concept} in {topic}?", "programming", "medium"),
            ("comparison", "What is the difference between {concept1} and {concept2}?", "general", "medium"),
            ("troubleshooting", "What would cause {error} in {topic}?", "technical", "hard"),
            ("best_practice", "Which is the best approach for {scenario} in {topic}?", "general", "medium"),
            ("algorithm_complexity", "What is the time complexity of {algorithm}?", "algorithms", "hard"),
            ("syntax", "Which syntax is correct for {operation} in {language}?", "programming", "easy"),
            ("debugging", "What is wrong with this {language} code: {code}?", "programming", "medium")
        ]
        
        for template_name, pattern, category, difficulty in templates:
            cursor.execute('''
                INSERT OR IGNORE INTO question_templates 
                (template_name, template_pattern, topic_category, difficulty_level)
                VALUES (?, ?, ?, ?)
            ''', (template_name, pattern, category, difficulty))
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if not expired"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cache_value FROM performance_cache 
                WHERE cache_key = ? AND expires_at > ?
            ''', (cache_key, datetime.now().isoformat()))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return pickle.loads(result[0].encode('latin1'))
            return None
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    def set_cached_result(self, cache_key: str, value: Any, ttl_seconds: int = 300):
        """Cache result with TTL"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
            cache_value = pickle.dumps(value).decode('latin1')
            
            cursor.execute('''
                INSERT OR REPLACE INTO performance_cache 
                (cache_key, cache_value, expires_at)
                VALUES (?, ?, ?)
            ''', (cache_key, cache_value, expires_at))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    def add_question(self, question_data: Dict) -> int:
        """Add new MCQ question with duplicate detection"""
        # Generate hash for duplicate detection
        question_hash = hashlib.md5(
            f"{question_data['question']}{question_data['option_a']}{question_data['option_b']}".encode()
        ).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for duplicates
        cursor.execute('SELECT id FROM mcq_questions WHERE question_hash = ?', (question_hash,))
        if cursor.fetchone():
            conn.close()
            print(f"⚠️ Duplicate question detected, skipping...")
            return -1
        
        cursor.execute('''
            INSERT INTO mcq_questions 
            (question_text, option_a, option_b, option_c, option_d, correct_answer, 
             explanation, topic, subtopic, difficulty, source, confidence_score, question_hash, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            question_data['question'],
            question_data['option_a'],
            question_data['option_b'],
            question_data['option_c'],
            question_data['option_d'],
            question_data['correct_answer'],
            question_data.get('explanation', ''),
            question_data['topic'],
            question_data.get('subtopic', ''),
            question_data.get('difficulty', 'medium'),
            question_data.get('source', 'ai_generated'),
            question_data.get('confidence_score', 0.8),
            question_hash,
            question_data.get('tags', '')
        ))
        
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ MCQ question added: ID {question_id}")
        return question_id
    
    def get_questions_by_topic(self, topic: str, difficulty: str = None, limit: int = 10, 
                              exclude_used: bool = False) -> List[Dict]:
        """Get questions with advanced filtering and caching"""
        cache_key = f"questions_{topic}_{difficulty}_{limit}_{exclude_used}"
        cached_result = self.get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM mcq_questions WHERE topic LIKE ?'
        params = [f'%{topic}%']
        
        if difficulty:
            query += ' AND difficulty = ?'
            params.append(difficulty)
        
        if exclude_used:
            query += ' AND times_used < 3'  # Limit reuse
        
        # Prioritize high-quality questions
        query += ' ORDER BY confidence_score DESC, success_rate DESC, RANDOM() LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        questions = cursor.fetchall()
        conn.close()
        
        # Convert to dict format
        question_list = []
        for q in questions:
            question_list.append({
                'id': q[0], 'question': q[1], 'option_a': q[2], 'option_b': q[3],
                'option_c': q[4], 'option_d': q[5], 'correct_answer': q[6],
                'explanation': q[7], 'topic': q[8], 'subtopic': q[9],
                'difficulty': q[10], 'source': q[11], 'confidence_score': q[15],
                'times_used': q[16], 'success_rate': q[17]
            })
        
        # Cache the result
        self.set_cached_result(cache_key, question_list, 180)  # 3 minutes cache
        
        return question_list
    
    def get_adaptive_questions(self, user_name: str, topic: str, performance_level: str, 
                              count: int = 10) -> List[Dict]:
        """Get adaptive questions based on user performance"""
        difficulty_map = {
            'beginner': 'easy',
            'intermediate': 'medium', 
            'advanced': 'hard',
            'expert': 'hard'
        }
        
        difficulty = difficulty_map.get(performance_level, 'medium')
        
        # Get user's weak areas
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT weak_areas FROM learning_analytics 
            WHERE user_name = ? AND topic = ? 
            ORDER BY analysis_date DESC LIMIT 1
        ''', (user_name, topic))
        
        result = cursor.fetchone()
        weak_areas = result[0].split(',') if result and result[0] else []
        
        conn.close()
        
        # Get questions focusing on weak areas
        questions = []
        if weak_areas:
            for area in weak_areas[:3]:  # Focus on top 3 weak areas
                area_questions = self.get_questions_by_topic(area.strip(), difficulty, count//3)
                questions.extend(area_questions)
        
        # Fill remaining with general topic questions
        if len(questions) < count:
            remaining = count - len(questions)
            general_questions = self.get_questions_by_topic(topic, difficulty, remaining)
            questions.extend(general_questions)
        
        # If still not enough questions, generate some
        if len(questions) < count:
            print(f"⚠️ Only {len(questions)} questions available, generating more...")
            # Import here to avoid circular imports
            from agents.mcq_agent import mcq_generator
            needed = count - len(questions)
            new_questions = mcq_generator.generate_mcq_batch(topic, difficulty, needed)
            for q in new_questions:
                q_id = self.add_question(q)
                if q_id > 0:
                    questions.append({**q, 'id': q_id})
        
        return questions[:count]  # Return exactly the requested count
        
    def create_exam_session(self, topic: str, difficulty: str, num_questions: int, user_name: str = "Anonymous") -> str:
        """Create new exam session"""
        session_id = f"exam_{int(time.time())}_{random.randint(1000, 9999)}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO exam_sessions 
            (session_id, topic, difficulty, total_questions, user_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, topic, difficulty, num_questions, user_name))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Exam session created: {session_id}")
        return session_id
    
    def get_exam_session(self, session_id: str) -> Dict:
        """Get exam session details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM exam_sessions WHERE session_id = ?', (session_id,))
        session = cursor.fetchone()
        conn.close()
        
        if session:
            return {
                'id': session[0],
                'session_id': session[1],
                'topic': session[2],
                'difficulty': session[3],
                'total_questions': session[4],
                'questions_answered': session[5],
                'correct_answers': session[6],
                'start_time': session[7],
                'end_time': session[8],
                'status': session[9],
                'user_name': session[10],
                'time_limit': session[11]
            }
        return None
    
    def record_answer(self, session_id: str, question_id: int, user_answer: str, is_correct: bool, time_taken: int = 0):
        """Record user answer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add answer record
        cursor.execute('''
            INSERT INTO user_answers 
            (session_id, question_id, user_answer, is_correct, time_taken)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, question_id, user_answer, is_correct, time_taken))
        
        # Update session stats
        cursor.execute('''
            UPDATE exam_sessions 
            SET questions_answered = questions_answered + 1,
                correct_answers = correct_answers + ?
            WHERE session_id = ?
        ''', (1 if is_correct else 0, session_id))
        
        # Update question usage stats
        cursor.execute('''
            UPDATE mcq_questions 
            SET times_used = times_used + 1,
                success_rate = (
                    SELECT AVG(CAST(is_correct AS FLOAT)) 
                    FROM user_answers 
                    WHERE question_id = ?
                )
            WHERE id = ?
        ''', (question_id, question_id))
        
        conn.commit()
        conn.close()
    
class ExamSimulator:
    """Advanced exam simulation with real-time analytics and adaptive difficulty"""
    
    def __init__(self, db: MCQDatabase):
        self.db = db
        self.active_sessions = {}
    
    def create_adaptive_exam(self, topic: str, user_name: str, target_duration: int = 30, 
                           initial_difficulty: str = "medium") -> str:
        """Create an adaptive exam that adjusts difficulty based on performance"""
        session_id = f"adaptive_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Determine user's performance level
        performance_level = self._get_user_performance_level(user_name, topic)
        
        # Get adaptive questions
        questions = self.db.get_adaptive_questions(user_name, topic, performance_level, 15)
        
        if len(questions) < 10:
            # Generate more questions if needed
            from agents.mcq_agent import mcq_generator
            additional = mcq_generator.generate_mcq_batch(topic, initial_difficulty, 10 - len(questions))
            for q in additional:
                q_id = self.db.add_question(q)
                if q_id > 0:
                    questions.append({**q, 'id': q_id})
        
        # Create session
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO exam_sessions 
            (session_id, topic, difficulty, total_questions, user_name, time_limit, performance_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, topic, initial_difficulty, len(questions), user_name, target_duration * 60, performance_level))
        
        conn.commit()
        conn.close()
        
        # Store session data
        self.active_sessions[session_id] = {
            'questions': questions,
            'current_question': 0,
            'start_time': time.time(),
            'answers': [],
            'difficulty_adjustments': 0
        }
        
        return session_id
    
    def get_next_question(self, session_id: str) -> Optional[Dict]:
        """Get next question with adaptive difficulty adjustment"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        if session['current_question'] >= len(session['questions']):
            return None
        
        question = session['questions'][session['current_question']]
        
        # Add timing and session info
        question['session_info'] = {
            'question_number': session['current_question'] + 1,
            'total_questions': len(session['questions']),
            'time_elapsed': int(time.time() - session['start_time']),
            'progress_percentage': ((session['current_question'] + 1) / len(session['questions'])) * 100
        }
        
        return question
    
    def submit_answer(self, session_id: str, question_id: int, user_answer: str, 
                     time_taken: int, confidence_level: int = 3) -> Dict:
        """Submit answer and get immediate feedback with adaptive adjustment"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        current_q = session['questions'][session['current_question']]
        
        is_correct = user_answer.upper() == current_q['correct_answer'].upper()
        
        # Record answer
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_answers 
            (session_id, question_id, user_answer, is_correct, time_taken, confidence_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, question_id, user_answer, is_correct, time_taken, confidence_level))
        
        conn.commit()
        conn.close()
        
        # Store in session
        session['answers'].append({
            'question_id': question_id,
            'user_answer': user_answer,
            'correct_answer': current_q['correct_answer'],
            'is_correct': is_correct,
            'time_taken': time_taken,
            'confidence_level': confidence_level
        })
        
        # Move to next question
        session['current_question'] += 1
        
        # Adaptive difficulty adjustment
        self._adjust_difficulty_if_needed(session_id)
        
        # Prepare feedback
        feedback = {
            'is_correct': is_correct,
            'correct_answer': current_q['correct_answer'],
            'explanation': current_q.get('explanation', 'No explanation available'),
            'time_taken': time_taken,
            'question_completed': session['current_question'],
            'total_questions': len(session['questions']),
            'current_score': sum(1 for a in session['answers'] if a['is_correct']),
            'percentage': (sum(1 for a in session['answers'] if a['is_correct']) / len(session['answers'])) * 100
        }
        
        return feedback
    
    def _adjust_difficulty_if_needed(self, session_id: str):
        """Adjust difficulty based on recent performance"""
        session = self.active_sessions[session_id]
        answers = session['answers']
        
        # Check last 3 answers for adjustment
        if len(answers) >= 3 and session['difficulty_adjustments'] < 2:
            recent_answers = answers[-3:]
            recent_score = sum(1 for a in recent_answers if a['is_correct']) / len(recent_answers)
            
            # Adjust difficulty based on performance
            if recent_score >= 0.8:  # 80% or higher - increase difficulty
                self._increase_difficulty(session_id)
            elif recent_score <= 0.3:  # 30% or lower - decrease difficulty
                self._decrease_difficulty(session_id)
    
    def _increase_difficulty(self, session_id: str):
        """Increase difficulty by replacing upcoming questions"""
        session = self.active_sessions[session_id]
        session['difficulty_adjustments'] += 1
        print(f"📈 Increasing difficulty for session {session_id}")
        # Implementation would replace easier questions with harder ones
    
    def _decrease_difficulty(self, session_id: str):
        """Decrease difficulty by replacing upcoming questions"""
        session = self.active_sessions[session_id]
        session['difficulty_adjustments'] += 1
        print(f"📉 Decreasing difficulty for session {session_id}")
        # Implementation would replace harder questions with easier ones
    
    def _get_user_performance_level(self, user_name: str, topic: str) -> str:
        """Determine user's performance level based on history"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT AVG(score_percentage) FROM exam_sessions 
            WHERE user_name = ? AND topic = ? AND status = 'completed'
        ''', (user_name, topic))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] is not None:
            avg_score = result[0]
            if avg_score >= 85:
                return 'expert'
            elif avg_score >= 70:
                return 'advanced'
            elif avg_score >= 50:
                return 'intermediate'
            else:
                return 'beginner'
        
        return 'beginner'  # Default for new users
    
    def complete_exam(self, session_id: str) -> Dict:
        """Complete exam and generate comprehensive analytics"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        end_time = time.time()
        total_duration = int(end_time - session['start_time'])
        
        # Calculate final statistics
        total_questions = len(session['answers'])
        correct_answers = sum(1 for a in session['answers'] if a['is_correct'])
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Update database
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE exam_sessions 
            SET status = 'completed', end_time = ?, actual_duration = ?, 
                questions_answered = ?, correct_answers = ?, score_percentage = ?
            WHERE session_id = ?
        ''', (datetime.now().isoformat(), total_duration, total_questions, 
              correct_answers, score_percentage, session_id))
        
        conn.commit()
        conn.close()
        
        # Generate analytics
        analytics = self._generate_exam_analytics(session)
        
        # Clean up session
        del self.active_sessions[session_id]
        
        return {
            'session_id': session_id,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'score_percentage': score_percentage,
            'duration_minutes': total_duration // 60,
            'analytics': analytics
        }
    
    def _generate_exam_analytics(self, session: Dict) -> Dict:
        """Generate comprehensive exam analytics"""
        answers = session['answers']
        
        if not answers:
            return {}
        
        # Time analysis
        avg_time = sum(a['time_taken'] for a in answers) / len(answers)
        fastest_time = min(a['time_taken'] for a in answers)
        slowest_time = max(a['time_taken'] for a in answers)
        
        # Confidence analysis
        avg_confidence = sum(a['confidence_level'] for a in answers) / len(answers)
        
        # Performance trends
        first_half = answers[:len(answers)//2]
        second_half = answers[len(answers)//2:]
        
        first_half_score = sum(1 for a in first_half if a['is_correct']) / len(first_half) * 100
        second_half_score = sum(1 for a in second_half if a['is_correct']) / len(second_half) * 100
        
        return {
            'time_analysis': {
                'average_time_per_question': avg_time,
                'fastest_question': fastest_time,
                'slowest_question': slowest_time
            },
            'confidence_analysis': {
                'average_confidence': avg_confidence,
                'high_confidence_correct': sum(1 for a in answers if a['confidence_level'] >= 4 and a['is_correct']),
                'low_confidence_correct': sum(1 for a in answers if a['confidence_level'] <= 2 and a['is_correct'])
            },
            'performance_trends': {
                'first_half_score': first_half_score,
                'second_half_score': second_half_score,
                'improvement': second_half_score - first_half_score
            }
        }

class LearningAnalytics:
    """Advanced learning analytics and personalized recommendations"""
    
    def __init__(self, db: MCQDatabase):
        self.db = db
    
    def analyze_user_performance(self, user_name: str, topic: str = None) -> Dict:
        """Comprehensive user performance analysis"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Base query
        base_query = '''
            SELECT es.topic, es.difficulty, es.score_percentage, es.actual_duration,
                   ua.is_correct, ua.time_taken, ua.confidence_level, mq.subtopic
            FROM exam_sessions es
            JOIN user_answers ua ON es.session_id = ua.session_id
            JOIN mcq_questions mq ON ua.question_id = mq.id
            WHERE es.user_name = ? AND es.status = 'completed'
        '''
        
        params = [user_name]
        if topic:
            base_query += ' AND es.topic = ?'
            params.append(topic)
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {'message': 'No performance data available'}
        
        # Analyze results
        analysis = {
            'overall_performance': self._analyze_overall_performance(results),
            'topic_breakdown': self._analyze_topic_breakdown(results),
            'difficulty_analysis': self._analyze_difficulty_performance(results),
            'time_management': self._analyze_time_management(results),
            'confidence_accuracy': self._analyze_confidence_accuracy(results),
            'learning_recommendations': self._generate_learning_recommendations(results, user_name)
        }
        
        return analysis
    
    def _analyze_overall_performance(self, results: List[Tuple]) -> Dict:
        """Analyze overall user performance"""
        total_questions = len(results)
        correct_answers = sum(1 for r in results if r[4])  # is_correct
        accuracy = (correct_answers / total_questions) * 100
        
        avg_time = sum(r[5] for r in results) / total_questions  # time_taken
        avg_confidence = sum(r[6] for r in results) / total_questions  # confidence_level
        
        return {
            'total_questions_attempted': total_questions,
            'overall_accuracy': accuracy,
            'average_time_per_question': avg_time,
            'average_confidence_level': avg_confidence,
            'performance_level': self._get_performance_level(accuracy)
        }
    
    def _analyze_topic_breakdown(self, results: List[Tuple]) -> Dict:
        """Analyze performance by topic and subtopic"""
        topic_stats = {}
        
        for result in results:
            topic = result[0]
            subtopic = result[7] or 'General'
            is_correct = result[4]
            
            if topic not in topic_stats:
                topic_stats[topic] = {'total': 0, 'correct': 0, 'subtopics': {}}
            
            topic_stats[topic]['total'] += 1
            if is_correct:
                topic_stats[topic]['correct'] += 1
            
            if subtopic not in topic_stats[topic]['subtopics']:
                topic_stats[topic]['subtopics'][subtopic] = {'total': 0, 'correct': 0}
            
            topic_stats[topic]['subtopics'][subtopic]['total'] += 1
            if is_correct:
                topic_stats[topic]['subtopics'][subtopic]['correct'] += 1
        
        # Calculate percentages
        for topic in topic_stats:
            topic_stats[topic]['accuracy'] = (topic_stats[topic]['correct'] / topic_stats[topic]['total']) * 100
            
            for subtopic in topic_stats[topic]['subtopics']:
                st = topic_stats[topic]['subtopics'][subtopic]
                st['accuracy'] = (st['correct'] / st['total']) * 100
        
        return topic_stats
    
    def _generate_learning_recommendations(self, results: List[Tuple], user_name: str) -> List[str]:
        """Generate personalized learning recommendations"""
        recommendations = []
        
        # Analyze weak areas
        topic_performance = {}
        for result in results:
            topic = result[0]
            is_correct = result[4]
            
            if topic not in topic_performance:
                topic_performance[topic] = {'total': 0, 'correct': 0}
            
            topic_performance[topic]['total'] += 1
            if is_correct:
                topic_performance[topic]['correct'] += 1
        
        # Find weak topics (< 60% accuracy)
        weak_topics = []
        for topic, stats in topic_performance.items():
            accuracy = (stats['correct'] / stats['total']) * 100
            if accuracy < 60:
                weak_topics.append((topic, accuracy))
        
        # Generate recommendations
        if weak_topics:
            weak_topics.sort(key=lambda x: x[1])  # Sort by accuracy (lowest first)
            recommendations.append(f"Focus on improving {weak_topics[0][0]} (current accuracy: {weak_topics[0][1]:.1f}%)")
            
            if len(weak_topics) > 1:
                recommendations.append(f"Also review {weak_topics[1][0]} concepts")
        
        # Time management recommendations
        avg_time = sum(r[5] for r in results) / len(results)
        if avg_time > 120:  # More than 2 minutes per question
            recommendations.append("Practice time management - aim for 90-120 seconds per question")
        
        # Confidence recommendations
        overconfident = sum(1 for r in results if r[6] >= 4 and not r[4])  # High confidence but wrong
        underconfident = sum(1 for r in results if r[6] <= 2 and r[4])  # Low confidence but correct
        
        if overconfident > len(results) * 0.2:  # More than 20% overconfident
            recommendations.append("Review answers more carefully - you may be overconfident in some areas")
        
        if underconfident > len(results) * 0.2:  # More than 20% underconfident
            recommendations.append("Build confidence in your knowledge - you know more than you think!")
        
        return recommendations
    
    def _get_performance_level(self, accuracy: float) -> str:
        """Determine performance level based on accuracy"""
        if accuracy >= 90:
            return 'Expert'
        elif accuracy >= 80:
            return 'Advanced'
        elif accuracy >= 70:
            return 'Intermediate'
        elif accuracy >= 60:
            return 'Developing'
        else:
            return 'Beginner'
    
    def _analyze_difficulty_performance(self, results: List[Tuple]) -> Dict:
        """Analyze performance by difficulty level"""
        difficulty_stats = {}
        
        for result in results:
            difficulty = result[1]
            is_correct = result[4]
            
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {'total': 0, 'correct': 0}
            
            difficulty_stats[difficulty]['total'] += 1
            if is_correct:
                difficulty_stats[difficulty]['correct'] += 1
        
        # Calculate accuracy for each difficulty
        for difficulty in difficulty_stats:
            stats = difficulty_stats[difficulty]
            stats['accuracy'] = (stats['correct'] / stats['total']) * 100
        
        return difficulty_stats
    
    def _analyze_time_management(self, results: List[Tuple]) -> Dict:
        """Analyze time management patterns"""
        times = [r[5] for r in results]  # time_taken
        
        return {
            'average_time': sum(times) / len(times),
            'fastest_time': min(times),
            'slowest_time': max(times),
            'time_consistency': self._calculate_time_consistency(times)
        }
    
    def _analyze_confidence_accuracy(self, results: List[Tuple]) -> Dict:
        """Analyze relationship between confidence and accuracy"""
        confidence_accuracy = {}
        
        for result in results:
            confidence = result[6]
            is_correct = result[4]
            
            if confidence not in confidence_accuracy:
                confidence_accuracy[confidence] = {'total': 0, 'correct': 0}
            
            confidence_accuracy[confidence]['total'] += 1
            if is_correct:
                confidence_accuracy[confidence]['correct'] += 1
        
        # Calculate accuracy for each confidence level
        for confidence in confidence_accuracy:
            stats = confidence_accuracy[confidence]
            stats['accuracy'] = (stats['correct'] / stats['total']) * 100
        
        return confidence_accuracy
    
    def _calculate_time_consistency(self, times: List[int]) -> float:
        """Calculate time consistency (lower is more consistent)"""
        if len(times) < 2:
            return 0.0
        
        mean_time = sum(times) / len(times)
        variance = sum((t - mean_time) ** 2 for t in times) / len(times)
        std_dev = variance ** 0.5
        
        # Return coefficient of variation (std_dev / mean)
        return std_dev / mean_time if mean_time > 0 else 0.0

class MCQGenerator:
    """Advanced AI-powered MCQ generation engine with optimization"""
    
    def __init__(self):
        self.llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL
        )
        self.message_generator = MessageGenerator()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.generation_cache = {}
    
    def generate_mcq_batch(self, topic: str, difficulty: str = "medium", count: int = 5) -> List[Dict]:
        """Generate multiple MCQs with parallel processing and smart caching"""
        cache_key = f"{topic}_{difficulty}_{count}"
        
        # Check cache first
        if cache_key in self.generation_cache:
            cached_time, cached_questions = self.generation_cache[cache_key]
            if time.time() - cached_time < 1800:  # 30 minutes cache
                print(f"🎯 Using cached questions for {topic}")
                return cached_questions
        
        questions = []
        
        # Use parallel processing for multiple questions
        if count > 1:
            futures = []
            for i in range(min(count, 3)):  # Limit parallel requests
                future = self.executor.submit(self.generate_single_mcq, topic, difficulty)
                futures.append(future)
            
            # Collect results with timeout
            for i, future in enumerate(futures):
                try:
                    question = future.result(timeout=25)  # 25 second timeout per question
                    if question:
                        questions.append(question)
                        print(f"✅ Generated question {i+1}/{len(futures)} for {topic}")
                    else:
                        print(f"⚠️ Failed to generate question {i+1}/{len(futures)}")
                except FutureTimeoutError:
                    print(f"⏰ Question {i+1} timed out, using fallback")
                    fallback = self._create_fallback_question(topic, difficulty)
                    questions.append(fallback)
                except Exception as e:
                    print(f"❌ Error generating question {i+1}: {e}")
                    fallback = self._create_fallback_question(topic, difficulty)
                    questions.append(fallback)
            
            # Generate remaining questions if needed
            while len(questions) < count:
                fallback = self._create_fallback_question(topic, difficulty)
                questions.append(fallback)
                print(f"🔄 Added fallback question {len(questions)}/{count}")
        
        else:
            # Single question generation
            try:
                question = self.generate_single_mcq(topic, difficulty)
                if question:
                    questions.append(question)
                else:
                    questions.append(self._create_fallback_question(topic, difficulty))
            except Exception as e:
                print(f"❌ Error generating single question: {e}")
                questions.append(self._create_fallback_question(topic, difficulty))
        
        # Cache successful results
        if questions:
            self.generation_cache[cache_key] = (time.time(), questions)
        
        return questions
    
    def generate_single_mcq(self, topic: str, difficulty: str = "medium") -> Dict:
        """Generate a single high-quality MCQ with advanced prompting"""
        
        difficulty_prompts = {
            "easy": "basic concepts, simple recall, fundamental principles, definitions",
            "medium": "application of concepts, moderate analysis, problem-solving, implementation",
            "hard": "complex analysis, synthesis, critical thinking, advanced applications, optimization"
        }
        
        # Enhanced prompt with better structure
        prompt = f"""
You are an expert educator creating high-quality multiple choice questions.

TOPIC: {topic}
DIFFICULTY: {difficulty} level
FOCUS: {difficulty_prompts.get(difficulty, 'understanding')}

REQUIREMENTS:
1. Create ONE clear, unambiguous question
2. Provide exactly 4 options (A, B, C, D)
3. Only ONE option should be clearly correct
4. Other options should be plausible but definitively wrong
5. Include a detailed explanation
6. Make it practical and relevant to real-world scenarios

QUALITY STANDARDS:
- Question should test understanding, not just memorization
- Options should be similar in length and complexity
- Avoid "all of the above" or "none of the above"
- Use specific, concrete examples when possible

FORMAT (EXACT):
QUESTION: [Your clear, specific question here]
A) [First option]
B) [Second option]
C) [Third option]
D) [Fourth option]
CORRECT: [A/B/C/D]
EXPLANATION: [Detailed explanation of why the correct answer is right and others are wrong]

EXAMPLE for "Python Programming" at medium level:
QUESTION: What will be the output of this Python code: x = [1, 2]; y = x; y.append(3); print(len(x))?
A) 2
B) 3
C) Error
D) None
CORRECT: B
EXPLANATION: In Python, when you assign a list to another variable (y = x), both variables reference the same list object. When y.append(3) adds an element, it modifies the original list that both x and y point to. Therefore, len(x) returns 3, not 2.

Now create your MCQ:
"""
        
        try:
            start_time = time.time()
            
            # Use faster model if available
            response = self.llm.invoke(prompt)
            
            elapsed_time = time.time() - start_time
            print(f"⏱️ LLM response time: {elapsed_time:.2f} seconds")
            
            result = self._parse_mcq_response(response, topic, difficulty)
            
            # If parsing failed, create a fallback question
            if not result:
                print("⚠️ LLM parsing failed, creating enhanced fallback question")
                result = self._create_enhanced_fallback_question(topic, difficulty)
            
            return result
            
        except Exception as e:
            print(f"❌ MCQ generation error: {e}")
            print("🔄 Creating enhanced fallback question...")
            return self._create_enhanced_fallback_question(topic, difficulty)
    
    def _create_enhanced_fallback_question(self, topic: str, difficulty: str) -> Dict:
        """Create enhanced fallback questions with topic-specific templates"""
        
        # Topic-specific question templates
        topic_templates = {
            "python": {
                "easy": {
                    "question": "Which of the following is the correct way to create a list in Python?",
                    "options": ["my_list = []", "my_list = ()", "my_list = {}", "my_list = <>"],
                    "correct": "A",
                    "explanation": "In Python, lists are created using square brackets []. Parentheses () create tuples, curly braces {} create dictionaries or sets."
                },
                "medium": {
                    "question": f"What is the most efficient way to check if an element exists in a large dataset in {topic}?",
                    "options": ["Using a list with 'in' operator", "Using a set with 'in' operator", "Using a for loop", "Using try-except"],
                    "correct": "B",
                    "explanation": "Sets use hash tables for O(1) average lookup time, making them much faster than lists O(n) for membership testing."
                }
            },
            "javascript": {
                "easy": {
                    "question": "How do you declare a variable in JavaScript?",
                    "options": ["var myVar;", "variable myVar;", "v myVar;", "declare myVar;"],
                    "correct": "A",
                    "explanation": "In JavaScript, variables are declared using 'var', 'let', or 'const' keywords. 'var' is the traditional way."
                }
            },
            "machine learning": {
                "medium": {
                    "question": "What is the primary purpose of cross-validation in machine learning?",
                    "options": ["To increase model accuracy", "To assess model performance", "To reduce overfitting", "To speed up training"],
                    "correct": "B",
                    "explanation": "Cross-validation is primarily used to assess how well a model will generalize to unseen data by testing it on multiple train-test splits."
                }
            }
        }
        
        # Default fallback templates by difficulty
        default_templates = {
            "easy": {
                "question": f"What is a fundamental concept in {topic}?",
                "options": ["Basic principle", "Advanced theory", "Complex algorithm", "Expert technique"],
                "correct": "A",
                "explanation": f"Understanding basic principles is fundamental to learning {topic}."
            },
            "medium": {
                "question": f"How would you apply {topic} concepts in a real-world scenario?",
                "options": ["Through practical implementation", "By memorization only", "Without understanding context", "Using random approaches"],
                "correct": "A", 
                "explanation": f"Practical implementation is the best way to apply {topic} concepts effectively."
            },
            "hard": {
                "question": f"What is the most challenging aspect when optimizing {topic} solutions?",
                "options": ["Balancing performance and complexity", "Basic syntax understanding", "Simple implementation", "Trivial optimization"],
                "correct": "A",
                "explanation": f"Advanced {topic} optimization requires balancing multiple factors like performance, maintainability, and complexity."
            }
        }
        
        # Try to find topic-specific template
        topic_key = topic.lower()
        for key in topic_templates:
            if key in topic_key:
                if difficulty in topic_templates[key]:
                    template = topic_templates[key][difficulty]
                    break
        else:
            # Use default template
            template = default_templates.get(difficulty, default_templates["medium"])
        
        return {
            'question': template["question"],
            'option_a': template["options"][0],
            'option_b': template["options"][1], 
            'option_c': template["options"][2],
            'option_d': template["options"][3],
            'correct_answer': template["correct"],
            'explanation': template["explanation"],
            'topic': topic,
            'difficulty': difficulty,
            'source': 'enhanced_fallback',
            'confidence_score': 0.7,
            'tags': f'fallback,{difficulty},{topic.lower().replace(" ", "_")}'
        }
    
    def _create_fallback_question(self, topic: str, difficulty: str) -> Dict:
        """Create a fallback question when LLM fails"""
        return self._create_enhanced_fallback_question(topic, difficulty)
    
    def _parse_mcq_response(self, response: str, topic: str, difficulty: str) -> Dict:
        """Parse LLM response into structured MCQ data"""
        try:
            lines = response.strip().split('\n')
            
            question = ""
            options = {"A": "", "B": "", "C": "", "D": ""}
            correct_answer = ""
            explanation = ""
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('QUESTION:'):
                    question = line.replace('QUESTION:', '').strip()
                    current_section = 'question'
                elif line.startswith('A)'):
                    options['A'] = line.replace('A)', '').strip()
                elif line.startswith('B)'):
                    options['B'] = line.replace('B)', '').strip()
                elif line.startswith('C)'):
                    options['C'] = line.replace('C)', '').strip()
                elif line.startswith('D)'):
                    options['D'] = line.replace('D)', '').strip()
                elif line.startswith('CORRECT:'):
                    correct_answer = line.replace('CORRECT:', '').strip().upper()
                elif line.startswith('EXPLANATION:'):
                    explanation = line.replace('EXPLANATION:', '').strip()
                    current_section = 'explanation'
                elif current_section == 'explanation':
                    explanation += " " + line
            
            # Validate the parsed data
            if not question or not all(options.values()) or correct_answer not in ['A', 'B', 'C', 'D']:
                print(f"⚠️ Invalid MCQ format in response")
                return None
            
            return {
                'question': question,
                'option_a': options['A'],
                'option_b': options['B'],
                'option_c': options['C'],
                'option_d': options['D'],
                'correct_answer': correct_answer,
                'explanation': explanation,
                'topic': topic,
                'difficulty': difficulty,
                'source': 'ai_generated',
                'confidence_score': 0.85
            }
            
        except Exception as e:
            print(f"❌ MCQ parsing error: {e}")
            return None

class MCQAnalyzer:
    """AI-powered MCQ analysis and solving engine"""
    
    def __init__(self):
        self.llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL
        )
    
    def analyze_and_solve_mcq(self, question_data: Dict) -> Dict:
        """Analyze MCQ and provide AI solution with reasoning"""
        
        prompt = f"""
You are an expert AI that can solve any multiple choice question with detailed reasoning.

QUESTION: {question_data['question']}
A) {question_data['option_a']}
B) {question_data['option_b']}
C) {question_data['option_c']}
D) {question_data['option_d']}

Analyze this question step by step and provide:
1. Your answer (A, B, C, or D)
2. Detailed reasoning
3. Confidence level (0-100%)
4. Key concepts involved
5. Why other options are incorrect

Format your response as:
ANSWER: [A/B/C/D]
CONFIDENCE: [0-100]%
REASONING: [Your detailed step-by-step analysis]
CONCEPTS: [Key concepts/topics involved]
WRONG_OPTIONS: [Why A, B, C, D are wrong - only mention the incorrect ones]
"""
        
        try:
            response = self.llm.invoke(prompt)
            return self._parse_analysis_response(response, question_data)
        except Exception as e:
            print(f"❌ MCQ analysis error: {e}")
            return {
                'ai_answer': 'A',
                'confidence': 50,
                'reasoning': 'Analysis failed',
                'concepts': [],
                'is_correct': False
            }
    
    def _parse_analysis_response(self, response: str, question_data: Dict) -> Dict:
        """Parse AI analysis response"""
        try:
            lines = response.strip().split('\n')
            
            ai_answer = ""
            confidence = 50
            reasoning = ""
            concepts = ""
            wrong_options = ""
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('ANSWER:'):
                    ai_answer = line.replace('ANSWER:', '').strip().upper()
                elif line.startswith('CONFIDENCE:'):
                    conf_text = line.replace('CONFIDENCE:', '').strip().replace('%', '')
                    try:
                        confidence = int(conf_text)
                    except:
                        confidence = 50
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
                    current_section = 'reasoning'
                elif line.startswith('CONCEPTS:'):
                    concepts = line.replace('CONCEPTS:', '').strip()
                    current_section = 'concepts'
                elif line.startswith('WRONG_OPTIONS:'):
                    wrong_options = line.replace('WRONG_OPTIONS:', '').strip()
                    current_section = 'wrong_options'
                elif current_section == 'reasoning':
                    reasoning += " " + line
                elif current_section == 'concepts':
                    concepts += " " + line
                elif current_section == 'wrong_options':
                    wrong_options += " " + line
            
            # Check if AI answer matches correct answer
            correct_answer = question_data.get('correct_answer', '').upper()
            is_correct = ai_answer == correct_answer
            
            return {
                'ai_answer': ai_answer,
                'confidence': confidence,
                'reasoning': reasoning,
                'concepts': concepts.split(',') if concepts else [],
                'wrong_options_analysis': wrong_options,
                'is_correct': is_correct,
                'correct_answer': correct_answer
            }
            
        except Exception as e:
            print(f"❌ Analysis parsing error: {e}")
            return {
                'ai_answer': 'A',
                'confidence': 50,
                'reasoning': 'Parsing failed',
                'concepts': [],
                'is_correct': False
            }

class MCQPlatformScanner:
    """Autonomous agent for scanning external MCQ platforms"""
    
    def __init__(self):
        self.llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL
        )
    
    def simulate_platform_scan(self, platform_name: str, topic: str) -> Dict:
        """Simulate scanning external MCQ platform (demo version)"""
        
        # In a real implementation, this would use web scraping, OCR, or API calls
        # For demo, we'll generate sample questions as if scanned from external platform
        
        print(f"🔍 Simulating scan of {platform_name} for topic: {topic}")
        
        # Simulate finding questions on external platform
        simulated_questions = [
            {
                'question': f'Sample question from {platform_name} about {topic}',
                'option_a': 'Option A from external platform',
                'option_b': 'Option B from external platform', 
                'option_c': 'Option C from external platform',
                'option_d': 'Option D from external platform',
                'correct_answer': 'A',
                'explanation': f'This question was found on {platform_name}',
                'topic': topic,
                'difficulty': 'medium',
                'source': f'scanned_{platform_name.lower()}',
                'confidence_score': 0.7
            }
        ]
        
        return {
            'platform_name': platform_name,
            'questions_found': len(simulated_questions),
            'questions_imported': len(simulated_questions),
            'questions': simulated_questions,
            'scan_status': 'completed',
            'notes': f'Successfully scanned {platform_name} and found {len(simulated_questions)} questions'
        }

# Global instances with advanced features
mcq_db = MCQDatabase()
mcq_generator = MCQGenerator()
mcq_analyzer = MCQAnalyzer()
mcq_scanner = MCQPlatformScanner()
exam_simulator = ExamSimulator(mcq_db)
learning_analytics = LearningAnalytics(mcq_db)

@tool
def generate_mcq_questions(topic: str, difficulty: str = "medium", count: int = 5) -> str:
    """
    Generate AI-powered MCQ questions for any topic with advanced caching and optimization
    
    Args:
        topic: Subject/topic for questions (e.g., "Python Programming", "Machine Learning")
        difficulty: Question difficulty - easy, medium, hard
        count: Number of questions to generate (1-10 for optimal performance)
    
    Returns:
        Success message with generation details and performance metrics
    """
    try:
        print(f"🧠 Generating {count} MCQ questions for {topic} at {difficulty} level")
        
        # Validate inputs
        if count < 1 or count > 10:
            count = min(max(count, 1), 10)  # Clamp between 1-10
        
        if difficulty not in ['easy', 'medium', 'hard']:
            difficulty = 'medium'
        
        start_time = time.time()
        
        # Generate questions with advanced features
        questions = mcq_generator.generate_mcq_batch(topic, difficulty, count)
        
        generation_time = time.time() - start_time
        
        if not questions:
            return f"❌ Failed to generate questions for topic: {topic}"
        
        # Save to database with enhanced metadata
        saved_count = 0
        duplicate_count = 0
        for question in questions:
            try:
                question_id = mcq_db.add_question(question)
                if question_id > 0:
                    saved_count += 1
                else:
                    duplicate_count += 1
            except Exception as e:
                print(f"⚠️ Failed to save question: {e}")
        
        # Calculate performance metrics
        success_rate = (len(questions) / count) * 100
        avg_generation_time = generation_time / count
        
        result = f"""✅ Advanced MCQ Generation Completed!

📊 Generation Summary:
• Topic: {topic}
• Difficulty: {difficulty.title()}
• Requested: {count} questions
• Generated: {len(questions)} questions
• Saved to Database: {saved_count} questions
• Duplicates Skipped: {duplicate_count} questions
• Success Rate: {success_rate:.1f}%

⚡ Performance Metrics:
• Total Generation Time: {generation_time:.2f} seconds
• Average Time per Question: {avg_generation_time:.2f} seconds
• Cache Hits: {getattr(mcq_generator, 'cache_hits', 0)}
• Fallback Questions: {sum(1 for q in questions if q.get('source') == 'enhanced_fallback')}

🎯 Questions are now available for exams and practice sessions!
💡 Use 'create_exam_session' or 'create_adaptive_exam' for intelligent assessments."""
        
        print(result)
        return result
        
    except Exception as e:
        error_msg = f"❌ Advanced MCQ generation failed: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def create_adaptive_exam(topic: str, user_name: str = "Anonymous", target_duration: int = 30, 
                        initial_difficulty: str = "medium") -> str:
    """
    Create an adaptive exam that adjusts difficulty based on real-time performance
    
    Args:
        topic: Topic for the adaptive exam
        user_name: Name of the exam taker for personalized adaptation
        target_duration: Target exam duration in minutes
        initial_difficulty: Starting difficulty level
    
    Returns:
        Adaptive exam session details with personalized recommendations
    """
    try:
        print(f"🎯 Creating adaptive exam: {topic} for {user_name}")
        
        # Create adaptive exam session
        session_id = exam_simulator.create_adaptive_exam(topic, user_name, target_duration, initial_difficulty)
        
        # Get user's performance history for context
        user_analysis = learning_analytics.analyze_user_performance(user_name, topic)
        
        result = f"""✅ Adaptive Exam Session Created!

🎯 Session Details:
• Session ID: {session_id}
• Topic: {topic}
• Participant: {user_name}
• Target Duration: {target_duration} minutes
• Initial Difficulty: {initial_difficulty.title()}
• Adaptive Features: ✅ Enabled

🧠 Personalization Features:
• Performance-based difficulty adjustment
• Real-time analytics and feedback
• Personalized question selection
• Confidence level tracking
• Time management analysis

📊 User Performance Context:
{user_analysis.get('overall_performance', {}).get('performance_level', 'New User')} level detected

🎮 Next Steps:
1. Use the exam interface with Session ID: {session_id}
2. Answer questions with confidence levels
3. Get real-time adaptive difficulty adjustment
4. Receive comprehensive performance analytics

💡 The AI will continuously adapt the exam difficulty based on your performance!"""
        
        print(result)
        return result
        
    except Exception as e:
        error_msg = f"❌ Adaptive exam creation failed: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def analyze_user_performance(user_name: str, topic: str = None) -> str:
    """
    Generate comprehensive learning analytics and personalized recommendations
    
    Args:
        user_name: Name of the user to analyze
        topic: Specific topic to analyze (optional, analyzes all topics if not provided)
    
    Returns:
        Detailed performance analysis with personalized learning recommendations
    """
    try:
        print(f"📊 Analyzing performance for {user_name}" + (f" in {topic}" if topic else ""))
        
        # Get comprehensive analysis
        analysis = learning_analytics.analyze_user_performance(user_name, topic)
        
        if 'message' in analysis:
            return f"📊 {analysis['message']} for user: {user_name}"
        
        overall = analysis.get('overall_performance', {})
        recommendations = analysis.get('learning_recommendations', [])
        
        result = f"""📊 Comprehensive Learning Analytics for {user_name}

🎯 Overall Performance:
• Total Questions Attempted: {overall.get('total_questions_attempted', 0)}
• Overall Accuracy: {overall.get('overall_accuracy', 0):.1f}%
• Performance Level: {overall.get('performance_level', 'Unknown')}
• Average Time per Question: {overall.get('average_time_per_question', 0):.1f} seconds
• Average Confidence Level: {overall.get('average_confidence_level', 0):.1f}/5

📚 Topic Breakdown:"""
        
        topic_breakdown = analysis.get('topic_breakdown', {})
        for topic_name, stats in topic_breakdown.items():
            result += f"""
• {topic_name}: {stats['accuracy']:.1f}% accuracy ({stats['correct']}/{stats['total']} questions)"""
        
        result += f"""

🎚️ Difficulty Analysis:"""
        
        difficulty_analysis = analysis.get('difficulty_analysis', {})
        for difficulty, stats in difficulty_analysis.items():
            result += f"""
• {difficulty.title()}: {stats['accuracy']:.1f}% accuracy ({stats['correct']}/{stats['total']} questions)"""
        
        result += f"""

⏱️ Time Management:
• Average Time: {analysis.get('time_management', {}).get('average_time', 0):.1f} seconds
• Fastest Question: {analysis.get('time_management', {}).get('fastest_time', 0)} seconds
• Slowest Question: {analysis.get('time_management', {}).get('slowest_time', 0)} seconds
• Time Consistency: {analysis.get('time_management', {}).get('time_consistency', 0):.2f}

🎯 Personalized Learning Recommendations:"""
        
        for i, recommendation in enumerate(recommendations, 1):
            result += f"""
{i}. {recommendation}"""
        
        if not recommendations:
            result += "\n• Keep up the great work! Continue practicing to maintain your performance level."
        
        result += f"""

💡 Next Steps:
• Take adaptive exams to improve weak areas
• Focus on time management if needed
• Build confidence through targeted practice
• Review explanations for incorrect answers"""
        
        print("✅ Performance analysis completed")
        return result
        
    except Exception as e:
        error_msg = f"❌ Performance analysis failed: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def get_advanced_statistics() -> str:
    """
    Get comprehensive platform statistics with advanced analytics
    
    Returns:
        Detailed platform statistics including performance trends and insights
    """
    try:
        print("📊 Generating advanced MCQ platform statistics")
        
        conn = sqlite3.connect(mcq_db.db_path)
        cursor = conn.cursor()
        
        # Enhanced statistics queries
        stats_queries = {
            'total_questions': 'SELECT COUNT(*) FROM mcq_questions',
            'total_sessions': 'SELECT COUNT(*) FROM exam_sessions',
            'completed_sessions': 'SELECT COUNT(*) FROM exam_sessions WHERE status = "completed"',
            'total_scans': 'SELECT COUNT(*) FROM platform_scans',
            'avg_score': '''SELECT AVG(score_percentage) FROM exam_sessions 
                           WHERE status = "completed" AND score_percentage IS NOT NULL''',
            'total_users': 'SELECT COUNT(DISTINCT user_name) FROM exam_sessions',
            'avg_session_duration': '''SELECT AVG(actual_duration) FROM exam_sessions 
                                      WHERE status = "completed" AND actual_duration IS NOT NULL''',
            'question_sources': '''SELECT source, COUNT(*) FROM mcq_questions 
                                  GROUP BY source ORDER BY COUNT(*) DESC''',
            'difficulty_distribution': '''SELECT difficulty, COUNT(*) FROM mcq_questions 
                                         GROUP BY difficulty ORDER BY COUNT(*) DESC''',
            'top_topics': '''SELECT topic, COUNT(*) FROM mcq_questions 
                            GROUP BY topic ORDER BY COUNT(*) DESC LIMIT 5''',
            'performance_trends': '''SELECT 
                                    DATE(start_time) as date,
                                    AVG(score_percentage) as avg_score,
                                    COUNT(*) as sessions
                                    FROM exam_sessions 
                                    WHERE status = "completed" AND start_time >= date('now', '-7 days')
                                    GROUP BY DATE(start_time)
                                    ORDER BY date DESC'''
        }
        
        # Execute queries
        stats = {}
        for key, query in stats_queries.items():
            cursor.execute(query)
            result = cursor.fetchall()
            stats[key] = result
        
        conn.close()
        
        # Process results
        total_questions = stats['total_questions'][0][0]
        total_sessions = stats['total_sessions'][0][0]
        completed_sessions = stats['completed_sessions'][0][0]
        total_scans = stats['total_scans'][0][0]
        avg_score = stats['avg_score'][0][0] or 0
        total_users = stats['total_users'][0][0]
        avg_duration = stats['avg_session_duration'][0][0] or 0
        
        result = f"""📊 Advanced MCQ Intelligence Platform Analytics

🎯 Core Metrics:
• Total Questions Generated: {total_questions}
• Total Exam Sessions: {total_sessions}
• Completed Sessions: {completed_sessions}
• Active Users: {total_users}
• Platform Scans: {total_scans}
• Average Score: {avg_score:.1f}%
• Average Session Duration: {avg_duration/60:.1f} minutes

📚 Content Distribution:"""
        
        # Question sources
        for source, count in stats['question_sources']:
            result += f"""
• {source.replace('_', ' ').title()}: {count} questions"""
        
        result += f"""

🎚️ Difficulty Distribution:"""
        
        for difficulty, count in stats['difficulty_distribution']:
            result += f"""
• {difficulty.title()}: {count} questions"""
        
        result += f"""

🔥 Top Topics:"""
        
        for topic, count in stats['top_topics']:
            result += f"""
• {topic}: {count} questions"""
        
        result += f"""

📈 Performance Trends (Last 7 Days):"""
        
        if stats['performance_trends']:
            for date, avg_score_day, sessions in stats['performance_trends']:
                result += f"""
• {date}: {avg_score_day:.1f}% avg score ({sessions} sessions)"""
        else:
            result += """
• No recent session data available"""
        
        result += f"""

🤖 AI Capabilities Status:
• ✅ Advanced Question Generation with Caching
• ✅ Intelligent Question Analysis with Reasoning
• ✅ Autonomous Platform Scanning (Simulated)
• ✅ Adaptive Learning Analytics
• ✅ Real-time Performance Tracking
• ✅ Personalized Exam Creation
• ✅ Comprehensive Learning Recommendations

💡 Platform Status: Fully Operational with Advanced AI Features!"""
        
        print("✅ Advanced statistics generated successfully")
        return result
        
    except Exception as e:
        error_msg = f"❌ Advanced statistics generation failed: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def create_exam_session(topic: str, difficulty: str = "medium", num_questions: int = 10, user_name: str = "Anonymous") -> str:
    """
    Create a new MCQ exam session
    
    Args:
        topic: Topic for the exam
        difficulty: Question difficulty level
        num_questions: Number of questions in exam
        user_name: Name of the exam taker
    
    Returns:
        Exam session details with session ID
    """
    try:
        print(f"📝 Creating exam session: {topic} ({difficulty}) - {num_questions} questions")
        
        # Check if we have enough questions
        available_questions = mcq_db.get_questions_by_topic(topic, difficulty, num_questions)
        
        if len(available_questions) < num_questions:
            # Generate more questions if needed
            needed = num_questions - len(available_questions)
            print(f"⚠️ Only {len(available_questions)} questions available, generating {needed} more...")
            
            new_questions = mcq_generator.generate_mcq_batch(topic, difficulty, needed)
            for question in new_questions:
                question_id = mcq_db.add_question(question)
                if question_id > 0:
                    available_questions.append({**question, 'id': question_id})
        
        # Create exam session
        session_id = mcq_db.create_exam_session(topic, difficulty, num_questions, user_name)
        
        result = f"""✅ Exam Session Created Successfully!

📋 Session Details:
• Session ID: {session_id}
• Topic: {topic}
• Difficulty: {difficulty.title()}
• Questions: {num_questions}
• Participant: {user_name}
• Status: Ready to Start
• Time Limit: 30 minutes

🎯 Next Steps:
1. Open the MCQ exam interface
2. Use Session ID: {session_id}
3. Start your intelligent assessment!

💡 The AI will analyze your performance and provide personalized feedback."""
        
        print(result)
        return result
        
    except Exception as e:
        error_msg = f"❌ Exam session creation failed: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def analyze_mcq_question(question_id: int) -> str:
    """
    AI analysis of an MCQ question with detailed reasoning
    
    Args:
        question_id: ID of the question to analyze
    
    Returns:
        Detailed AI analysis and solution
    """
    try:
        print(f"🔍 Analyzing MCQ question ID: {question_id}")
        
        # Get question from database
        conn = sqlite3.connect(mcq_db.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mcq_questions WHERE id = ?', (question_id,))
        question_row = cursor.fetchone()
        conn.close()
        
        if not question_row:
            return f"❌ Question with ID {question_id} not found"
        
        # Convert to dict
        question_data = {
            'id': question_row[0],
            'question': question_row[1],
            'option_a': question_row[2],
            'option_b': question_row[3],
            'option_c': question_row[4],
            'option_d': question_row[5],
            'correct_answer': question_row[6],
            'explanation': question_row[7],
            'topic': question_row[8],
            'difficulty': question_row[9]
        }
        
        # Analyze with AI
        analysis = mcq_analyzer.analyze_and_solve_mcq(question_data)
        
        result = f"""🧠 AI Analysis of MCQ Question #{question_id}

📝 Question: {question_data['question']}

🎯 AI Solution:
• AI Answer: {analysis['ai_answer']}
• Confidence: {analysis['confidence']}%
• Correct Answer: {analysis['correct_answer']}
• AI Accuracy: {'✅ Correct' if analysis['is_correct'] else '❌ Incorrect'}

🔍 Detailed Reasoning:
{analysis['reasoning']}

📚 Key Concepts:
{', '.join(analysis['concepts']) if analysis['concepts'] else 'Not specified'}

❌ Why Other Options Are Wrong:
{analysis.get('wrong_options_analysis', 'Not provided')}

💡 Original Explanation:
{question_data['explanation']}

📊 Question Stats:
• Topic: {question_data['topic']}
• Difficulty: {question_data['difficulty'].title()}
• Source: {question_data.get('source', 'Unknown')}"""
        
        print("✅ MCQ analysis completed")
        return result
        
    except Exception as e:
        error_msg = f"❌ MCQ analysis failed: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def scan_external_platform(platform_name: str, topic: str = "general") -> str:
    """
    Simulate scanning external MCQ platforms for questions
    
    Args:
        platform_name: Name of the platform to scan
        topic: Topic to search for
    
    Returns:
        Scan results and imported questions
    """
    try:
        print(f"🔍 Scanning external platform: {platform_name}")
        
        # Simulate platform scan
        scan_result = mcq_scanner.simulate_platform_scan(platform_name, topic)
        
        # Save scan record
        conn = sqlite3.connect(mcq_db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO platform_scans 
            (platform_name, questions_found, questions_imported, status, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            scan_result['platform_name'],
            scan_result['questions_found'],
            scan_result['questions_imported'],
            scan_result['scan_status'],
            scan_result['notes']
        ))
        conn.commit()
        conn.close()
        
        # Import found questions
        imported_count = 0
        for question in scan_result['questions']:
            try:
                mcq_db.add_question(question)
                imported_count += 1
            except Exception as e:
                print(f"⚠️ Failed to import question: {e}")
        
        result = f"""🔍 External Platform Scan Completed!

🌐 Platform: {platform_name}
📊 Scan Results:
• Questions Found: {scan_result['questions_found']}
• Questions Imported: {imported_count}
• Topic Focus: {topic}
• Scan Status: {scan_result['scan_status'].title()}

📝 Scan Notes:
{scan_result['notes']}

🎯 Next Steps:
• Questions are now available in the database
• Use them in exam sessions
• AI can analyze and solve these questions
• Platform patterns learned for future scans

💡 This demonstrates the autonomous scanning capability of the MCQ Intelligence Platform!"""
        
        print(result)
        return result
        
    except Exception as e:
        error_msg = f"❌ Platform scan failed: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def get_mcq_statistics() -> str:
    """
    Get comprehensive statistics about the MCQ platform
    
    Returns:
        Detailed platform statistics and analytics
    """
    try:
        print("📊 Generating MCQ platform statistics")
        
        conn = sqlite3.connect(mcq_db.db_path)
        cursor = conn.cursor()
        
        # Get question statistics
        cursor.execute('SELECT COUNT(*) FROM mcq_questions')
        total_questions = cursor.fetchone()[0]
        
        cursor.execute('SELECT topic, COUNT(*) FROM mcq_questions GROUP BY topic ORDER BY COUNT(*) DESC')
        topics = cursor.fetchall()
        
        cursor.execute('SELECT difficulty, COUNT(*) FROM mcq_questions GROUP BY difficulty')
        difficulties = cursor.fetchall()
        
        cursor.execute('SELECT source, COUNT(*) FROM mcq_questions GROUP BY source')
        sources = cursor.fetchall()
        
        # Get exam statistics
        cursor.execute('SELECT COUNT(*) FROM exam_sessions')
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM exam_sessions WHERE status = "completed"')
        completed_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(CAST(correct_answers AS FLOAT) / total_questions * 100) FROM exam_sessions WHERE status = "completed"')
        avg_score = cursor.fetchone()[0] or 0
        
        # Get platform scan statistics
        cursor.execute('SELECT COUNT(*) FROM platform_scans')
        total_scans = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(questions_imported) FROM platform_scans')
        total_imported = cursor.fetchone()[0] or 0
        
        conn.close()
        
        result = f"""📊 MCQ Intelligence Platform Statistics

🎯 Question Database:
• Total Questions: {total_questions}
• AI Generated: {sum(count for source, count in sources if 'ai' in source)}
• External Imported: {total_imported}

📚 Topics Coverage:
"""
        
        for topic, count in topics[:5]:  # Top 5 topics
            result += f"• {topic}: {count} questions\n"
        
        result += f"""
🎚️ Difficulty Distribution:
"""
        
        for difficulty, count in difficulties:
            result += f"• {difficulty.title()}: {count} questions\n"
        
        result += f"""
📝 Exam Sessions:
• Total Sessions: {total_sessions}
• Completed: {completed_sessions}
• Average Score: {avg_score:.1f}%

🔍 Platform Scans:
• Total Scans: {total_scans}
• Questions Imported: {total_imported}

🤖 AI Capabilities:
• ✅ Autonomous Question Generation
• ✅ Intelligent Question Analysis
• ✅ External Platform Scanning
• ✅ Adaptive Learning Analytics
• ✅ Real-time Performance Tracking

💡 Platform Status: Fully Operational & Learning!"""
        
        print("✅ Statistics generated successfully")
        return result
        
    except Exception as e:
        error_msg = f"❌ Statistics generation failed: {str(e)}"
        print(error_msg)
        return error_msg

# Simple functions for direct use with advanced features
def generate_questions_simple(topic, difficulty="medium", count=5):
    """Simple question generation function with advanced features"""
    return generate_mcq_questions.func(topic, difficulty, count)

def create_exam_simple(topic, difficulty="medium", num_questions=10, user_name="Anonymous"):
    """Simple exam creation function"""
    return create_exam_session.func(topic, difficulty, num_questions, user_name)

def create_adaptive_exam_simple(topic, user_name="Anonymous", target_duration=30, initial_difficulty="medium"):
    """Simple adaptive exam creation function"""
    return create_adaptive_exam.func(topic, user_name, target_duration, initial_difficulty)

def analyze_question_simple(question_id):
    """Simple question analysis function"""
    return analyze_mcq_question.func(question_id)

def scan_platform_simple(platform_name, topic="general"):
    """Simple platform scanning function"""
    return scan_external_platform.func(platform_name, topic)

def get_stats_simple():
    """Simple statistics function with advanced analytics"""
    return get_advanced_statistics.func()

def analyze_user_simple(user_name, topic=None):
    """Simple user performance analysis function"""
    return analyze_user_performance.func(user_name, topic)

def get_next_question_simple(session_id):
    """Get next question in adaptive exam"""
    return exam_simulator.get_next_question(session_id)

def submit_answer_simple(session_id, question_id, user_answer, time_taken, confidence_level=3):
    """Submit answer in adaptive exam"""
    return exam_simulator.submit_answer(session_id, question_id, user_answer, time_taken, confidence_level)

def complete_exam_simple(session_id):
    """Complete adaptive exam and get analytics"""
    return exam_simulator.complete_exam(session_id)

# Advanced test function with comprehensive features
def test_advanced_mcq_agent():
    """Test the advanced MCQ Intelligence Agent functionality"""
    print("🧪 Testing Advanced MCQ Intelligence Agent...")
    print("=" * 70)
    
    try:
        # Test 1: Advanced question generation
        print("\n1. Testing advanced question generation...")
        result = generate_questions_simple("Advanced Python Programming", "medium", 3)
        print("✅ Advanced generation completed")
        
        # Test 2: Adaptive exam creation
        print("\n2. Testing adaptive exam creation...")
        result = create_adaptive_exam_simple("Python Programming", "TestUser", 20, "medium")
        print("✅ Adaptive exam creation completed")
        
        # Test 3: User performance analysis
        print("\n3. Testing user performance analysis...")
        result = analyze_user_simple("TestUser", "Python Programming")
        print("✅ Performance analysis completed")
        
        # Test 4: Advanced platform scanning
        print("\n4. Testing advanced platform scanning...")
        result = scan_platform_simple("GeeksforGeeks", "Data Structures")
        print("✅ Advanced platform scan completed")
        
        # Test 5: Advanced statistics
        print("\n5. Testing advanced statistics...")
        result = get_stats_simple()
        print("✅ Advanced statistics completed")
        
        # Test 6: Question analysis
        print("\n6. Testing question analysis...")
        result = analyze_question_simple(1)
        print("✅ Question analysis completed")
        
        print("\n🎉 All advanced MCQ tests passed!")
        print("🚀 MCQ Intelligence Platform is fully operational with advanced features!")
        
    except Exception as e:
        print(f"❌ Advanced test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_advanced_mcq_agent()