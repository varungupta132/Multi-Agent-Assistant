"""
Intelligent WhatsApp Agent - LangChain Tool with Ollama-powered content generation
Sends WhatsApp messages via the Twilio WhatsApp API.
"""
from langchain_core.tools import tool
from twilio.rest import Client
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_NUMBER,
    DEFAULT_PHONE_RECIPIENT,
)
from llm.message_generator import generate_whatsapp_message


def _format_whatsapp_number(to: str) -> str:
    """Normalize a recipient number into the Twilio WhatsApp format."""
    if not to:
        to = DEFAULT_PHONE_RECIPIENT

    # Keep only digits and the leading +
    to = "".join(char for char in to if char.isdigit() or char == "+")

    if not to.startswith("whatsapp:"):
        if not to.startswith("+"):
            to = "+91" + to
        to = f"whatsapp:{to}"

    return to


@tool
def send_whatsapp(to: str, user_request: str, message: str = "") -> str:
    """
    Send an intelligent WhatsApp message using the Twilio WhatsApp API with
    Ollama-generated content.

    Args:
        to: Recipient phone number (with or without country code)
        user_request: Original user request for context
        message: Optional message body (will be generated if not provided)

    Returns:
        Success or error message with the message SID
    """
    try:
        print(f"📱 Processing intelligent WhatsApp message to {to}")
        if user_request:
            print(f"🎯 User request: {user_request[:100]}...")

        # Generate intelligent content if not provided
        if not message and user_request:
            print("🧠 Generating intelligent WhatsApp message...")
            message = generate_whatsapp_message(user_request, to, "whatsapp message")
        elif not message:
            message = "Hello from your AI assistant!"

        print(f"💬 Final message: {message[:100]}...")

        # Normalize the recipient number
        to = _format_whatsapp_number(to)
        print(f"📱 Formatted number: {to}")

        # Send via Twilio
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=to,
        )

        success_msg = f"✅ Intelligent WhatsApp message sent to {to}. SID: {msg.sid}"
        print(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"❌ WhatsApp failed: {str(e)}"
        print(error_msg)

        error_str = str(e).lower()
        if "not a valid phone number" in error_str:
            print("💡 Phone number format issue. Use format: +1234567890")
        elif "not verified" in error_str or "unverified" in error_str:
            print("💡 For Twilio WhatsApp sandbox, join the sandbox first:")
            print("   https://console.twilio.com/us1/develop/sms/whatsapp/sandbox")
        elif "insufficient funds" in error_str or "balance" in error_str:
            print("💡 Add funds to your Twilio account")

        return error_msg


# Tool metadata for LangGraph
whatsapp_tool = send_whatsapp
