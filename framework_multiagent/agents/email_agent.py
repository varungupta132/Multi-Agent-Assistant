"""
Intelligent Email Agent - LangChain Tool with Ollama-powered content generation
"""
from langchain_core.tools import tool
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT, DEFAULT_EMAIL_RECIPIENT
from llm.message_generator import generate_email_content

@tool
def send_email(to: str, user_request: str, subject: str = "", body: str = "") -> str:
    """
    Send an intelligent email using SMTP with Ollama-generated content.
    
    Args:
        to: Recipient email address
        user_request: Original user request for context
        subject: Optional subject (will be generated if not provided)
        body: Optional body (will be generated if not provided)
    
    Returns:
        Success or error message
"""

    try:
        print(f"📧 Processing intelligent email to {to}")
        print(f"🎯 User request: {user_request[:100]}...")
        
        # Use default recipient if not provided
        if not to:
            to = DEFAULT_EMAIL_RECIPIENT
            print(f"📍 Using default recipient: {to}")
        
        # Generate intelligent content if not provided
        if not subject or not body:
            print("🧠 Generating intelligent email content...")
            generated = generate_email_content(user_request, to, "email communication")
            
            if not subject:
                subject = generated["subject"]
            if not body:
                body = generated["body"]
        
        print(f"📋 Final subject: {subject}")
        print(f"💬 Final body: {body[:100]}...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to
        msg['Subject'] = subject
        
        # Create email body with timestamp
        email_body = f"""{body}

---
This email was sent by your Multi-Agent AI Assistant
Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
From: {EMAIL_ADDRESS}

Best regards,
AI Assistant Framework"""
        
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
        
        # Connect to server and send
        print("🔗 Connecting to Gmail SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        print("🔐 Authenticating...")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        print("📤 Sending intelligent email...")
        server.sendmail(EMAIL_ADDRESS, to, msg.as_string())
        server.quit()
        
        success_msg = f"✅ Intelligent email sent successfully to {to}"
        print(success_msg)
        return success_msg
        
    except Exception as e:
        error_msg = f"❌ Email failed: {str(e)}"
        print(error_msg)
        return error_msg

# Tool metadata for LangGraph
email_tool = send_email