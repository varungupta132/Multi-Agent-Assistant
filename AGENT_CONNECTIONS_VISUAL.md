# 🔄 Multi-Agent Framework - Visual Connection Map

## **🎯 Complete Agent Connection Flowchart**

```
                                🚀 MULTI-AGENT FRAMEWORK
                                    (main.py)
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   🎤 USER INPUT     │
                              │                     │
                              │ • Web Interface     │
                              │ • Python API        │
                              │ • Natural Language  │
                              │ • CLI Commands      │
                              └─────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  🧠 LLM PARSER      │
                              │  (task_parser.py)   │
                              │                     │
                              │ • Ollama LLM        │
                              │ • JSON Conversion   │
                              │ • Task Classification│
                              └─────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  💾 TASK MEMORY     │
                              │  (task_memory.py)   │
                              │                     │
                              │ • SQLite Database   │
                              │ • Task Queue        │
                              │ • Analytics         │
                              └─────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  🎯 LANGGRAPH       │
                              │  (agent_graph.py)   │
                              │                     │
                              │ • Router System     │
                              │ • State Management  │
                              │ • Agent Orchestration│
                              └─────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
        ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
        │    📧 EMAIL         │ │    📞 CALL          │ │   📱 WHATSAPP       │
        │    AGENT            │ │    AGENT            │ │   AGENT             │
        │                     │ │                     │ │                     │
        │ email_agent.py      │ │ call_agent.py       │ │ whatsapp_agent.py   │
        │                     │ │                     │ │                     │
        │ ┌─────────────────┐ │ │ ┌─────────────────┐ │ │ ┌─────────────────┐ │
        │ │🧠 AI Enhancement│ │ │ │📞 Smart Dialing │ │ │ │📱 Message Send  │ │
        │ │📧 Email Compose │ │ │ │📊 Call Logging  │ │ │ │👥 Contact Mgmt  │ │
        │ │📤 Send System   │ │ │ │🎙️ Voice Integ   │ │ │ │💬 Chat History  │ │
        │ │📊 Tracking      │ │ │ │📈 Analytics     │ │ │ │📎 Media Support │ │
        │ └─────────────────┘ │ │ └─────────────────┘ │ │ └─────────────────┘ │
        └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
        ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
        │    ✈️ FLIGHT        │ │    🎵 MUSIC         │ │   🧠 MCQ            │
        │    AGENT            │ │    AGENT            │ │   AGENT             │
        │                     │ │                     │ │                     │
        │ flight_agent.py     │ │ music_agent.py      │ │ mcq_agent.py        │
        │                     │ │                     │ │                     │
        │ ┌─────────────────┐ │ │ ┌─────────────────┐ │ │ ┌─────────────────┐ │
        │ │✈️ Flight Search │ │ │ │🧠 Mood Analysis │ │ │ │🧠 AI Question   │ │
        │ │💳 Booking Sys   │ │ │ │🎵 Music Select  │ │ │ │📝 Exam Creation │ │
        │ │💰 Price Track   │ │ │ │📱 Playlist Mgmt │ │ │ │🔍 Platform Scan │ │
        │ │🗺️ Travel Plan   │ │ │ │😊 Emotion Detect│ │ │ │📊 Analytics     │ │
        │ └─────────────────┘ │ │ └─────────────────┘ │ │ └─────────────────┘ │
        └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   📋 TASK AGENT     │
                              │                     │
                              │ task_agent.py       │
                              │                     │
                              │ ┌─────────────────┐ │
                              │ │📋 Task Creation │ │
                              │ │📊 Task Mgmt     │ │
                              │ │⏰ Deadline Track│ │
                              │ │📈 Progress Mon  │ │
                              │ └─────────────────┘ │
                              └─────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  ⏰ SCHEDULER       │
                              │  (scheduler.py)     │
                              │                     │
                              │ • Background Tasks  │
                              │ • Queue Management  │
                              │ • Retry Logic       │
                              └─────────────────────┘
```

## **🌐 Web Interface Integration Map**

```
                                🌐 FLASK WEB APPLICATION
                                      (app.py)
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
        ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
        │   📧 /email         │ │   📞 /call          │ │  📱 /whatsapp       │
        │                     │ │                     │ │                     │
        │ ┌─────────────────┐ │ │ ┌─────────────────┐ │ │ ┌─────────────────┐ │
        │ │📝 Form Interface│ │ │ │📞 Dialer UI     │ │ │ │💬 Message UI    │ │
        │ │📤 Send Button   │ │ │ │📞 Call Button   │ │ │ │📤 Send Button   │ │
        │ │📊 History View  │ │ │ │📋 Call Log      │ │ │ │💬 Chat History  │ │
        │ └─────────────────┘ │ │ └─────────────────┘ │ │ └─────────────────┘ │
        │         │           │ │         │           │ │         │           │
        │         ▼           │ │         ▼           │ │         ▼           │
        │ POST /api/email     │ │ POST /api/call      │ │ POST /api/whatsapp  │
        └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
        ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
        │   ✈️ /flight        │ │   🎵 /music         │ │   🧠 /mcq           │
        │                     │ │                     │ │                     │
        │ ┌─────────────────┐ │ │ ┌─────────────────┐ │ │ ┌─────────────────┐ │
        │ │🔍 Search UI     │ │ │ │😊 Mood Selector │ │ │ │📊 Statistics    │ │
        │ │💳 Booking Form  │ │ │ │🎵 Play Controls │ │ │ │🧠 Generate      │ │
        │ │📊 Flight History│ │ │ │📱 Playlist View │ │ │ │📝 Create Exam   │ │
        │ └─────────────────┘ │ │ └─────────────────┘ │ │ │🔍 Analyze       │ │
        │         │           │ │         │           │ │ │🤖 Platform Scan │ │
        │         ▼           │ │         ▼           │ │ │📝 Take Exam     │ │
        │ POST /api/flight    │ │ POST /api/music     │ │ └─────────────────┘ │
        └─────────────────────┘ └─────────────────────┘ │         │           │
                    │                    │               │         ▼           │
                    └────────────────────┼───────────────┤ POST /api/mcq/*     │
                                         │               └─────────────────────┘
                                         ▼
                              ┌─────────────────────┐
                              │   📋 /task          │
                              │                     │
                              │ ┌─────────────────┐ │
                              │ │📋 Task Creator  │ │
                              │ │📊 Task List     │ │
                              │ │📈 Progress Track│ │
                              │ └─────────────────┘ │
                              │         │           │
                              │         ▼           │
                              │ POST /api/task      │
                              └─────────────────────┘
```

## **💾 Database Connection Architecture**

```
                              🗄️ DATABASE ECOSYSTEM
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
        ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
        │   📊 tasks.db       │ │🧠 mcq_intelligence  │ │   🎵 music.db       │
        │                     │ │      .db            │ │                     │
        │ ┌─────────────────┐ │ │ ┌─────────────────┐ │ │ ┌─────────────────┐ │
        │ │📋 tasks         │ │ │ │🧠 mcq_questions │ │ │ │🎵 music_library │ │
        │ │👤 users         │ │ │ │📝 exam_sessions │ │ │ │📱 playlists     │ │
        │ │📊 analytics     │ │ │ │✅ user_answers  │ │ │ │📊 play_history  │ │
        │ │📈 performance   │ │ │ │🔍 platform_scans│ │ │ │😊 mood_data     │ │
        │ └─────────────────┘ │ │ │📊 learning_anal │ │ │ └─────────────────┘ │
        └─────────────────────┘ │ └─────────────────┘ │ └─────────────────────┘
                    │           └─────────────────────┘           │
                    └────────────────────┼────────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   ✈️ flights.db     │
                              │                     │
                              │ ┌─────────────────┐ │
                              │ │✈️ bookings      │ │
                              │ │🔍 searches      │ │
                              │ │💰 price_history │ │
                              │ │📊 travel_stats  │ │
                              │ └─────────────────┘ │
                              └─────────────────────┘
```

## **🔄 Real-Time Data Flow Example**

### **Complete Flow: "Generate MCQ questions on Python"**

```
Step 1: 🎤 USER INPUT
┌─────────────────────────────────────────────────────────────┐
│ Input: "Generate MCQ questions on Python programming"       │
│ Source: Web UI (/mcq) or CLI or API                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 2: 🧠 LLM PARSING
┌─────────────────────────────────────────────────────────────┐
│ task_parser.py → Ollama LLM                                 │
│ Output: {"task": "mcq", "operation": "generate",            │
│          "topic": "Python Programming", "difficulty": "med"}│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 3: 💾 MEMORY STORAGE
┌─────────────────────────────────────────────────────────────┐
│ task_memory.py → tasks.db                                   │
│ Task ID: 123, Status: "pending", Data: parsed JSON         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 4: 🎯 ROUTING
┌─────────────────────────────────────────────────────────────┐
│ agent_graph.py → LangGraph Router                           │
│ Identifies: task_type = "mcq" → Routes to MCQ Agent        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 5: 🧠 MCQ AGENT EXECUTION
┌─────────────────────────────────────────────────────────────┐
│ mcq_agent.py → MCQ Intelligence Platform                    │
│ ├── Operation Router: "generate"                            │
│ ├── AI Generation: Ollama LLM creates questions            │
│ ├── Fallback System: Smart fallbacks if LLM fails         │
│ ├── Database: Save to mcq_intelligence.db                  │
│ └── Analytics: Update platform statistics                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 6: 💾 RESULT STORAGE
┌─────────────────────────────────────────────────────────────┐
│ Multiple Databases Updated:                                 │
│ ├── tasks.db: Task status = "completed"                    │
│ ├── mcq_intelligence.db: New questions added               │
│ └── Analytics: Platform metrics updated                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 7: 📤 USER RESPONSE
┌─────────────────────────────────────────────────────────────┐
│ Response Channels:                                          │
│ ├── Web UI: Shows generated questions in interface         │
│ ├── API: Returns JSON with question data                   │
│ └── CLI: Formatted success message with details            │
└─────────────────────────────────────────────────────────────┘
```

## **🎯 Agent Interaction Matrix**

```
                    📧    📞    📱    ✈️    🎵    🧠    📋
                  Email Call WhatsApp Flight Music MCQ Task
                  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
🧠 LLM Parser     │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │
💾 Task Memory    │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │
🎯 Router         │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │
🌐 Web Interface  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │
📊 Analytics      │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │
⏰ Scheduler      │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │  ✅  │
                  └─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Legend:
✅ = Full Integration
📧 = Email Agent        🎵 = Music Agent
📞 = Call Agent         🧠 = MCQ Agent  
📱 = WhatsApp Agent     📋 = Task Agent
✈️ = Flight Agent
```

**Your multi-agent framework has complete interconnectivity between all components, creating a unified AI ecosystem!** 🚀