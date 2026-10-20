"""
LLM Task Parser using LangChain + Ollama
Converts natural language to structured task data
"""
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import json
import re
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OLLAMA_MODEL, OLLAMA_BASE_URL

class TaskParser:
    def __init__(self):
        """Initialize the LLM task parser"""
        self.llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL
        )
        
        self.prompt = PromptTemplate(
            input_variables=["input"],
            template="""You are an AI task parser that converts natural language to structured JSON.

SUPPORTED TASKS:
- email: Send email (requires: to, subject, body)
- call: Make phone call (requires: to)  
- whatsapp: Send WhatsApp message (requires: to, message)
- flight: Book flight (requires: from_city, to_city, travel_date, passengers)
- music: Play mood-based music (requires: user_mood_input)
- mcq: MCQ Intelligence Platform (requires: operation, topic, difficulty)

RULES:
1. Return ONLY valid JSON, no other text
2. Use these exact field names: task, to, subject, body, message, from_city, to_city, travel_date, passengers, user_mood_input, operation, topic, difficulty, count, platform_name
3. If phone number has no country code, add +91
4. Extract the ACTUAL message content the user wants to send, not generic text
5. For emails, create a meaningful subject based on the message content
6. For flights, extract cities and dates from natural language
7. For music, capture the full emotional context and mood description
8. For MCQ tasks, identify the operation (generate, create_exam, analyze, scan, stats) and extract topic/difficulty
9. Preserve the user's intended message exactly as they want it sent

USER INPUT: {input}

EXAMPLES:
"send email to john@gmail.com saying hello how are you" 
→ {{"task": "email", "to": "john@gmail.com", "subject": "Hello", "body": "hello how are you"}}

"whatsapp to 7318018232 that meeting is tomorrow at 3pm"
→ {{"task": "whatsapp", "to": "+917318018232", "message": "meeting is tomorrow at 3pm"}}

"book flight from Delhi to Mumbai tomorrow"
→ {{"task": "flight", "from_city": "Delhi", "to_city": "Mumbai", "travel_date": "tomorrow", "passengers": 1}}

"I'm feeling really happy today, play some music"
→ {{"task": "music", "user_mood_input": "I'm feeling really happy today, play some music"}}

"play something sad, I'm heartbroken"
→ {{"task": "music", "user_mood_input": "play something sad, I'm heartbroken"}}

"generate MCQ questions on Python programming"
→ {{"task": "mcq", "operation": "generate", "topic": "Python Programming", "difficulty": "medium", "count": 5}}

"create exam session for machine learning with 10 questions"
→ {{"task": "mcq", "operation": "create_exam", "topic": "Machine Learning", "difficulty": "medium", "num_questions": 10}}

"analyze MCQ question number 5"
→ {{"task": "mcq", "operation": "analyze", "question_id": 5}}

"scan CodeChef platform for data structures questions"
→ {{"task": "mcq", "operation": "scan", "platform_name": "CodeChef", "topic": "Data Structures"}}

"show MCQ platform statistics"
→ {{"task": "mcq", "operation": "stats"}}

"call +917318018232"
→ {{"task": "call", "to": "+917318018232"}}

JSON Response:"""
        )

    def parse_task(self, user_input: str) -> Dict[str, Any]:
        """Parse user input into structured task data"""
        try:
            print(f"🧠 Parsing: '{user_input}'")
            
            # Get LLM response
            response = self.llm.invoke(self.prompt.format(input=user_input))
            print(f"🤖 LLM Response: {response[:200]}...")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                
                # Validate and clean the data
                parsed_data = self._validate_and_clean(parsed_data)
                print(f"✅ Parsed: {parsed_data}")
                return parsed_data
            else:
                print("❌ No JSON found in response, using fallback")
                return self._fallback_parse(user_input)
                
        except Exception as e:
            print(f"❌ LLM parsing error: {e}")
            return self._fallback_parse(user_input)

    def _validate_and_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean parsed data"""
        # Ensure required fields exist
        if 'task' not in data:
            data['task'] = 'unknown'
        
        # Clean phone numbers
        if 'to' in data and data['to']:
            phone = data['to']
            if phone.isdigit() and len(phone) == 10:
                data['to'] = f"+91{phone}"
        
        # Add default subject for emails
        if data.get('task') == 'email' and not data.get('subject'):
            data['subject'] = 'Message from AI Assistant'
        
        return data

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Enhanced fallback parsing when LLM fails"""
        import re  # Import re module here
        text = text.lower().strip()
        original_text = text  # Keep original for message extraction
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Extract phone numbers
        phone_patterns = [r'\+\d{10,15}', r'\d{10}']
        phone = None
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group()
                if not phone.startswith('+'):
                    phone = '+91' + phone
                break
        
        # Check for flight booking keywords
        flight_keywords = ['flight', 'book flight', 'fly', 'travel', 'trip']
        city_keywords = ['delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata', 'hyderabad']
        
        # Enhanced message extraction - look for actual content after keywords
        message = ""
        message_indicators = ['saying', 'that', 'message', 'tell', 'about', 'regarding']
        
        for indicator in message_indicators:
            if indicator in text:
                parts = text.split(indicator, 1)
                if len(parts) > 1:
                    message = parts[1].strip()
                    # Clean up the message
                    message = message.replace('him', '').replace('her', '').strip()
                    break
        
        # If no message found with indicators, try to extract from context
        if not message:
            # Remove command words and extract remaining content
            command_words = ['send', 'email', 'whatsapp', 'call', 'to', 'phone', 'message', 'book', 'flight']
            words = text.split()
            filtered_words = []
            skip_next = False
            
            for i, word in enumerate(words):
                if skip_next:
                    skip_next = False
                    continue
                    
                if word in command_words:
                    continue
                elif '@' in word or word.startswith('+') or word.isdigit():
                    continue
                else:
                    filtered_words.append(word)
            
            if filtered_words:
                message = ' '.join(filtered_words)
        
        # Generate subject for emails based on message content
        def generate_subject(msg):
            if not msg:
                return "Message from AI Assistant"
            
            # Extract key words for subject
            words = msg.split()[:4]  # First 4 words
            subject = ' '.join(words).title()
            
            # Add context-based subjects
            if 'meeting' in msg.lower():
                return "Meeting Update"
            elif 'project' in msg.lower():
                return "Project Update"
            elif 'urgent' in msg.lower():
                return "Urgent Message"
            elif 'hello' in msg.lower() or 'hi' in msg.lower():
                return "Hello"
            else:
                return subject if subject else "Message from AI Assistant"
        
        # Check for flight booking first
        if any(keyword in text for keyword in flight_keywords):
            # Extract cities and travel details
            from_city = "Delhi"  # Default
            to_city = "Mumbai"   # Default
            
            # Look for city patterns
            for city in city_keywords:
                if city in text:
                    if 'from' in text and text.find('from') < text.find(city):
                        from_city = city.title()
                    elif 'to' in text and text.find('to') < text.find(city):
                        to_city = city.title()
            
            # Extract date information
            travel_date = ""
            if 'tomorrow' in text:
                from datetime import datetime, timedelta
                travel_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'today' in text:
                from datetime import datetime
                travel_date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract passenger count
            passengers = 1
            import re
            passenger_match = re.search(r'(\d+)\s*(people|person|passenger)', text)
            if passenger_match:
                passengers = int(passenger_match.group(1))
            
            return {
                'task': 'flight',
                'from_city': from_city,
                'to_city': to_city,
                'travel_date': travel_date,
                'passengers': passengers,
                'original_input': original_text
            }
        
        # Check for MCQ requests
        mcq_keywords = ['mcq', 'question', 'quiz', 'exam', 'test', 'assessment', 'generate questions', 'create exam']
        if any(keyword in text for keyword in mcq_keywords):
            # Determine MCQ operation
            operation = "generate"  # default
            topic = "General Knowledge"  # default
            difficulty = "medium"  # default
            
            if 'generate' in text or 'create questions' in text:
                operation = "generate"
            elif 'exam' in text or 'quiz' in text or 'test' in text:
                operation = "create_exam"
            elif 'analyze' in text:
                operation = "analyze"
            elif 'scan' in text:
                operation = "scan"
            elif 'statistics' in text or 'stats' in text:
                operation = "stats"
            
            # Extract topic
            programming_topics = ['python', 'java', 'javascript', 'c++', 'programming']
            cs_topics = ['machine learning', 'ml', 'data structure', 'algorithm', 'database', 'networking']
            
            for prog_topic in programming_topics:
                if prog_topic in text:
                    topic = f"{prog_topic.title()} Programming"
                    break
            
            for cs_topic in cs_topics:
                if cs_topic in text:
                    topic = cs_topic.title()
                    break
            
            # Extract difficulty
            if 'easy' in text or 'basic' in text:
                difficulty = "easy"
            elif 'hard' in text or 'difficult' in text or 'advanced' in text:
                difficulty = "hard"
            
            # Extract count for generation
            count_match = re.search(r'(\d+)\s*questions?', text)
            count = int(count_match.group(1)) if count_match else 5
            
            mcq_data = {
                'task': 'mcq',
                'operation': operation,
                'topic': topic,
                'difficulty': difficulty
            }
            
            if operation == "generate":
                mcq_data['count'] = count
            elif operation == "create_exam":
                mcq_data['num_questions'] = count
                mcq_data['user_name'] = "Anonymous"
            elif operation == "analyze":
                # Try to extract question ID
                id_match = re.search(r'question\s*(?:number\s*)?(\d+)', text)
                mcq_data['question_id'] = int(id_match.group(1)) if id_match else 1
            elif operation == "scan":
                # Try to extract platform name
                platforms = ['codechef', 'hackerrank', 'leetcode', 'geeksforgeeks', 'codeforces']
                platform_name = "External Platform"
                for platform in platforms:
                    if platform in text.lower():
                        platform_name = platform.title()
                        break
                mcq_data['platform_name'] = platform_name
            
            return mcq_data
        
        # Check for music requests
        music_keywords = ['music', 'song', 'play', 'playlist', 'feeling', 'mood', 'happy', 'sad', 'stressed', 'relaxed', 'angry', 'motivated', 'romantic']
        if any(keyword in text for keyword in music_keywords):
            # Check if it's clearly a music request (not MCQ related)
            music_indicators = ['play music', 'play song', 'feeling', 'mood', 'stressed', 'happy', 'sad', 'angry', 'playlist']
            mcq_indicators = ['mcq', 'question', 'quiz', 'exam', 'test', 'generate']
            
            # If it has MCQ indicators, don't treat as music
            if not any(indicator in text for indicator in mcq_indicators):
                if any(indicator in text for indicator in music_indicators):
                    return {
                        'task': 'music',
                        'user_mood_input': original_text
                    }
        
        # Determine task type - prioritize call detection
        call_keywords = ['call', 'phone', 'ring', 'dial']
        email_keywords = ['email', 'mail']
        whatsapp_keywords = ['whatsapp', 'message', 'text']
        
        if any(keyword in text for keyword in call_keywords):
            return {
                'task': 'call',
                'to': phone if phone else '',
                'message': message or 'Hello from your AI assistant!'
            }
        elif emails or any(keyword in text for keyword in email_keywords):
            return {
                'task': 'email',
                'to': emails[0] if emails else '',
                'subject': generate_subject(message),
                'body': message or 'Hello from your AI assistant!'
            }
        elif phone or any(keyword in text for keyword in whatsapp_keywords):
            return {
                'task': 'whatsapp',
                'to': phone or '',
                'message': message or 'Hello from your AI assistant!'
            }
        else:
            return {
                'task': 'unknown',
                'input': text
            }

# Global parser instance
parser = TaskParser()

def parse_task(user_input: str) -> Dict[str, Any]:
    """Main function to parse user input"""
    return parser.parse_task(user_input)