"""
Intelligent Call Agent - LangChain Tool with Ollama-powered content generation
Uses Twilio's Text-to-Speech for custom voice messages
"""
from langchain_core.tools import tool
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from datetime import datetime
import urllib.parse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, DEFAULT_PHONE_RECIPIENT

@tool
def make_call(to: str, user_request: str = "", message: str = "") -> str:
    """
    Make an intelligent phone call using Twilio Voice API with AI-generated content.
    
    Args:
        to: Recipient phone number (with country code)
        user_request: Original user request for context
        message: Optional message to speak (will be generated if not provided)
    
    Returns:
        Success or error message with call SID
    """
    try:
        print(f"📞 Processing intelligent call to {to}")
        if user_request:
            print(f"🎯 User request: {user_request[:100]}...")
        
        # Use default recipient if not provided
        if not to:
            to = DEFAULT_PHONE_RECIPIENT
            print(f"📍 Using default recipient: {to}")
        
        # Format phone number
        if not to.startswith('+'):
            to = '+91' + to
        
        print(f"📞 Formatted number: {to}")
        
        # Generate intelligent voice message if not provided
        if not message and user_request:
            print("🧠 Generating intelligent voice message...")
            from llm.message_generator import generate_voice_message
            message = generate_voice_message(user_request, to, "voice call")
        elif not message:
            message = "Hello! This is a call from your AI assistant. Have a great day!"
        
        print(f"🗣️ Final voice message: {message[:100]}...")
        
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        print("📤 Initiating intelligent call with TTS...")
        
        # Create TwiML with Text-to-Speech
        twiml = VoiceResponse()
        twiml.say(
            message,
            voice='alice',  # Use Alice voice (clear female voice)
            language='en-US'
        )
        
        # Convert TwiML to string
        twiml_str = str(twiml)
        print(f"🎵 TwiML generated: {twiml_str[:100]}...")
        
        # Make the call with inline TwiML
        call = client.calls.create(
            to=to,
            from_=TWILIO_PHONE_NUMBER,
            twiml=twiml_str,  # Use inline TwiML instead of URL
            timeout=30,
            record=False
        )
        
        success_msg = f"✅ Intelligent call initiated to {to}. Call SID: {call.sid}"
        print(success_msg)
        print(f"📋 Call Status: {call.status}")
        print(f"🔗 Call SID: {call.sid}")
        print(f"🎤 Voice message: {message[:50]}...")
        
        return success_msg
        
    except Exception as e:
        error_msg = f"❌ Call failed: {str(e)}"
        print(error_msg)
        
        # Provide specific error guidance
        error_str = str(e).lower()
        if "not a valid phone number" in error_str:
            print("💡 Phone number format issue. Use format: +1234567890")
        elif "not verified" in error_str or "unverified" in error_str:
            print("💡 For Twilio trial accounts, verify the destination number first")
            print("   Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
        elif "insufficient funds" in error_str or "balance" in error_str:
            print("💡 Add funds to your Twilio account")
        elif "permission" in error_str or "forbidden" in error_str:
            print("💡 Check Twilio account permissions and phone number capabilities")
        else:
            print("💡 Check Twilio console for detailed error information")
            print(f"   Account: https://console.twilio.com/us1/account")
        
        return error_msg

# Tool metadata for LangGraph
call_tool = make_call