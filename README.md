# Multi-Agent AI Framework

An industry-grade multi-agent AI system built with **LangChain + LangGraph + Ollama**. It understands natural-language commands, routes them to specialized agents via a LangGraph state machine, and executes real-world actions — sending emails, making voice calls, sending WhatsApp messages, booking flights, playing mood-based music, generating MCQ exams, and managing tasks.

## Architecture

```
User Input (Web UI / CLI)
        │
        ▼
┌──────────────────────┐
│  LLM Task Parser      │  Ollama converts natural language → structured JSON
│  (task_parser.py)     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Task Memory          │  SQLite stores every task + execution log
│  (task_memory.py)     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  LangGraph Router     │  Routes by task type to the right agent node
│  (agent_graph.py)     │
└──────────┬───────────┘
           │
   ┌───────┴────────┬─────────┬──────────┬──────────┬─────────┐
   ▼       ▼        ▼         ▼          ▼          ▼        ▼
 Email  Call  WhatsApp  Flight  Music  MCQ  Task
```

A background **scheduler** (`followup/scheduler.py`) continuously processes queued tasks, and an **LLM message generator** (`llm/message_generator.py`) produces professional, context-aware content for each communication agent.

## The 7 Agents

| Agent | File | What it does |
|-------|------|--------------|
| **Email** | `agents/email_agent.py` | Sends real emails via Gmail SMTP with Ollama-generated professional content |
| **Call** | `agents/call_agent.py` | Makes voice calls via Twilio with AI-generated Text-to-Speech messages |
| **WhatsApp** | `agents/whatsapp_agent.py` | Sends WhatsApp messages via Twilio WhatsApp API |
| **Flight** | `agents/flight_agent.py` | Searches and books flights from a SQLite flight database |
| **Music** | `agents/music_agent.py` | Detects mood from input and generates a matching playlist |
| **MCQ** | `agents/mcq_agent.py` | Generates questions, runs adaptive exams, and analyzes performance |
| **Task** | `agents/task_agent.py` | Creates, tracks, and completes tasks with deadline alerts |

## Tech Stack

- **LangGraph** — multi-agent state graph orchestration
- **LangChain + Ollama** — local LLM for task parsing and message generation
- **Flask** — web frontend with per-agent pages
- **Twilio** — WhatsApp messaging and voice calls
- **Gmail SMTP** — email delivery
- **SQLite** — persistent storage for tasks, flights, music, and MCQ data

## Prerequisites

1. **Python 3.9+**
2. **Ollama** running locally with a model installed:
   ```bash
   # Install Ollama: https://ollama.com
   ollama serve          # start the server
   ollama pull llama2    # download the model used by default
   ```
3. **Twilio account** (for WhatsApp + voice calls) — [console.twilio.com](https://console.twilio.com/)
4. **Gmail account** with an App Password — [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/multi-agent-ai-framework.git
cd multi-agent-ai-framework

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Configuration

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your real values:

```env
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+10000000000
FLASK_SECRET_KEY=a-random-secret-string
```

> **Security:** The `.env` file is gitignored and will never be committed. Never share your real credentials.

## Running the App

### Web interface (recommended)

```bash
python run_project.py
```

This runs startup diagnostics (checks Ollama, dependencies, and config) then launches the Flask server. Open **http://localhost:5000** in your browser.

You can also start the web server directly:

```bash
python app.py
```

### CLI interface

```bash
# Interactive mode
python -m framework_multiagent.main

# Single command
python -m framework_multiagent.main "send email to john@example.com saying hello"
```

## Project Structure

```
.
├── app.py                      # Flask web frontend + REST API
├── run_project.py              # Startup diagnostics + launcher
├── requirements.txt
├── .env.example                # Template for environment variables
├── .gitignore
├── templates/                  # Jinja2 HTML pages (one per agent)
│   ├── base.html
│   ├── index.html
│   ├── email.html
│   ├── call.html
│   ├── whatsapp.html
│   ├── task.html
│   ├── flight.html
│   ├── music.html
│   ├── mcq.html
│   └── flight_platform.html
└── framework_multiagent/       # Core framework package
    ├── __init__.py
    ├── config.py               # Loads config from environment variables
    ├── main.py                 # CLI entry point
    ├── agents/                  # LangChain @tool agent implementations
    │   ├── email_agent.py
    │   ├── call_agent.py
    │   ├── whatsapp_agent.py
    │   ├── flight_agent.py
    │   ├── music_agent.py
    │   ├── mcq_agent.py
    │   └── task_agent.py
    ├── graph/                   # LangGraph multi-agent orchestration
    │   └── agent_graph.py
    ├── llm/                     # Ollama-powered task parsing + message generation
    │   ├── task_parser.py
    │   └── message_generator.py
    ├── memory/                  # SQLite task storage
    │   └── task_memory.py
    └── followup/                # Background task scheduler
        └── scheduler.py
```

## Example Commands

```
send email to john@example.com saying the project is complete
whatsapp to 9876543210 that the meeting is postponed
call +919876543210
book a flight from Delhi to Mumbai tomorrow
I'm feeling happy, play some music
generate 5 MCQ questions on Python programming
create a task to finish the report by 5pm
```

## Additional Documentation

- [Architecture Flowchart](MULTI_AGENT_FLOWCHART.md)
- [Agent Connections Visual](AGENT_CONNECTIONS_VISUAL.md)
- [MCQ Intelligence Platform](MCQ_INTELLIGENCE_PLATFORM.md)
- [MCQ Usage Guide](MCQ_USAGE_GUIDE.md)
- [Upgrade Guide](UPGRADE_GUIDE.md)

## License

This project is provided for educational and development purposes.
