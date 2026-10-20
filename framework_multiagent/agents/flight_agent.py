"""
Autonomous Flight Booking Agent with Dummy Booking Platform
Multi-Agent Design using LangChain + LangGraph + Ollama
"""
from langchain_core.tools import tool
from datetime import datetime, timedelta
import json
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH
from llm.message_generator import MessageGenerator

class FlightDatabase:
    """Database manager for flights and bookings"""
    
    def __init__(self, db_path="flights.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize flight booking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS flights")
        cursor.execute("DROP TABLE IF EXISTS bookings")
        
        # Create flights table
        cursor.execute('''
            CREATE TABLE flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flight_no TEXT NOT NULL,
                airline TEXT NOT NULL,
                from_city TEXT NOT NULL,
                to_city TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                arrival_time TEXT NOT NULL,
                available_seats INTEGER DEFAULT 50,
                price REAL DEFAULT 5000.0,
                aircraft TEXT DEFAULT 'Boeing 737',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create bookings table
        cursor.execute('''
            CREATE TABLE bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id TEXT UNIQUE NOT NULL,
                passenger_name TEXT NOT NULL,
                flight_id INTEGER,
                from_city TEXT NOT NULL,
                to_city TEXT NOT NULL,
                travel_date TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                seats_booked INTEGER DEFAULT 1,
                total_price REAL,
                status TEXT DEFAULT 'confirmed',
                booking_time TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (flight_id) REFERENCES flights (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Flight database initialized: {self.db_path}")
        
        # Add sample flights
        self._add_sample_flights()
    
    def _add_sample_flights(self):
        """Add sample flight data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sample flights for next 7 days
        base_date = datetime.now()
        sample_flights = []
        
        routes = [
            ("Delhi", "Mumbai", "AI101", "Air India"),
            ("Delhi", "Mumbai", "AI203", "Air India"),
            ("Delhi", "Bangalore", "AI301", "Air India"),
            ("Delhi", "Bangalore", "SG401", "SpiceJet"),
            ("Mumbai", "Delhi", "AI102", "Air India"),
            ("Mumbai", "Bangalore", "AI501", "Air India"),
            ("Bangalore", "Delhi", "AI302", "Air India"),
            ("Bangalore", "Mumbai", "AI502", "Air India"),
            ("Delhi", "Chennai", "AI601", "Air India"),
            ("Chennai", "Delhi", "AI602", "Air India")
        ]
        
        times = [
            ("06:30", "08:45"),
            ("09:00", "11:15"),
            ("12:30", "14:45"),
            ("15:00", "17:15"),
            ("18:00", "20:15"),
            ("20:30", "22:45")
        ]
        
        for day_offset in range(7):  # Next 7 days
            flight_date = (base_date + timedelta(days=day_offset)).strftime('%Y-%m-%d')
            
            for from_city, to_city, flight_no, airline in routes:
                for dep_time, arr_time in times[:3]:  # 3 flights per route per day
                    sample_flights.append((
                        flight_no, airline, from_city, to_city,
                        flight_date, dep_time, arr_time,
                        45 + (day_offset * 2), 5000 + (day_offset * 100)
                    ))
        
        cursor.executemany('''
            INSERT INTO flights (flight_no, airline, from_city, to_city, departure_date, 
                               departure_time, arrival_time, available_seats, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_flights)
        
        conn.commit()
        conn.close()
        print(f"✅ Added {len(sample_flights)} sample flights")
    
    def search_flights(self, from_city, to_city, travel_date, passengers=1):
        """Search for available flights - ALWAYS returns flights for demo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First try exact match
        cursor.execute('''
            SELECT * FROM flights 
            WHERE from_city LIKE ? AND to_city LIKE ? AND departure_date = ? 
            AND available_seats >= ?
            ORDER BY departure_time
        ''', (f"%{from_city}%", f"%{to_city}%", travel_date, passengers))
        
        flights = cursor.fetchall()
        
        # If no flights found, CREATE DEMO FLIGHTS for any route
        if not flights:
            print(f"🎭 Creating demo flights for {from_city} → {to_city} on {travel_date}")
            
            # Generate demo flights for this route
            demo_flights = [
                (f"AI{hash(from_city + to_city) % 900 + 100}", "Air India", from_city, to_city, 
                 travel_date, "06:30", "08:45", 45, 5500, "Boeing 737"),
                (f"SG{hash(to_city + from_city) % 900 + 200}", "SpiceJet", from_city, to_city, 
                 travel_date, "09:15", "11:30", 38, 4800, "Airbus A320"),
                (f"6E{hash(from_city + travel_date) % 900 + 300}", "IndiGo", from_city, to_city, 
                 travel_date, "14:20", "16:35", 42, 5200, "Airbus A320"),
                (f"UK{hash(to_city + travel_date) % 900 + 400}", "Vistara", from_city, to_city, 
                 travel_date, "18:45", "21:00", 35, 6200, "Boeing 737"),
            ]
            
            # Insert demo flights
            cursor.executemany('''
                INSERT INTO flights (flight_no, airline, from_city, to_city, departure_date, 
                                   departure_time, arrival_time, available_seats, price, aircraft)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', demo_flights)
            
            conn.commit()
            
            # Now fetch the created flights
            cursor.execute('''
                SELECT * FROM flights 
                WHERE from_city = ? AND to_city = ? AND departure_date = ? 
                AND available_seats >= ?
                ORDER BY departure_time
            ''', (from_city, to_city, travel_date, passengers))
            
            flights = cursor.fetchall()
        
        conn.close()
        
        print(f"✈️ Found {len(flights)} flights from {from_city} to {to_city} on {travel_date}")
        return flights
    
    def book_flight(self, flight_id, passenger_name, seats=1):
        """Book a flight and generate booking ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get flight details
        cursor.execute('SELECT * FROM flights WHERE id = ?', (flight_id,))
        flight = cursor.fetchone()
        
        if not flight:
            conn.close()
            return None, "Flight not found"
        
        if flight[8] < seats:  # available_seats
            conn.close()
            return None, f"Only {flight[8]} seats available"
        
        # Generate booking ID
        booking_id = f"BK{datetime.now().strftime('%Y%m%d')}{flight_id:03d}"
        
        # Create booking
        total_price = flight[9] * seats  # price * seats
        
        cursor.execute('''
            INSERT INTO bookings (booking_id, passenger_name, flight_id, from_city, to_city,
                                travel_date, departure_time, seats_booked, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (booking_id, passenger_name, flight_id, flight[3], flight[4], 
              flight[5], flight[6], seats, total_price))
        
        # Update available seats
        cursor.execute('''
            UPDATE flights SET available_seats = available_seats - ? WHERE id = ?
        ''', (seats, flight_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Flight booked: {booking_id}")
        return booking_id, "Booking successful"
class FlightBookingAgent:
    """AI-powered flight booking agent"""
    
    def __init__(self):
        self.db = FlightDatabase()
        self.message_generator = MessageGenerator()
    
    def parse_booking_request(self, user_input):
        """Parse natural language booking request using AI - Enhanced for any city"""
        try:
            print(f"🧠 Parsing flight request: {user_input}")
            
            parsing_prompt = f"""
            Parse this flight booking request and extract details: "{user_input}"
            
            IMPORTANT: Extract ANY city names mentioned, even if they're not major cities.
            
            Extract:
            1. Source city (departure from) - ANY city name
            2. Destination city (arrival to) - ANY city name  
            3. Travel date (convert to YYYY-MM-DD format)
            4. Time preference (morning/afternoon/evening)
            5. Number of passengers (default 1)
            
            Current date: {datetime.now().strftime('%Y-%m-%d')}
            
            Rules:
            - If user says "tomorrow", use {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
            - If user says "today", use {datetime.now().strftime('%Y-%m-%d')}
            - If user mentions a date like "31st" or "March 31", convert to proper format
            - Extract ANY city name, even small cities like Mathura, Agra, etc.
            
            Format response as:
            FROM: [city name]
            TO: [city name]
            DATE: [YYYY-MM-DD]
            TIME: [morning/afternoon/evening/any]
            PASSENGERS: [number]
            
            Examples:
            "book ticket from Mathura to Delhi on 31st"
            FROM: Mathura
            TO: Delhi
            DATE: 2026-03-31
            TIME: any
            PASSENGERS: 1
            
            "flight from Agra to Mumbai tomorrow morning"
            FROM: Agra
            TO: Mumbai  
            DATE: {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
            TIME: morning
            PASSENGERS: 1
            
            "book flight Jaipur to Bangalore on March 15th for 2 people"
            FROM: Jaipur
            TO: Bangalore
            DATE: 2026-03-15
            TIME: any
            PASSENGERS: 2
            
            Your parsing:
            """
            
            response = self.message_generator.llm.invoke(parsing_prompt)
            
            # Parse AI response
            parsed_data = {
                'from_city': 'Delhi',
                'to_city': 'Mumbai', 
                'travel_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time_preference': 'any',
                'passengers': 1
            }
            
            lines = response.strip().split('\n')
            for line in lines:
                if 'FROM:' in line:
                    city = line.split('FROM:')[-1].strip()
                    if city and len(city) > 1:
                        parsed_data['from_city'] = city.title()
                elif 'TO:' in line:
                    city = line.split('TO:')[-1].strip()
                    if city and len(city) > 1:
                        parsed_data['to_city'] = city.title()
                elif 'DATE:' in line:
                    date_str = line.split('DATE:')[-1].strip()
                    try:
                        # Validate date format
                        datetime.strptime(date_str, '%Y-%m-%d')
                        parsed_data['travel_date'] = date_str
                    except:
                        pass
                elif 'TIME:' in line:
                    parsed_data['time_preference'] = line.split('TIME:')[-1].strip().lower()
                elif 'PASSENGERS:' in line:
                    try:
                        parsed_data['passengers'] = int(line.split('PASSENGERS:')[-1].strip())
                    except:
                        pass
            
            # Fallback parsing from the original input if AI parsing didn't work well
            user_lower = user_input.lower()
            
            # Extract cities using common patterns
            import re
            
            # Look for "from X to Y" pattern
            from_to_match = re.search(r'from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+on|\s+tomorrow|\s+today|$)', user_lower)
            if from_to_match:
                parsed_data['from_city'] = from_to_match.group(1).strip().title()
                parsed_data['to_city'] = from_to_match.group(2).strip().title()
            
            # Look for date patterns
            if 'tomorrow' in user_lower:
                parsed_data['travel_date'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'today' in user_lower:
                parsed_data['travel_date'] = datetime.now().strftime('%Y-%m-%d')
            elif '31' in user_input or '31st' in user_lower:
                # Assume current month if just day is mentioned
                current_month = datetime.now().month
                current_year = datetime.now().year
                if current_month == 12:  # If December, go to next year
                    parsed_data['travel_date'] = f"{current_year + 1}-01-31"
                else:
                    next_month = current_month + 1
                    parsed_data['travel_date'] = f"{current_year}-{next_month:02d}-31"
            
            # Extract time preference
            if 'morning' in user_lower:
                parsed_data['time_preference'] = 'morning'
            elif 'afternoon' in user_lower:
                parsed_data['time_preference'] = 'afternoon'
            elif 'evening' in user_lower:
                parsed_data['time_preference'] = 'evening'
            
            # Extract passenger count
            passenger_match = re.search(r'(\d+)\s*(people|person|passenger)', user_lower)
            if passenger_match:
                parsed_data['passengers'] = int(passenger_match.group(1))
            
            print(f"✅ Parsed booking request: {parsed_data}")
            return parsed_data
            
        except Exception as e:
            print(f"❌ Parsing error: {e}")
            # Fallback with basic extraction
            user_lower = user_input.lower()
            
            # Try to extract any city names
            from_city = "Delhi"
            to_city = "Mumbai"
            
            # Simple city extraction
            cities = ["mathura", "delhi", "mumbai", "bangalore", "chennai", "kolkata", "hyderabad", 
                     "pune", "ahmedabad", "jaipur", "lucknow", "kanpur", "nagpur", "agra", "varanasi"]
            
            found_cities = []
            for city in cities:
                if city in user_lower:
                    found_cities.append(city.title())
            
            if len(found_cities) >= 2:
                from_city = found_cities[0]
                to_city = found_cities[1]
            elif len(found_cities) == 1:
                from_city = found_cities[0]
            
            return {
                'from_city': from_city,
                'to_city': to_city,
                'travel_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time_preference': 'any',
                'passengers': 1
            }
    
    def select_best_flight(self, flights, time_preference):
        """Select best flight based on time preference"""
        if not flights:
            return None
        
        # Convert time preference to hour ranges
        time_ranges = {
            'morning': (6, 12),
            'afternoon': (12, 18), 
            'evening': (18, 24),
            'any': (0, 24)
        }
        
        start_hour, end_hour = time_ranges.get(time_preference, (0, 24))
        
        # Filter flights by time preference
        suitable_flights = []
        for flight in flights:
            dep_time = flight[6]  # departure_time
            hour = int(dep_time.split(':')[0])
            if start_hour <= hour < end_hour:
                suitable_flights.append(flight)
        
        # If no flights in preferred time, use all flights
        if not suitable_flights:
            suitable_flights = flights
        
        # Select flight with most seats available (best option)
        best_flight = max(suitable_flights, key=lambda f: f[8])  # available_seats
        
        print(f"✅ Selected flight: {best_flight[1]} {best_flight[2]} at {best_flight[6]}")
        return best_flight

# Global flight booking agent
flight_agent = FlightBookingAgent()

@tool
def search_flights(from_city: str, to_city: str, travel_date: str, passengers: int = 1) -> str:
    """
    Search for available flights between cities
    
    Args:
        from_city: Departure city
        to_city: Destination city  
        travel_date: Travel date (YYYY-MM-DD format)
        passengers: Number of passengers (default 1)
    
    Returns:
        Formatted flight search results
    """
    try:
        print(f"🔍 Searching flights: {from_city} → {to_city} on {travel_date}")
        
        flights = flight_agent.db.search_flights(from_city, to_city, travel_date, passengers)
        
        if not flights:
            return f"❌ No flights found from {from_city} to {to_city} on {travel_date}"
        
        result = f"✈️ Available Flights: {from_city} → {to_city} on {travel_date}\n"
        result += "=" * 60 + "\n\n"
        
        for flight in flights:
            result += f"""🛫 {flight[2]} {flight[1]} - {flight[3]} → {flight[4]}
⏰ Departure: {flight[6]} | Arrival: {flight[7]}
💺 Available Seats: {flight[8]} | 💰 Price: ₹{flight[9]:,.0f}
✈️ Aircraft: {flight[10]}
{'─' * 50}
"""
        
        result += f"\n📊 Total {len(flights)} flights available"
        return result
        
    except Exception as e:
        error_msg = f"❌ Flight search failed: {str(e)}"
        print(error_msg)
        return error_msg
@tool
def book_flight_autonomous(user_request: str, passenger_name: str = "AI User") -> str:
    """
    Autonomously book a flight from natural language request
    
    Args:
        user_request: Natural language booking request
        passenger_name: Name of the passenger (default: AI User)
    
    Returns:
        Booking confirmation or error message
    """
    try:
        print(f"🤖 Autonomous flight booking: {user_request}")
        
        # Step 1: Parse the request using AI
        parsed_data = flight_agent.parse_booking_request(user_request)
        
        # Step 2: Search for flights
        flights = flight_agent.db.search_flights(
            parsed_data['from_city'],
            parsed_data['to_city'], 
            parsed_data['travel_date'],
            parsed_data['passengers']
        )
        
        if not flights:
            return f"❌ No flights available from {parsed_data['from_city']} to {parsed_data['to_city']} on {parsed_data['travel_date']}"
        
        # Step 3: Select best flight using AI
        selected_flight = flight_agent.select_best_flight(flights, parsed_data['time_preference'])
        
        if not selected_flight:
            return "❌ No suitable flights found for your preferences"
        
        # Step 4: Book the flight
        booking_id, message = flight_agent.db.book_flight(
            selected_flight[0],  # flight_id
            passenger_name,
            parsed_data['passengers']
        )
        
        if not booking_id:
            return f"❌ Booking failed: {message}"
        
        # Step 5: Generate confirmation message
        confirmation = f"""✅ FLIGHT BOOKED SUCCESSFULLY!

🎫 Booking Details:
• Booking ID: {booking_id}
• Passenger: {passenger_name}
• Flight: {selected_flight[2]} {selected_flight[1]}
• Route: {selected_flight[3]} → {selected_flight[4]}
• Date: {selected_flight[5]}
• Departure: {selected_flight[6]}
• Arrival: {selected_flight[7]}
• Seats: {parsed_data['passengers']}
• Total Price: ₹{selected_flight[9] * parsed_data['passengers']:,.0f}

🤖 AI Agent Actions Completed:
✓ Understood your request: "{user_request}"
✓ Parsed travel details automatically
✓ Searched {len(flights)} available flights
✓ Selected best flight based on preferences
✓ Completed booking autonomously
✓ Generated booking confirmation

📱 Your booking is confirmed and saved in the system!"""
        
        print(f"✅ Autonomous booking completed: {booking_id}")
        return confirmation
        
    except Exception as e:
        error_msg = f"❌ Autonomous booking failed: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def get_flight_bookings(passenger_name: str = "") -> str:
    """
    Get all flight bookings for a passenger
    
    Args:
        passenger_name: Name of passenger (optional, shows all if empty)
    
    Returns:
        Formatted booking history
    """
    try:
        conn = sqlite3.connect(flight_agent.db.db_path)
        cursor = conn.cursor()
        
        if passenger_name:
            cursor.execute('''
                SELECT * FROM bookings WHERE passenger_name LIKE ? ORDER BY booking_time DESC
            ''', (f"%{passenger_name}%",))
        else:
            cursor.execute('SELECT * FROM bookings ORDER BY booking_time DESC')
        
        bookings = cursor.fetchall()
        conn.close()
        
        if not bookings:
            return "📋 No flight bookings found"
        
        result = "🎫 Flight Booking History\n" + "=" * 50 + "\n\n"
        
        for booking in bookings:
            result += f"""📋 Booking ID: {booking[1]}
👤 Passenger: {booking[2]}
✈️ Route: {booking[4]} → {booking[5]}
📅 Travel Date: {booking[6]}
⏰ Departure: {booking[7]}
💺 Seats: {booking[8]}
💰 Total: ₹{booking[9]:,.0f}
📊 Status: {booking[10].upper()}
🕒 Booked: {booking[11]}
{'─' * 40}
"""
        
        result += f"\n📊 Total {len(bookings)} bookings found"
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get bookings: {str(e)}"
        print(error_msg)
        return error_msg

# Simple functions for direct use
def book_flight_simple(user_request, passenger_name="AI User"):
    """Simple flight booking function"""
    return book_flight_autonomous.func(user_request, passenger_name)

def search_flights_simple(from_city, to_city, travel_date, passengers=1):
    """Simple flight search function"""
    return search_flights.func(from_city, to_city, travel_date, passengers)

def get_bookings_simple(passenger_name=""):
    """Simple booking history function"""
    return get_flight_bookings.func(passenger_name)

# Test function
def test_flight_agent():
    """Test the flight booking agent"""
    print("🧪 Testing Flight Booking Agent...")
    print("=" * 50)
    
    # Test flight search
    print("\n1. Testing flight search...")
    search_result = search_flights_simple("Delhi", "Mumbai", "2026-02-01")
    print(search_result)
    
    # Test autonomous booking
    print("\n2. Testing autonomous booking...")
    booking_result = book_flight_simple("Book a flight from Delhi to Mumbai tomorrow morning", "Test User")
    print(booking_result)
    
    # Test booking history
    print("\n3. Testing booking history...")
    history_result = get_bookings_simple()
    print(history_result)
    
    print("\n🎉 Flight agent testing completed!")

if __name__ == "__main__":
    test_flight_agent()