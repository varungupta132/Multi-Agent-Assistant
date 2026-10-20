#!/usr/bin/env python3
"""
Multi-Agent AI Framework - Web Frontend
Beautiful Flask web interface for the AI agent system
"""
from flask import Flask, render_template, request, jsonify
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add framework to path
sys.path.append('framework_multiagent')

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Import agent functions
def send_whatsapp_message(to, user_request):
    """Send WhatsApp message using the agent"""
    try:
        from llm.message_generator import generate_whatsapp_message
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, DEFAULT_PHONE_RECIPIENT
        from twilio.rest import Client
        
        # Generate message with Ollama
        message = generate_whatsapp_message(user_request)
        
        # Format phone number (remove spaces and format properly)
        if not to:
            to = DEFAULT_PHONE_RECIPIENT
        
        # Remove all spaces and non-digit characters except +
        to = ''.join(char for char in to if char.isdigit() or char == '+')
        
        if not to.startswith('whatsapp:'):
            if not to.startswith('+'):
                to = '+91' + to
            to = f'whatsapp:{to}'
        
        # Send via Twilio
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=to
        )
        
        return {
            'success': True,
            'message': message,
            'sid': msg.sid,
            'to': to
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def send_email_message(to, user_request):
    """Send email using the agent"""
    try:
        from agents.email_agent import send_email
        
        result = send_email.invoke({
            "to": to,
            "user_request": user_request,
            "subject": "",
            "body": ""
        })
        
        return {
            'success': True,
            'result': result,
            'to': to
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def make_voice_call(to, user_request):
    """Make voice call using the agent"""
    try:
        from agents.call_agent import make_call
        
        result = make_call.invoke({
            "to": to,
            "user_request": user_request,
            "message": ""
        })
        
        return {
            'success': True,
            'result': result,
            'to': to
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/whatsapp')
def whatsapp_page():
    """WhatsApp agent page"""
    return render_template('whatsapp.html')

@app.route('/email')
def email_page():
    """Email agent page"""
    return render_template('email.html')

@app.route('/task')
def task_page():
    """Task management page"""
    return render_template('task.html')

@app.route('/api/task', methods=['POST'])
def api_task():
    """API endpoint for task management"""
    try:
        data = request.get_json()
        operation = data.get('operation', 'create')
        
        print(f"📝 Task API called: operation={operation}, data={data}")
        
        if operation == 'create':
            task_name = data.get('task_name', '').strip()
            task_description = data.get('task_description', '').strip()
            deadline = data.get('deadline', '').strip()
            
            if not task_name:
                return jsonify({'success': False, 'error': 'Task name is required'})
            
            # Import here to avoid circular imports
            sys.path.append('framework_multiagent')
            from agents.task_agent import create_task_simple
            
            result = create_task_simple(task_name, task_description, deadline)
            
            return jsonify({
                'success': True,
                'result': result,
                'task_name': task_name
            })
            
        elif operation == 'create_smart':
            user_input = data.get('user_input', '').strip()
            end_time = data.get('end_time', '').strip()
            
            if not user_input:
                return jsonify({'success': False, 'error': 'Please describe what you want to do'})
            
            # Import here to avoid circular imports
            sys.path.append('framework_multiagent')
            from agents.task_agent import create_smart_task_simple
            
            result = create_smart_task_simple(user_input, end_time)
            
            return jsonify({
                'success': True,
                'result': result,
                'user_input': user_input
            })
            
        elif operation == 'list':
            sys.path.append('framework_multiagent')
            from agents.task_agent import get_live_tasks_simple
            
            result = get_live_tasks_simple()
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        elif operation == 'complete':
            task_id = data.get('task_id', 0)
            
            if not task_id:
                return jsonify({'success': False, 'error': 'Task ID is required'})
            
            sys.path.append('framework_multiagent')
            from agents.task_agent import complete_task_simple
            
            result = complete_task_simple(task_id)
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        elif operation == 'test_alert':
            task_name = data.get('task_name', 'Test Task')
            
            sys.path.append('framework_multiagent')
            from agents.task_agent import test_alert_simple
            
            result = test_alert_simple(task_name)
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        elif operation == 'check_alerts':
            sys.path.append('framework_multiagent')
            from agents.task_agent import force_check_alerts_simple
            
            result = force_check_alerts_simple()
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        else:
            return jsonify({'success': False, 'error': f'Invalid operation: {operation}'})
            
    except Exception as e:
        print(f"❌ Task API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/task/live', methods=['GET'])
def api_task_live():
    """API endpoint for live task data"""
    try:
        print("📊 Live task data requested")
        
        sys.path.append('framework_multiagent')
        from agents.task_agent import task_tracker
        
        live_tasks = task_tracker.get_live_task_data()
        
        print(f"✅ Returning {len(live_tasks)} live tasks")
        
        return jsonify({
            'success': True,
            'tasks': live_tasks,
            'count': len(live_tasks),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Live task API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'tasks': []
        })

@app.route('/api/whatsapp', methods=['POST'])
def api_whatsapp():
    """API endpoint for WhatsApp messages"""
    data = request.get_json()
    to = data.get('to', '')
    user_request = data.get('message', '')
    
    if not user_request:
        return jsonify({'success': False, 'error': 'Message is required'})
    
    result = send_whatsapp_message(to, user_request)
    return jsonify(result)

@app.route('/api/email', methods=['POST'])
def api_email():
    """API endpoint for emails"""
    data = request.get_json()
    to = data.get('to', '')
    user_request = data.get('message', '')
    
    if not user_request:
        return jsonify({'success': False, 'error': 'Message is required'})
    
    result = send_email_message(to, user_request)
    return jsonify(result)

@app.route('/call')
def call_page():
    """Call agent page"""
    return render_template('call.html')

@app.route('/flight')
def flight_page():
    """Flight booking agent page"""
    return render_template('flight.html')

@app.route('/flight-platform')
def flight_platform_page():
    """Demo flight booking platform page"""
    return render_template('flight_platform.html')

@app.route('/music')
def music_page():
    """Mood-aware music agent page"""
    return render_template('music.html')

@app.route('/mcq')
def mcq_page():
    """MCQ Intelligence Platform page"""
    return render_template('mcq.html')

@app.route('/api/call', methods=['POST'])
def api_call():
    """API endpoint for voice calls"""
    data = request.get_json()
    to = data.get('to', '')
    user_request = data.get('message', '')
    
    if not user_request:
        return jsonify({'success': False, 'error': 'Message is required'})
    
    result = make_voice_call(to, user_request)
    return jsonify(result)

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API endpoint to generate message preview"""
    data = request.get_json()
    user_request = data.get('message', '')
    agent_type = data.get('type', 'whatsapp')
    
    if not user_request:
        return jsonify({'success': False, 'error': 'Message is required'})
    
    try:
        if agent_type == 'whatsapp':
            from llm.message_generator import generate_whatsapp_message
            generated = generate_whatsapp_message(user_request)
        elif agent_type == 'email':
            from llm.message_generator import generate_email_content
            generated = generate_email_content(user_request)
        elif agent_type == 'call':
            from llm.message_generator import generate_voice_message
            generated = generate_voice_message(user_request)
        else:
            return jsonify({'success': False, 'error': 'Invalid agent type'})
        
        return jsonify({
            'success': True,
            'generated': generated
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/flight/book', methods=['POST'])
def api_flight_book():
    """API endpoint for autonomous flight booking"""
    try:
        data = request.get_json()
        user_request = data.get('user_request', '').strip()
        passenger_name = data.get('passenger_name', 'AI User').strip()
        
        if not user_request:
            return jsonify({'success': False, 'error': 'Booking request is required'})
        
        if not passenger_name:
            return jsonify({'success': False, 'error': 'Passenger name is required'})
        
        print(f"✈️ Flight booking API called: {user_request}")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.flight_agent import book_flight_simple
        
        result = book_flight_simple(user_request, passenger_name)
        
        return jsonify({
            'success': True,
            'result': result,
            'user_request': user_request,
            'passenger_name': passenger_name
        })
        
    except Exception as e:
        print(f"❌ Flight booking API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/flight/search', methods=['POST'])
def api_flight_search():
    """API endpoint for flight search"""
    try:
        data = request.get_json()
        from_city = data.get('from_city', '').strip()
        to_city = data.get('to_city', '').strip()
        travel_date = data.get('travel_date', '').strip()
        passengers = data.get('passengers', 1)
        
        if not from_city or not to_city or not travel_date:
            return jsonify({'success': False, 'error': 'All search fields are required'})
        
        if from_city == to_city:
            return jsonify({'success': False, 'error': 'Source and destination cannot be the same'})
        
        print(f"🔍 Flight search API called: {from_city} → {to_city} on {travel_date}")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.flight_agent import search_flights_simple
        
        result = search_flights_simple(from_city, to_city, travel_date, passengers)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        print(f"❌ Flight search API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/flight/history', methods=['GET'])
def api_flight_history():
    """API endpoint for flight booking history"""
    try:
        print("📋 Flight history API called")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.flight_agent import flight_agent
        
        # Get raw booking data from database
        import sqlite3
        conn = sqlite3.connect(flight_agent.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bookings ORDER BY booking_time DESC')
        bookings_raw = cursor.fetchall()
        conn.close()
        
        # Convert to structured format
        bookings = []
        for booking in bookings_raw:
            bookings.append({
                'id': booking[0],
                'booking_id': booking[1],
                'passenger_name': booking[2],
                'flight_id': booking[3],
                'from_city': booking[4],
                'to_city': booking[5],
                'travel_date': booking[6],
                'departure_time': booking[7],
                'seats_booked': booking[8],
                'total_price': booking[9],
                'status': booking[10],
                'booking_time': booking[11]
            })
        
        # Also get text format for backward compatibility
        from agents.flight_agent import get_bookings_simple
        result_text = get_bookings_simple()
        
        return jsonify({
            'success': True,
            'result': result_text,
            'bookings': bookings,
            'count': len(bookings)
        })
        
    except Exception as e:
        print(f"❌ Flight history API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'bookings': []
        })

@app.route('/api/flight/stats', methods=['GET'])
def api_flight_stats():
    """API endpoint for flight platform statistics"""
    try:
        print("📊 Flight stats API called")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.flight_agent import flight_agent
        
        import sqlite3
        conn = sqlite3.connect(flight_agent.db.db_path)
        cursor = conn.cursor()
        
        # Get total flights
        cursor.execute('SELECT COUNT(*) FROM flights')
        total_flights = cursor.fetchone()[0]
        
        # Get total bookings
        cursor.execute('SELECT COUNT(*) FROM bookings')
        total_bookings = cursor.fetchone()[0]
        
        # Get total passengers
        cursor.execute('SELECT SUM(seats_booked) FROM bookings')
        total_passengers = cursor.fetchone()[0] or 0
        
        # Get total revenue
        cursor.execute('SELECT SUM(total_price) FROM bookings')
        total_revenue = cursor.fetchone()[0] or 0
        
        conn.close()
        
        stats = {
            'total_flights': total_flights,
            'total_bookings': total_bookings,
            'total_passengers': total_passengers,
            'total_revenue': total_revenue
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ Flight stats API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'stats': {
                'total_flights': 0,
                'total_bookings': 0,
                'total_passengers': 0,
                'total_revenue': 0
            }
        })

@app.route('/api/flight/available', methods=['GET'])
def api_flight_available():
    """API endpoint for available flights"""
    try:
        route = request.args.get('route', '')
        date = request.args.get('date', '')
        
        print(f"🔍 Available flights API called: route={route}, date={date}")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.flight_agent import flight_agent
        
        import sqlite3
        conn = sqlite3.connect(flight_agent.db.db_path)
        cursor = conn.cursor()
        
        # Build query based on filters
        query = 'SELECT * FROM flights WHERE available_seats > 0'
        params = []
        
        if route:
            # Parse route like "Delhi → Mumbai"
            if '→' in route:
                from_city, to_city = route.split('→')
                query += ' AND from_city = ? AND to_city = ?'
                params.extend([from_city.strip(), to_city.strip()])
        
        if date:
            query += ' AND departure_date = ?'
            params.append(date)
        
        query += ' ORDER BY departure_time'
        
        cursor.execute(query, params)
        flights_raw = cursor.fetchall()
        conn.close()
        
        # Convert to structured format
        flights = []
        for flight in flights_raw:
            flights.append({
                'id': flight[0],
                'flight_no': flight[1],
                'airline': flight[2],
                'from_city': flight[3],
                'to_city': flight[4],
                'departure_date': flight[5],
                'departure_time': flight[6],
                'arrival_time': flight[7],
                'available_seats': flight[8],
                'price': flight[9],
                'aircraft': flight[10]
            })
        
        return jsonify({
            'success': True,
            'flights': flights,
            'count': len(flights)
        })
        
    except Exception as e:
        print(f"❌ Available flights API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'flights': []
        })

@app.route('/api/music/play', methods=['POST'])
def api_music_play():
    """API endpoint for mood-based music playing"""
    try:
        data = request.get_json()
        mood_input = data.get('mood_input', '').strip()
        
        if not mood_input:
            return jsonify({'success': False, 'error': 'Mood input is required'})
        
        print(f"🎵 Music play API called: {mood_input}")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.music_agent import play_music_for_mood
        
        result = play_music_for_mood(mood_input)
        
        return jsonify({
            'success': True,
            'result': result,
            'mood_input': mood_input
        })
        
    except Exception as e:
        print(f"❌ Music play API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/music/library', methods=['GET'])
def api_music_library():
    """API endpoint for music library information"""
    try:
        print("📚 Music library API called")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.music_agent import get_music_info
        
        result = get_music_info()
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        print(f"❌ Music library API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/music/history', methods=['GET'])
def api_music_history():
    """API endpoint for playlist history"""
    try:
        print("📋 Music history API called")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.music_agent import get_music_history
        
        result = get_music_history()
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        print(f"❌ Music history API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/music/control', methods=['POST'])
def api_music_control():
    """API endpoint for music playback control"""
    try:
        data = request.get_json()
        action = data.get('action', '').strip()
        value = data.get('value')
        
        if not action:
            return jsonify({'success': False, 'error': 'Action is required'})
        
        print(f"🎮 Music control API called: {action} (value: {value})")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.music_agent import control_music
        
        result = control_music(action, value)
        
        return jsonify({
            'success': True,
            'result': result,
            'action': action
        })
        
    except Exception as e:
        print(f"❌ Music control API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/music/custom', methods=['POST'])
def api_music_custom():
    """API endpoint for creating custom playlists"""
    try:
        data = request.get_json()
        mood_description = data.get('mood_description')
        song_count = data.get('song_count', 10)
        energy_preference = data.get('energy_preference', 'balanced')
        
        if not mood_description:
            return jsonify({'success': False, 'error': 'Mood description is required'})
        
        print(f"🎵 Custom playlist API called: {mood_description}")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.music_agent import create_playlist
        
        result = create_playlist(mood_description, song_count, energy_preference)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        print(f"❌ Custom playlist API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/music/details', methods=['GET'])
def api_music_details():
    """API endpoint for current song details"""
    try:
        print("🎵 Song details API called")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.music_agent import get_song_details
        
        result = get_song_details()
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        print(f"❌ Song details API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/mcq/generate', methods=['POST'])
def api_mcq_generate():
    """API endpoint for MCQ question generation"""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        difficulty = data.get('difficulty', 'medium').strip()
        count = data.get('count', 5)
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic is required'})
        
        # Limit count to prevent long processing times
        if count > 3:
            count = 3
            
        print(f"🧠 MCQ generation API called: {topic} ({difficulty}) - {count} questions")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.mcq_agent import generate_questions_simple
        
        # Use threading with timeout
        import threading
        import time
        
        result_container = {'result': None, 'error': None}
        
        def generate_with_timeout():
            try:
                result_container['result'] = generate_questions_simple(topic, difficulty, count)
            except Exception as e:
                result_container['error'] = str(e)
        
        # Start generation in separate thread
        thread = threading.Thread(target=generate_with_timeout)
        thread.daemon = True
        thread.start()
        
        # Wait for completion with timeout
        thread.join(timeout=25)  # 25 second timeout
        
        if thread.is_alive():
            # Thread is still running, return partial success
            return jsonify({
                'success': True,
                'result': f"✅ Question generation started for {topic} ({difficulty} level). Processing {count} questions in background. Check statistics for updates.",
                'topic': topic,
                'difficulty': difficulty,
                'count': count,
                'note': 'Processing in background due to time limit'
            })
        
        if result_container['error']:
            return jsonify({
                'success': False,
                'error': result_container['error']
            })
        
        return jsonify({
            'success': True,
            'result': result_container['result'],
            'topic': topic,
            'difficulty': difficulty,
            'count': count
        })
        
    except Exception as e:
        print(f"❌ MCQ generation API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/mcq/exam', methods=['POST'])
def api_mcq_exam():
    """API endpoint for creating MCQ exam sessions"""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        difficulty = data.get('difficulty', 'medium').strip()
        num_questions = data.get('num_questions', 10)
        user_name = data.get('user_name', 'Anonymous').strip()
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic is required'})
        
        print(f"📝 MCQ exam creation API called: {topic} ({difficulty}) - {num_questions} questions")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.mcq_agent import create_exam_simple
        
        result = create_exam_simple(topic, difficulty, num_questions, user_name)
        
        return jsonify({
            'success': True,
            'result': result,
            'topic': topic,
            'difficulty': difficulty,
            'num_questions': num_questions,
            'user_name': user_name
        })
        
    except Exception as e:
        print(f"❌ MCQ exam creation API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/mcq/analyze', methods=['POST'])
def api_mcq_analyze():
    """API endpoint for MCQ question analysis"""
    try:
        data = request.get_json()
        question_id = data.get('question_id', 1)
        
        if not question_id or question_id < 1:
            return jsonify({'success': False, 'error': 'Valid question ID is required'})
        
        print(f"🔍 MCQ analysis API called: question ID {question_id}")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.mcq_agent import analyze_question_simple
        
        result = analyze_question_simple(question_id)
        
        return jsonify({
            'success': True,
            'result': result,
            'question_id': question_id
        })
        
    except Exception as e:
        print(f"❌ MCQ analysis API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/mcq/scan', methods=['POST'])
def api_mcq_scan():
    """API endpoint for external platform scanning"""
    try:
        data = request.get_json()
        platform_name = data.get('platform_name', '').strip()
        topic = data.get('topic', 'general').strip()
        
        if not platform_name:
            return jsonify({'success': False, 'error': 'Platform name is required'})
        
        print(f"🔍 MCQ platform scan API called: {platform_name} for {topic}")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.mcq_agent import scan_platform_simple
        
        result = scan_platform_simple(platform_name, topic)
        
        return jsonify({
            'success': True,
            'result': result,
            'platform_name': platform_name,
            'topic': topic
        })
        
    except Exception as e:
        print(f"❌ MCQ platform scan API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/api/mcq/stats', methods=['GET'])
def api_mcq_stats():
    """API endpoint for MCQ platform statistics"""
    try:
        print("📊 MCQ statistics API called")
        
        # Import here to avoid circular imports
        sys.path.append('framework_multiagent')
        from agents.mcq_agent import mcq_db
        
        import sqlite3
        conn = sqlite3.connect(mcq_db.db_path)
        cursor = conn.cursor()
        
        # Get question statistics
        cursor.execute('SELECT COUNT(*) FROM mcq_questions')
        total_questions = cursor.fetchone()[0]
        
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
        
        conn.close()
        
        stats = {
            'total_questions': total_questions,
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'avg_score': avg_score,
            'total_scans': total_scans
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ MCQ statistics API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'stats': {
                'total_questions': 0,
                'total_sessions': 0,
                'completed_sessions': 0,
                'avg_score': 0,
                'total_scans': 0
            }
        })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("🚀 Starting Multi-Agent AI Framework Web Interface...")
    print("🌐 Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)