# Configuration file for the multi-agent framework
# All sensitive values are loaded from environment variables via a .env file.
# Copy .env.example to .env and fill in your own credentials.
import os
from dotenv import load_dotenv

# Load .env file from project root (parent of framework_multiagent)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=_env_path)

# Email Configuration (Gmail)
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Twilio Configuration (WhatsApp & Voice Calls)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# Default recipients
DEFAULT_EMAIL_RECIPIENT = os.getenv("DEFAULT_EMAIL_RECIPIENT", "test@gmail.com")
DEFAULT_PHONE_RECIPIENT = os.getenv("DEFAULT_PHONE_RECIPIENT", "+910000000000")

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "tasks.db")
