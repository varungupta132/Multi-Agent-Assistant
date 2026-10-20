"""
Mood-Aware Music Agent - Multi-Agent System using LangChain + LangGraph + Ollama
Analyzes user mood from natural language and creates personalized playlists
"""
from langchain_core.tools import tool
from datetime import datetime
import json
import sqlite3
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH
from llm.message_generator import MessageGenerator

class MusicDatabase:
    """Database manager for music library and playlists"""
    
    def __init__(self, db_path="music.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize music database with songs and playlists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS songs")
        cursor.execute("DROP TABLE IF EXISTS playlists")
        cursor.execute("DROP TABLE IF EXISTS playlist_songs")
        cursor.execute("DROP TABLE IF EXISTS mood_sessions")
        
        # Create songs table
        cursor.execute('''
            CREATE TABLE songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                genre TEXT NOT NULL,
                mood_tags TEXT NOT NULL,
                energy_level INTEGER DEFAULT 5,
                tempo TEXT DEFAULT 'medium',
                duration INTEGER DEFAULT 180,
                file_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create playlists table
        cursor.execute('''
            CREATE TABLE playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mood TEXT NOT NULL,
                user_input TEXT,
                total_duration INTEGER DEFAULT 0,
                song_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create playlist_songs junction table
        cursor.execute('''
            CREATE TABLE playlist_songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER,
                song_id INTEGER,
                position INTEGER,
                FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                FOREIGN KEY (song_id) REFERENCES songs (id)
            )
        ''')
        
        # Create mood sessions table
        cursor.execute('''
            CREATE TABLE mood_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                detected_mood TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                playlist_id INTEGER,
                session_time TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (playlist_id) REFERENCES playlists (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Music database initialized: {self.db_path}")
        
        # Add sample music library
        self._add_sample_music()
    
    def _add_sample_music(self):
        """Add sample music library with various moods"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sample songs with mood tags
        sample_songs = [
            # Happy/Upbeat Songs
            ("Happy", "Pharrell Williams", "Pop", "happy,upbeat,energetic", 9, "fast", 232),
            ("Good as Hell", "Lizzo", "Pop", "happy,confident,empowering", 8, "medium", 219),
            ("Can't Stop the Feeling", "Justin Timberlake", "Pop", "happy,dance,upbeat", 9, "fast", 236),
            ("Walking on Sunshine", "Katrina and the Waves", "Pop", "happy,energetic,positive", 8, "fast", 239),
            ("I Gotta Feeling", "Black Eyed Peas", "Pop", "happy,party,celebration", 9, "fast", 285),
            
            # Sad/Melancholic Songs
            ("Someone Like You", "Adele", "Ballad", "sad,heartbreak,emotional", 3, "slow", 285),
            ("Mad World", "Gary Jules", "Alternative", "sad,melancholic,introspective", 2, "slow", 192),
            ("Hurt", "Johnny Cash", "Country", "sad,pain,reflective", 2, "slow", 218),
            ("Black", "Pearl Jam", "Grunge", "sad,loss,emotional", 3, "slow", 343),
            ("Tears in Heaven", "Eric Clapton", "Rock", "sad,grief,healing", 3, "slow", 282),
            
            # Relaxed/Chill Songs
            ("Weightless", "Marconi Union", "Ambient", "relaxed,calm,peaceful", 2, "slow", 485),
            ("River", "Joni Mitchell", "Folk", "relaxed,contemplative,serene", 4, "slow", 240),
            ("Mad About You", "Sting", "Jazz", "relaxed,romantic,smooth", 5, "medium", 231),
            ("Breathe Me", "Sia", "Alternative", "relaxed,introspective,gentle", 4, "slow", 268),
            ("Holocene", "Bon Iver", "Indie", "relaxed,nature,peaceful", 3, "slow", 337),
            
            # Angry/Intense Songs
            ("Break Stuff", "Limp Bizkit", "Nu Metal", "angry,aggressive,intense", 10, "fast", 167),
            ("Bodies", "Drowning Pool", "Metal", "angry,rage,powerful", 10, "fast", 203),
            ("Killing in the Name", "Rage Against the Machine", "Rock", "angry,rebellion,intense", 9, "fast", 314),
            ("Chop Suey!", "System of a Down", "Metal", "angry,chaotic,intense", 10, "fast", 210),
            ("B.Y.O.B.", "System of a Down", "Metal", "angry,political,aggressive", 9, "fast", 254),
            
            # Motivated/Workout Songs
            ("Eye of the Tiger", "Survivor", "Rock", "motivated,workout,determination", 9, "fast", 245),
            ("Stronger", "Kanye West", "Hip Hop", "motivated,empowering,confident", 8, "medium", 312),
            ("Till I Collapse", "Eminem", "Hip Hop", "motivated,workout,intense", 9, "fast", 297),
            ("Thunder", "Imagine Dragons", "Pop Rock", "motivated,powerful,energetic", 8, "fast", 187),
            ("Believer", "Imagine Dragons", "Pop Rock", "motivated,overcoming,strong", 8, "fast", 204),
            
            # Romantic Songs
            ("Perfect", "Ed Sheeran", "Pop", "romantic,love,tender", 6, "medium", 263),
            ("All of Me", "John Legend", "R&B", "romantic,devotion,intimate", 5, "slow", 269),
            ("Thinking Out Loud", "Ed Sheeran", "Pop", "romantic,sweet,gentle", 5, "slow", 281),
            ("Make You Feel My Love", "Bob Dylan", "Folk", "romantic,deep,emotional", 4, "slow", 212),
            ("At Last", "Etta James", "Jazz", "romantic,classic,soulful", 5, "medium", 180),
            
            # Stressed/Anxious Relief
            ("Clair de Lune", "Claude Debussy", "Classical", "calm,peaceful,soothing", 2, "slow", 300),
            ("Gymnopédie No. 1", "Erik Satie", "Classical", "calm,meditative,gentle", 2, "slow", 210),
            ("Aqueous Transmission", "Incubus", "Alternative", "calm,flowing,peaceful", 3, "slow", 438),
            ("Porcelain", "Moby", "Electronic", "calm,ethereal,soothing", 3, "slow", 240),
            ("Svefn-g-englar", "Sigur Rós", "Post Rock", "calm,atmospheric,healing", 3, "slow", 600),
        ]
        
        cursor.executemany('''
            INSERT INTO songs (title, artist, genre, mood_tags, energy_level, tempo, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_songs)
        
        conn.commit()
        conn.close()
        print(f"✅ Added {len(sample_songs)} songs to music library")
    
    def get_songs_by_mood(self, mood, limit=10):
        """Get songs that match a specific mood"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search for songs with matching mood tags
        cursor.execute('''
            SELECT * FROM songs 
            WHERE mood_tags LIKE ? 
            ORDER BY energy_level DESC, RANDOM()
            LIMIT ?
        ''', (f"%{mood}%", limit))
        
        songs = cursor.fetchall()
        conn.close()
        
        return songs
    
    def create_playlist(self, name, mood, user_input, song_ids):
        """Create a new playlist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate total duration
        if song_ids:
            placeholders = ','.join(['?' for _ in song_ids])
            cursor.execute(f'SELECT SUM(duration) FROM songs WHERE id IN ({placeholders})', song_ids)
            total_duration = cursor.fetchone()[0] or 0
        else:
            total_duration = 0
        
        # Create playlist
        cursor.execute('''
            INSERT INTO playlists (name, mood, user_input, total_duration, song_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, mood, user_input, total_duration, len(song_ids)))
        
        playlist_id = cursor.lastrowid
        
        # Add songs to playlist
        for position, song_id in enumerate(song_ids, 1):
            cursor.execute('''
                INSERT INTO playlist_songs (playlist_id, song_id, position)
                VALUES (?, ?, ?)
            ''', (playlist_id, song_id, position))
        
        conn.commit()
        conn.close()
        
        return playlist_id
class MoodAnalyzer:
    """AI-powered mood detection from natural language"""
    
    def __init__(self):
        self.message_generator = MessageGenerator()
    
    def detect_mood(self, user_input):
        """Analyze user input to detect emotional mood"""
        try:
            print(f"🧠 Analyzing mood from: {user_input[:50]}...")
            
            mood_prompt = f"""
            Analyze the emotional mood from this user input: "{user_input}"
            
            Detect the primary emotion and mood state. Consider:
            - Explicit emotional words (happy, sad, angry, etc.)
            - Implicit emotional context (tired, energetic, stressed, etc.)
            - Activity context (workout, relaxing, studying, etc.)
            - Tone and sentiment
            
            Available mood categories:
            - happy: joyful, excited, cheerful, celebrating
            - sad: depressed, heartbroken, melancholic, down
            - relaxed: calm, peaceful, chill, meditative
            - angry: frustrated, mad, aggressive, annoyed
            - motivated: energetic, determined, workout, pumped
            - romantic: loving, intimate, date night, romantic
            - stressed: anxious, overwhelmed, tense, worried
            
            Respond ONLY in this format:
            MOOD: [mood_name]
            CONFIDENCE: [0.0-1.0]
            REASON: [brief explanation]
            
            Examples:
            Input: "I'm feeling great today, everything is going well!"
            MOOD: happy
            CONFIDENCE: 0.9
            REASON: Explicit positive emotions and optimistic tone
            
            Input: "I'm so tired and stressed from work"
            MOOD: stressed
            CONFIDENCE: 0.8
            REASON: Mentions tiredness and stress from work pressure
            
            Input: "Just broke up with my girlfriend, feeling terrible"
            MOOD: sad
            CONFIDENCE: 0.95
            REASON: Explicit mention of breakup and negative feelings
            
            Input: "Going to the gym, need something to pump me up"
            MOOD: motivated
            CONFIDENCE: 0.85
            REASON: Workout context and request for energizing music
            
            Your analysis:
            """
            
            response = self.message_generator.llm.invoke(mood_prompt)
            
            # Parse AI response
            mood_data = {
                'mood': 'happy',
                'confidence': 0.5,
                'reason': 'Default mood'
            }
            
            lines = response.strip().split('\n')
            for line in lines:
                if 'MOOD:' in line:
                    mood = line.split('MOOD:')[-1].strip().lower()
                    if mood in ['happy', 'sad', 'relaxed', 'angry', 'motivated', 'romantic', 'stressed']:
                        mood_data['mood'] = mood
                elif 'CONFIDENCE:' in line:
                    try:
                        confidence = float(line.split('CONFIDENCE:')[-1].strip())
                        mood_data['confidence'] = max(0.0, min(1.0, confidence))
                    except:
                        pass
                elif 'REASON:' in line:
                    reason = line.split('REASON:')[-1].strip()
                    if reason:
                        mood_data['reason'] = reason
            
            # Fallback mood detection using keywords
            user_lower = user_input.lower()
            
            mood_keywords = {
                'happy': ['happy', 'great', 'awesome', 'fantastic', 'wonderful', 'excited', 'joy', 'cheerful', 'good day'],
                'sad': ['sad', 'depressed', 'down', 'heartbroken', 'terrible', 'awful', 'crying', 'upset', 'broke up'],
                'relaxed': ['relaxed', 'calm', 'chill', 'peaceful', 'meditate', 'zen', 'quiet', 'rest', 'unwind'],
                'angry': ['angry', 'mad', 'frustrated', 'pissed', 'furious', 'rage', 'annoyed', 'irritated'],
                'motivated': ['motivated', 'workout', 'gym', 'exercise', 'pumped', 'energetic', 'determined', 'focused'],
                'romantic': ['romantic', 'love', 'date', 'valentine', 'intimate', 'partner', 'relationship', 'crush'],
                'stressed': ['stressed', 'anxious', 'overwhelmed', 'pressure', 'worried', 'tense', 'busy', 'deadline']
            }
            
            # Check for keyword matches if confidence is low
            if mood_data['confidence'] < 0.7:
                for mood, keywords in mood_keywords.items():
                    for keyword in keywords:
                        if keyword in user_lower:
                            mood_data['mood'] = mood
                            mood_data['confidence'] = 0.8
                            mood_data['reason'] = f"Detected keyword: {keyword}"
                            break
                    if mood_data['confidence'] >= 0.7:
                        break
            
            print(f"✅ Detected mood: {mood_data['mood']} (confidence: {mood_data['confidence']:.2f})")
            return mood_data
            
        except Exception as e:
            print(f"❌ Mood detection error: {e}")
            return {
                'mood': 'happy',
                'confidence': 0.5,
                'reason': 'Fallback to default mood'
            }

class PlaylistGenerator:
    """Generates playlists based on detected mood"""
    
    def __init__(self, db):
        self.db = db
    
    def create_mood_playlist(self, mood, user_input, song_count=8):
        """Create a playlist based on detected mood"""
        try:
            print(f"🎵 Creating playlist for mood: {mood}")
            
            # Get songs matching the mood
            songs = self.db.get_songs_by_mood(mood, song_count * 2)  # Get more to have variety
            
            if not songs:
                # Fallback: get any songs and pretend they match
                print(f"⚠️ No songs found for {mood}, using fallback songs")
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM songs ORDER BY RANDOM() LIMIT ?', (song_count,))
                songs = cursor.fetchall()
                conn.close()
            
            # Select best songs for the mood
            selected_songs = self._select_best_songs(songs, mood, song_count)
            
            # Generate playlist name
            playlist_name = self._generate_playlist_name(mood)
            
            # Create playlist in database
            song_ids = [song[0] for song in selected_songs]  # song[0] is the ID
            playlist_id = self.db.create_playlist(playlist_name, mood, user_input, song_ids)
            
            # Calculate total duration
            total_duration = sum(song[7] for song in selected_songs)  # song[7] is duration
            
            playlist_info = {
                'id': playlist_id,
                'name': playlist_name,
                'mood': mood,
                'songs': selected_songs,
                'total_duration': total_duration,
                'song_count': len(selected_songs)
            }
            
            print(f"✅ Created playlist: {playlist_name} ({len(selected_songs)} songs)")
            return playlist_info
            
        except Exception as e:
            print(f"❌ Playlist creation error: {e}")
            return None
    
    def _select_best_songs(self, songs, mood, count):
        """Select the best songs for the mood"""
        if len(songs) <= count:
            return songs
        
        # Sort by relevance to mood and energy level
        mood_energy_map = {
            'happy': (7, 10),      # High energy
            'motivated': (8, 10),  # Very high energy
            'angry': (8, 10),      # High energy
            'romantic': (3, 6),    # Medium energy
            'relaxed': (1, 4),     # Low energy
            'sad': (1, 4),         # Low energy
            'stressed': (1, 3)     # Very low energy
        }
        
        min_energy, max_energy = mood_energy_map.get(mood, (4, 7))
        
        # Filter songs by energy level and select best ones
        suitable_songs = [song for song in songs if min_energy <= song[5] <= max_energy]
        
        if len(suitable_songs) < count:
            suitable_songs = songs  # Use all if not enough suitable ones
        
        # Return top songs (already randomized in query)
        return suitable_songs[:count]
    
    def _generate_playlist_name(self, mood):
        """Generate a creative playlist name based on mood"""
        mood_names = {
            'happy': [
                "Happy Vibes 🎉", "Sunshine Playlist ☀️", "Good Mood Mix 😊", 
                "Positive Energy 🌟", "Feel Good Hits 🎵", "Joyful Jams 🎶"
            ],
            'sad': [
                "Melancholy Moments 💙", "Rainy Day Blues 🌧️", "Emotional Journey 💔", 
                "Healing Sounds 🌙", "Quiet Reflections 🕯️", "Gentle Sadness 🍃"
            ],
            'relaxed': [
                "Chill Vibes 🌊", "Peaceful Moments 🧘", "Calm & Collected 🍃", 
                "Zen Zone 🕯️", "Tranquil Tunes 🌸", "Serenity Sounds 🌙"
            ],
            'angry': [
                "Rage Mode 🔥", "Intense Energy ⚡", "Aggressive Beats 💥", 
                "Fury Playlist 😤", "Raw Power 🎸", "Unleashed 🌪️"
            ],
            'motivated': [
                "Workout Warriors 💪", "Motivation Station 🚀", "Power Up Playlist ⚡", 
                "Beast Mode 🦁", "Unstoppable 🔥", "Champion Mindset 🏆"
            ],
            'romantic': [
                "Love Songs 💕", "Romantic Evening 🌹", "Date Night Vibes 💖", 
                "Heart & Soul 💝", "Intimate Moments 🕯️", "Love Story 💑"
            ],
            'stressed': [
                "Stress Relief 🌿", "Anxiety Ease 🌊", "Calming Therapy 🧘", 
                "Peace & Quiet 🕊️", "Mindful Moments 🌸", "Breathe Easy 💨"
            ]
        }
        
        names = mood_names.get(mood, ["Custom Playlist 🎵"])
        return random.choice(names)

class MusicPlayer:
    """Enhanced music player with realistic features"""
    
    def __init__(self):
        self.current_playlist = None
        self.current_song_index = 0
        self.is_playing = False
        self.is_paused = False
        self.volume = 75
        self.repeat_mode = "off"  # off, one, all
        self.shuffle_mode = False
        self.current_position = 0  # seconds into current song
        self.equalizer = {
            'bass': 0,
            'mid': 0,
            'treble': 0
        }
    
    def play_playlist(self, playlist_info):
        """Start playing a playlist with enhanced features"""
        try:
            self.current_playlist = playlist_info
            self.current_song_index = 0
            self.is_playing = True
            self.is_paused = False
            self.current_position = 0
            
            current_song = playlist_info['songs'][0]
            
            # Generate enhanced play message with player interface
            play_message = f"""🎵 MUSIC PLAYER ACTIVATED 🎵

┌─────────────────────────────────────────┐
│  🎧 {playlist_info['name']:<35} │
├─────────────────────────────────────────┤
│  ▶️  NOW PLAYING                        │
│  🎵 {current_song[1]:<35} │
│  👤 {current_song[2]:<35} │
│  🎼 {current_song[3]:<35} │
├─────────────────────────────────────────┤
│  ⏱️  {self._format_duration(current_song[7]):<8} 📊 Energy: {current_song[5]}/10     │
│  🔊 Volume: {self.volume}%   🔀 Shuffle: {'ON' if self.shuffle_mode else 'OFF'}    │
│  🔁 Repeat: {self.repeat_mode.upper():<8} 🎚️ EQ: Balanced    │
└─────────────────────────────────────────┘

🎶 PLAYER CONTROLS AVAILABLE:
• ⏯️  Play/Pause • ⏭️ Next • ⏮️ Previous
• 🔊 Volume • 🔀 Shuffle • 🔁 Repeat
• 📊 Status • ⏹️ Stop

🎵 Music streaming started! Enjoy your personalized playlist! 🎵"""
            
            print(f"🎵 Enhanced player started: {playlist_info['name']}")
            return play_message
            
        except Exception as e:
            print(f"❌ Playback error: {e}")
            return "❌ Failed to start music playback"
    
    def _format_duration(self, seconds):
        """Format duration in seconds to MM:SS"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def get_player_status(self):
        """Get detailed current player status"""
        if not self.current_playlist:
            return """🔇 MUSIC PLAYER STATUS 🔇

┌─────────────────────────────────────────┐
│  📱 PLAYER: IDLE                        │
│  🎵 No playlist loaded                  │
│  💡 Tip: Tell me your mood to start!    │
└─────────────────────────────────────────┘"""
        
        current_song = self.current_playlist['songs'][self.current_song_index]
        status_icon = "▶️" if self.is_playing else "⏸️" if self.is_paused else "⏹️"
        
        # Calculate progress bar
        progress_percent = (self.current_position / current_song[7]) * 100 if current_song[7] > 0 else 0
        progress_bar = "█" * int(progress_percent / 5) + "░" * (20 - int(progress_percent / 5))
        
        return f"""🎵 MUSIC PLAYER STATUS 🎵

┌─────────────────────────────────────────┐
│  {status_icon} {current_song[1]:<35} │
│  👤 {current_song[2]:<35} │
├─────────────────────────────────────────┤
│  {progress_bar} │
│  {self._format_duration(self.current_position)} / {self._format_duration(current_song[7])} ({progress_percent:.0f}%)                │
├─────────────────────────────────────────┤
│  📀 Playlist: {self.current_playlist['name']:<25} │
│  🎵 Track: {self.current_song_index + 1}/{len(self.current_playlist['songs']):<25} │
│  🔊 Volume: {self.volume}%   🔀 Shuffle: {'ON' if self.shuffle_mode else 'OFF'}    │
│  🔁 Repeat: {self.repeat_mode.upper():<8} 📊 Energy: {current_song[5]}/10     │
└─────────────────────────────────────────┘

🎮 Available Controls: play, pause, stop, next, previous, volume, shuffle, repeat"""
    
    def set_volume(self, volume):
        """Set player volume (0-100)"""
        try:
            volume = max(0, min(100, int(volume)))
            self.volume = volume
            return f"🔊 Volume set to {volume}%"
        except:
            return "❌ Invalid volume level (use 0-100)"
    
    def toggle_shuffle(self):
        """Toggle shuffle mode"""
        self.shuffle_mode = not self.shuffle_mode
        return f"🔀 Shuffle {'enabled' if self.shuffle_mode else 'disabled'}"
    
    def set_repeat_mode(self, mode):
        """Set repeat mode: off, one, all"""
        valid_modes = ['off', 'one', 'all']
        if mode.lower() in valid_modes:
            self.repeat_mode = mode.lower()
            return f"🔁 Repeat mode: {mode.upper()}"
        else:
            return f"❌ Invalid repeat mode. Use: {', '.join(valid_modes)}"
    
    def seek_to_position(self, position):
        """Seek to specific position in current song"""
        if not self.current_playlist:
            return "🔇 No music playing"
        
        current_song = self.current_playlist['songs'][self.current_song_index]
        position = max(0, min(current_song[7], int(position)))
        self.current_position = position
        
        return f"⏩ Seeked to {self._format_duration(position)}"

# Global instances
music_db = MusicDatabase()
mood_analyzer = MoodAnalyzer()
playlist_generator = PlaylistGenerator(music_db)
music_player = MusicPlayer()

@tool
def analyze_mood_and_play_music(user_input: str) -> str:
    """
    Analyze user mood from natural language and automatically create & play music
    
    Args:
        user_input: Natural language describing mood or music request
    
    Returns:
        Complete music experience with mood analysis and playlist
    """
    try:
        print(f"🎵 Processing music request: {user_input}")
        
        # Step 1: Detect mood from user input
        mood_data = mood_analyzer.detect_mood(user_input)
        
        # Step 2: Create playlist based on mood
        playlist_info = playlist_generator.create_mood_playlist(
            mood_data['mood'], 
            user_input
        )
        
        if not playlist_info:
            return "❌ Failed to create playlist. Please try again."
        
        # Step 3: Start playing music
        playback_message = music_player.play_playlist(playlist_info)
        
        # Step 4: Log the session
        conn = sqlite3.connect(music_db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO mood_sessions (user_input, detected_mood, confidence, playlist_id)
            VALUES (?, ?, ?, ?)
        ''', (user_input, mood_data['mood'], mood_data['confidence'], playlist_info['id']))
        conn.commit()
        conn.close()
        
        # Step 5: Generate complete response
        response = f"""🎭 MOOD ANALYSIS COMPLETE 🎭

🧠 Your Input: "{user_input}"
😊 Detected Mood: {mood_data['mood'].title()} (Confidence: {mood_data['confidence']:.0%})
💭 Analysis: {mood_data['reason']}

{playback_message}

📋 PLAYLIST DETAILS:
• Total Songs: {playlist_info['song_count']}
• Total Duration: {playlist_info['total_duration'] // 60} minutes
• Mood Category: {mood_data['mood'].title()}

🎼 TRACKLIST:
"""
        
        # Add song list
        for i, song in enumerate(playlist_info['songs'][:5], 1):  # Show first 5 songs
            response += f"{i}. {song[1]} - {song[2]} ({song[3]})\n"
        
        if len(playlist_info['songs']) > 5:
            response += f"... and {len(playlist_info['songs']) - 5} more songs\n"
        
        response += f"\n🤖 AI Music Agent: Your personalized {mood_data['mood']} playlist is ready! 🎵"
        
        print(f"✅ Music experience completed for mood: {mood_data['mood']}")
        return response
        
    except Exception as e:
        error_msg = f"❌ Music agent error: {str(e)}"
        print(error_msg)
        return error_msg
@tool
def get_music_library() -> str:
    """
    Get overview of available music library and mood categories
    
    Returns:
        Formatted music library information
    """
    try:
        conn = sqlite3.connect(music_db.db_path)
        cursor = conn.cursor()
        
        # Get total songs
        cursor.execute('SELECT COUNT(*) FROM songs')
        total_songs = cursor.fetchone()[0]
        
        # Get songs by mood
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN mood_tags LIKE '%happy%' THEN 'Happy'
                    WHEN mood_tags LIKE '%sad%' THEN 'Sad'
                    WHEN mood_tags LIKE '%relaxed%' OR mood_tags LIKE '%calm%' THEN 'Relaxed'
                    WHEN mood_tags LIKE '%angry%' OR mood_tags LIKE '%aggressive%' THEN 'Angry'
                    WHEN mood_tags LIKE '%motivated%' OR mood_tags LIKE '%workout%' THEN 'Motivated'
                    WHEN mood_tags LIKE '%romantic%' OR mood_tags LIKE '%love%' THEN 'Romantic'
                    ELSE 'Other'
                END as mood_category,
                COUNT(*) as song_count
            FROM songs 
            GROUP BY mood_category
            ORDER BY song_count DESC
        ''')
        
        mood_stats = cursor.fetchall()
        
        # Get recent playlists
        cursor.execute('''
            SELECT name, mood, created_at, song_count 
            FROM playlists 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        
        recent_playlists = cursor.fetchall()
        conn.close()
        
        result = f"""🎵 MUSIC LIBRARY OVERVIEW 🎵

📊 Total Songs: {total_songs}

🎭 Available Mood Categories:
"""
        
        for mood, count in mood_stats:
            if mood != 'Other':
                result += f"• {mood}: {count} songs\n"
        
        result += f"""
🎼 Supported Moods:
• 😊 Happy - Upbeat, joyful, celebratory music
• 😢 Sad - Melancholic, emotional, healing songs  
• 😌 Relaxed - Calm, peaceful, meditative tracks
• 😠 Angry - Intense, aggressive, powerful music
• 💪 Motivated - Energetic, workout, determination songs
• 💕 Romantic - Love songs, intimate, date night music
• 😰 Stressed - Anxiety relief, calming, therapeutic sounds

📋 Recent Playlists Created:
"""
        
        if recent_playlists:
            for playlist in recent_playlists:
                created_date = playlist[2].split(' ')[0]  # Get just the date
                result += f"• {playlist[0]} ({playlist[1]}) - {playlist[3]} songs - {created_date}\n"
        else:
            result += "• No playlists created yet\n"
        
        result += f"""
🎯 How to Use:
Just tell me how you're feeling in natural language!

Examples:
• "I'm feeling really happy today!"
• "I'm stressed and need to relax"
• "Play something for my workout"
• "I'm sad and need some comfort music"
• "Date night music please"

🤖 The AI will detect your mood and create a perfect playlist automatically! 🎵"""
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get music library: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def get_playlist_history() -> str:
    """
    Get history of created playlists and mood sessions
    
    Returns:
        Formatted playlist history
    """
    try:
        conn = sqlite3.connect(music_db.db_path)
        cursor = conn.cursor()
        
        # Get mood sessions with playlist info
        cursor.execute('''
            SELECT ms.user_input, ms.detected_mood, ms.confidence, 
                   p.name, p.song_count, ms.session_time
            FROM mood_sessions ms
            LEFT JOIN playlists p ON ms.playlist_id = p.id
            ORDER BY ms.session_time DESC
            LIMIT 10
        ''')
        
        sessions = cursor.fetchall()
        conn.close()
        
        if not sessions:
            return "📋 No music sessions found. Start by telling me how you're feeling!"
        
        result = "🎵 MUSIC SESSION HISTORY 🎵\n" + "=" * 50 + "\n\n"
        
        for session in sessions:
            user_input, mood, confidence, playlist_name, song_count, session_time = session
            
            # Format session time
            session_date = session_time.split(' ')[0]
            session_time_only = session_time.split(' ')[1].split('.')[0]
            
            result += f"""📅 {session_date} at {session_time_only}
💬 User Said: "{user_input}"
🎭 Detected Mood: {mood.title()} ({confidence:.0%} confidence)
🎵 Created Playlist: {playlist_name or 'Unknown'}
🎼 Songs: {song_count or 0}
{'─' * 40}
"""
        
        result += f"\n📊 Total Sessions: {len(sessions)}"
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get playlist history: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def control_music_playback(action: str, value: str = None) -> str:
    """
    Enhanced music playback control with more features
    
    Args:
        action: Playback action (play, pause, stop, status, next, previous, volume, shuffle, repeat, seek)
        value: Optional value for certain actions (volume level, repeat mode, seek position)
    
    Returns:
        Playback status message
    """
    try:
        action = action.lower().strip()
        
        if action == "status":
            return music_player.get_player_status()
        
        elif action == "pause":
            if music_player.is_playing:
                music_player.is_paused = True
                music_player.is_playing = False
                current_song = music_player.current_playlist['songs'][music_player.current_song_index]
                return f"""⏸️ MUSIC PAUSED ⏸️

🎵 {current_song[1]} - {current_song[2]}
⏱️ Paused at {music_player._format_duration(music_player.current_position)}

🎮 Say 'play' or 'resume' to continue"""
            else:
                return "🔇 No music is currently playing"
        
        elif action == "play" or action == "resume":
            if music_player.current_playlist and music_player.is_paused:
                music_player.is_playing = True
                music_player.is_paused = False
                current_song = music_player.current_playlist['songs'][music_player.current_song_index]
                return f"""▶️ MUSIC RESUMED ▶️

🎵 {current_song[1]} - {current_song[2]}
⏱️ Continuing from {music_player._format_duration(music_player.current_position)}

🎶 Music is now playing!"""
            else:
                return "🔇 No playlist loaded. Tell me your mood to create a playlist!"
        
        elif action == "stop":
            music_player.is_playing = False
            music_player.is_paused = False
            music_player.current_position = 0
            return """⏹️ MUSIC STOPPED ⏹️

🎵 Playback stopped and reset
💡 Tell me your mood to start a new playlist!"""
        
        elif action == "next":
            if music_player.current_playlist:
                if music_player.current_song_index < len(music_player.current_playlist['songs']) - 1:
                    music_player.current_song_index += 1
                    music_player.current_position = 0
                    current_song = music_player.current_playlist['songs'][music_player.current_song_index]
                    return f"""⏭️ NEXT SONG ⏭️

🎵 Now Playing: {current_song[1]}
👤 Artist: {current_song[2]}
🎼 Genre: {current_song[3]}
📊 Energy: {current_song[5]}/10

🎶 Track {music_player.current_song_index + 1} of {len(music_player.current_playlist['songs'])}"""
                else:
                    if music_player.repeat_mode == "all":
                        music_player.current_song_index = 0
                        music_player.current_position = 0
                        current_song = music_player.current_playlist['songs'][0]
                        return f"🔁 Playlist restarted: {current_song[1]} - {current_song[2]}"
                    else:
                        return "⏭️ End of playlist reached. Enable repeat mode to loop!"
            else:
                return "🔇 No playlist loaded"
        
        elif action == "previous":
            if music_player.current_playlist:
                if music_player.current_song_index > 0:
                    music_player.current_song_index -= 1
                    music_player.current_position = 0
                    current_song = music_player.current_playlist['songs'][music_player.current_song_index]
                    return f"""⏮️ PREVIOUS SONG ⏮️

🎵 Now Playing: {current_song[1]}
👤 Artist: {current_song[2]}
🎼 Genre: {current_song[3]}
📊 Energy: {current_song[5]}/10

🎶 Track {music_player.current_song_index + 1} of {len(music_player.current_playlist['songs'])}"""
                else:
                    return "⏮️ Already at first song"
            else:
                return "🔇 No playlist loaded"
        
        elif action == "volume":
            if value:
                return music_player.set_volume(value)
            else:
                return f"🔊 Current volume: {music_player.volume}%. Use 'volume [0-100]' to change."
        
        elif action == "shuffle":
            return music_player.toggle_shuffle()
        
        elif action == "repeat":
            if value:
                return music_player.set_repeat_mode(value)
            else:
                return f"🔁 Current repeat mode: {music_player.repeat_mode.upper()}. Use 'repeat [off/one/all]' to change."
        
        elif action == "seek":
            if value:
                return music_player.seek_to_position(value)
            else:
                return "⏩ Use 'seek [seconds]' to jump to a position in the song"
        
        else:
            return f"""❌ Unknown action: {action}

🎮 Available Controls:
• play/resume - Start/resume playback
• pause - Pause current song  
• stop - Stop and reset playback
• next - Skip to next song
• previous - Go to previous song
• volume [0-100] - Set volume level
• shuffle - Toggle shuffle mode
• repeat [off/one/all] - Set repeat mode
• seek [seconds] - Jump to position
• status - Show detailed player status"""
        
    except Exception as e:
        error_msg = f"❌ Playback control error: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def get_current_song_details() -> str:
    """
    Get detailed information about the currently playing song
    
    Returns:
        Detailed song information with lyrics preview and recommendations
    """
    try:
        if not music_player.current_playlist:
            return "🔇 No music currently playing. Tell me your mood to start!"
        
        current_song = music_player.current_playlist['songs'][music_player.current_song_index]
        
        # Generate mock lyrics preview (first few lines)
        lyrics_preview = {
            "Happy": "🎵 I'm walking on sunshine, whoa-oh!\nAnd don't it feel good!\nHey, alright now...",
            "Someone Like You": "🎵 I heard that you're settled down\nThat you found a girl and you're married now\nI heard that your dreams came true...",
            "Eye of the Tiger": "🎵 Rising up, back on the street\nDid my time, took my chances\nWent the distance, now I'm back on my feet...",
            "Perfect": "🎵 I found a love for me\nDarling, just dive right in and follow my lead\nWell, I found a girl, beautiful and sweet..."
        }
        
        song_title = current_song[1]
        lyrics = lyrics_preview.get(song_title, "🎵 Lyrics not available for this song")
        
        # Calculate song progress
        progress_percent = (music_player.current_position / current_song[7]) * 100 if current_song[7] > 0 else 0
        
        result = f"""🎵 NOW PLAYING - DETAILED VIEW 🎵

╔═══════════════════════════════════════════╗
║  🎧 SONG INFORMATION                      ║
╠═══════════════════════════════════════════╣
║  Title: {current_song[1]:<30} ║
║  Artist: {current_song[2]:<29} ║
║  Genre: {current_song[3]:<30} ║
║  Duration: {music_player._format_duration(current_song[7]):<27} ║
║  Energy Level: {current_song[5]}/10{' ' * 20} ║
║  Tempo: {current_song[6]:<30} ║
╠═══════════════════════════════════════════╣
║  🎮 PLAYBACK STATUS                       ║
╠═══════════════════════════════════════════╣
║  Status: {'▶️ Playing' if music_player.is_playing else '⏸️ Paused' if music_player.is_paused else '⏹️ Stopped':<30} ║
║  Progress: {progress_percent:.1f}%{' ' * 25} ║
║  Position: {music_player._format_duration(music_player.current_position)} / {music_player._format_duration(current_song[7])}{' ' * 15} ║
║  Volume: {music_player.volume}%{' ' * 28} ║
╠═══════════════════════════════════════════╣
║  📀 PLAYLIST INFO                         ║
╠═══════════════════════════════════════════╣
║  Playlist: {music_player.current_playlist['name']:<26} ║
║  Track: {music_player.current_song_index + 1} of {len(music_player.current_playlist['songs'])}{' ' * 25} ║
║  Shuffle: {'ON' if music_player.shuffle_mode else 'OFF'}{' ' * 27} ║
║  Repeat: {music_player.repeat_mode.upper()}{' ' * 28} ║
╚═══════════════════════════════════════════╝

🎤 LYRICS PREVIEW:
{lyrics}

🎯 MOOD TAGS: {current_song[4]}

🎵 SIMILAR SONGS IN PLAYLIST:
"""
        
        # Add similar songs from current playlist
        similar_count = 0
        for i, song in enumerate(music_player.current_playlist['songs']):
            if i != music_player.current_song_index and similar_count < 3:
                if any(tag in song[4] for tag in current_song[4].split(',')):
                    result += f"• {song[1]} - {song[2]} ({song[3]})\n"
                    similar_count += 1
        
        if similar_count == 0:
            result += "• No similar songs found in current playlist\n"
        
        result += f"\n🎮 Use music controls to navigate: next, previous, pause, volume, etc."
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get song details: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def create_custom_playlist(mood_description: str, song_count: int = 10, energy_preference: str = "balanced") -> str:
    """
    Create a custom playlist with specific parameters
    
    Args:
        mood_description: Detailed description of desired mood/vibe
        song_count: Number of songs in playlist (5-20)
        energy_preference: Energy level preference (low, balanced, high)
    
    Returns:
        Custom playlist creation result
    """
    try:
        print(f"🎵 Creating custom playlist: {mood_description}")
        
        # Validate parameters
        song_count = max(5, min(20, int(song_count)))
        
        energy_map = {
            'low': (1, 4),
            'balanced': (3, 7), 
            'high': (7, 10)
        }
        
        energy_range = energy_map.get(energy_preference.lower(), (3, 7))
        
        # Detect mood using existing analyzer
        mood_data = mood_analyzer.detect_mood(mood_description)
        
        # Get songs matching criteria
        conn = sqlite3.connect(music_db.db_path)
        cursor = conn.cursor()
        
        # Advanced query with energy filtering
        cursor.execute('''
            SELECT * FROM songs 
            WHERE (mood_tags LIKE ? OR mood_tags LIKE ?) 
            AND energy_level BETWEEN ? AND ?
            ORDER BY RANDOM()
            LIMIT ?
        ''', (f"%{mood_data['mood']}%", f"%{energy_preference}%", energy_range[0], energy_range[1], song_count * 2))
        
        songs = cursor.fetchall()
        
        # If not enough songs, get more with relaxed criteria
        if len(songs) < song_count:
            cursor.execute('''
                SELECT * FROM songs 
                WHERE energy_level BETWEEN ? AND ?
                ORDER BY RANDOM()
                LIMIT ?
            ''', (energy_range[0], energy_range[1], song_count))
            songs = cursor.fetchall()
        
        conn.close()
        
        # Select best songs
        selected_songs = songs[:song_count]
        
        # Create custom playlist name
        custom_name = f"Custom {mood_data['mood'].title()} Mix ({energy_preference.title()} Energy)"
        
        # Create playlist
        song_ids = [song[0] for song in selected_songs]
        playlist_id = music_db.create_playlist(custom_name, mood_data['mood'], mood_description, song_ids)
        
        # Calculate stats
        total_duration = sum(song[7] for song in selected_songs)
        avg_energy = sum(song[5] for song in selected_songs) / len(selected_songs)
        
        result = f"""🎵 CUSTOM PLAYLIST CREATED 🎵

📀 Playlist: {custom_name}
🎭 Detected Mood: {mood_data['mood'].title()} ({mood_data['confidence']:.0%} confidence)
⚡ Energy Level: {energy_preference.title()} (Avg: {avg_energy:.1f}/10)
🎵 Songs: {len(selected_songs)}
⏱️ Total Duration: {total_duration // 60} minutes

🎼 TRACKLIST:
"""
        
        for i, song in enumerate(selected_songs, 1):
            result += f"{i:2d}. {song[1]} - {song[2]} ({song[3]}) [{song[5]}/10]\n"
        
        result += f"""
🎯 Playlist Criteria:
• Mood: {mood_description}
• Energy: {energy_preference.title()} ({energy_range[0]}-{energy_range[1]}/10)
• Song Count: {song_count}

🎮 Ready to play! Use 'play music' to start this playlist."""
        
        # Auto-play the custom playlist
        playlist_info = {
            'id': playlist_id,
            'name': custom_name,
            'mood': mood_data['mood'],
            'songs': selected_songs,
            'total_duration': total_duration,
            'song_count': len(selected_songs)
        }
        
        play_result = music_player.play_playlist(playlist_info)
        result += f"\n\n{play_result}"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Custom playlist creation failed: {str(e)}"
        print(error_msg)
        return error_msg

# Simple functions for direct use
def play_music_for_mood(user_input):
    """Simple music playing function"""
    return analyze_mood_and_play_music.func(user_input)

def get_music_info():
    """Simple music library info function"""
    return get_music_library.func()

def get_music_history():
    """Simple music history function"""
    return get_playlist_history.func()

def control_music(action, value=None):
    """Simple music control function"""
    return control_music_playback.func(action, value)

def get_song_details():
    """Simple current song details function"""
    return get_current_song_details.func()

def create_playlist(mood_description, song_count=10, energy_preference="balanced"):
    """Simple custom playlist creation function"""
    return create_custom_playlist.func(mood_description, song_count, energy_preference)

# Test function
def test_music_agent():
    """Test the music agent functionality"""
    print("🧪 Testing Mood-Aware Music Agent...")
    print("=" * 60)
    
    # Test 1: Happy mood
    print("\n1. Testing happy mood detection...")
    result1 = play_music_for_mood("I'm feeling absolutely fantastic today! Everything is going great!")
    print("✅ Happy mood test completed")
    print(result1[:200] + "..." if len(result1) > 200 else result1)
    
    # Test 2: Sad mood
    print("\n2. Testing sad mood detection...")
    result2 = play_music_for_mood("I'm really down today, just broke up with my partner")
    print("✅ Sad mood test completed")
    print(result2[:200] + "..." if len(result2) > 200 else result2)
    
    # Test 3: Workout mood
    print("\n3. Testing workout mood detection...")
    result3 = play_music_for_mood("Going to the gym, need some pumping music!")
    print("✅ Workout mood test completed")
    print(result3[:200] + "..." if len(result3) > 200 else result3)
    
    # Test 4: Music library
    print("\n4. Testing music library...")
    library_info = get_music_info()
    print("✅ Music library test completed")
    print(library_info[:300] + "..." if len(library_info) > 300 else library_info)
    
    print("\n🎉 Music agent testing completed!")

if __name__ == "__main__":
    test_music_agent()