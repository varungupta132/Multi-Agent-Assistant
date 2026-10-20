"""
Intelligent Message Generator using Ollama
Generates appropriate messages based on user intent and context
"""
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OLLAMA_MODEL, OLLAMA_BASE_URL

class MessageGenerator:
    def __init__(self):
        """Initialize the message generator with Ollama"""
        self.llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL
        )
        
        self.email_prompt = PromptTemplate(
            input_variables=["user_input", "recipient", "context"],
            template="""Generate a complete professional email from the user's brief context. Expand the context into a full, detailed, professional email.

USER CONTEXT: {user_input}

Rules:
- Create a detailed, professional email from the brief context
- Generate an appropriate subject line automatically
- Write a complete email body with proper greeting and closing
- Add relevant details and context to make it comprehensive
- Use professional business language
- Include proper email etiquette

Format:
SUBJECT: [professional subject line]
BODY: [complete professional email with greeting, detailed content, and closing]

Examples:

Context: "can we make interview tomorrow"
SUBJECT: Interview Scheduling Request - Tomorrow
BODY: Dear Hiring Manager,

I hope this email finds you well. I am writing to inquire about the possibility of scheduling an interview for tomorrow.

I am very interested in the position and would appreciate the opportunity to discuss my qualifications and how I can contribute to your team. I understand this is short notice, but I am flexible with timing and can accommodate your schedule.

Please let me know if tomorrow works for you, and if so, what time would be most convenient. I am available throughout the day and can meet either in person or via video call, whichever you prefer.

Thank you for considering my request. I look forward to hearing from you.

Best regards,
[Your Name]

Context: "meeting postponed to next week"
SUBJECT: Meeting Postponement - Rescheduling Required
BODY: Dear Team,

I hope you are all doing well. I am writing to inform you that our scheduled meeting will need to be postponed to next week due to unforeseen circumstances.

I apologize for any inconvenience this may cause and appreciate your understanding. I will send out a new meeting invitation with updated details once I have confirmed availability with all participants.

In the meantime, if there are any urgent matters that need immediate attention, please feel free to reach out to me directly.

Thank you for your flexibility and patience.

Best regards,
[Your Name]

Context: "project completed successfully"
SUBJECT: Project Completion Notification - Ready for Review
BODY: Dear Team,

I am pleased to inform you that the project has been completed successfully and is now ready for your review.

All deliverables have been finished according to the specifications and timeline we discussed. The project includes all requested features and has been thoroughly tested to ensure quality and functionality.

I have attached the final deliverables to this email for your review. Please take your time to examine the work and let me know if you have any questions or require any modifications.

I would be happy to schedule a presentation or walkthrough session at your convenience to discuss the project details and outcomes.

Thank you for your support throughout this project. I look forward to your feedback.

Best regards,
[Your Name]

Context: "sick leave for today"
SUBJECT: Sick Leave Request - [Today's Date]
BODY: Dear Manager,

I am writing to inform you that I am feeling unwell today and will not be able to come to work.

I woke up with flu-like symptoms and believe it would be best for both my recovery and the health of my colleagues if I take a sick day to rest and recover properly.

I will monitor my condition throughout the day and keep you updated on my status for tomorrow. If there are any urgent matters that require immediate attention, please feel free to contact me via email, and I will respond as soon as I am able.

I apologize for any inconvenience this may cause and appreciate your understanding.

Thank you for your consideration.

Best regards,
[Your Name]

Your professional email:"""
        )
        
        self.whatsapp_prompt = PromptTemplate(
            input_variables=["user_input", "recipient", "context"],
            template="""Generate a natural, detailed WhatsApp message based on the user's context. Create a conversational message like texting a close friend or family member.

USER CONTEXT: {user_input}

Rules:
- Write ONLY the message content
- Be natural and conversational like texting someone you know well
- Create a detailed, thoughtful message (2-4 sentences)
- Use appropriate emojis to make it friendly
- Sound genuine and personal
- Add context and details to make it more engaging
- Make it feel like a real person wrote it

Examples:

Context: "I'm stuck in traffic and will be late for dinner"
Message: Hey! 🚗 I'm completely stuck in this crazy traffic right now and it's not moving at all. I'm definitely going to be late for dinner - probably like 30-45 minutes behind schedule. Can you save me some food? I'm starving and this traffic is driving me nuts! 😅

Context: "meeting is postponed to tomorrow"  
Message: Hi there! 📅 Just wanted to let you know that our meeting today got postponed to tomorrow. Something urgent came up on their end. I'll send you the new time once I confirm it with everyone. Hope that works okay for your schedule! Let me know if you have any conflicts.

Context: "can't make it to the party tonight because I'm sick"
Message: Hey! 🤒 I'm really sorry but I won't be able to make it to the party tonight. I woke up feeling pretty awful - think I might be coming down with something. Don't want to risk getting everyone else sick! Have an amazing time and take lots of photos for me. I'll make it up to you soon! 🎉

Context: "project completed successfully"
Message: Hey! 🎉 Amazing news - I just finished the project and it turned out even better than I expected! All the hard work really paid off. I can't wait to show you what we accomplished. Want to grab coffee tomorrow so I can walk you through everything? I'm honestly pretty proud of how this came together! ✨

Your detailed message:"""
        )
        
        self.call_prompt = PromptTemplate(
            input_variables=["user_input", "recipient", "context"],
            template="""Generate a natural, detailed voice message for phone call. Create a conversational message like talking to someone you know.

USER CONTEXT: {user_input}

Rules:
- Write ONLY the voice message content
- Sound natural and conversational like talking to a real person
- Create a detailed, engaging message (20-30 seconds when spoken)
- Add context and personality to make it more natural
- No emojis or special characters (voice only)
- No asterisk actions like *chuckles*
- Sound genuine and personal
- Include relevant details to make the call more meaningful

Examples:

Context: "call mom saying I'm stuck in traffic"
Message: Hi Mom! I hope you're doing well. I'm calling because I'm completely stuck in this crazy traffic right now and it's barely moving. I'm definitely going to be late getting home, probably around 30 to 45 minutes behind schedule. I didn't want you to worry about where I was. The roads are just packed today for some reason. I'll call you again when I'm closer to home. Love you!

Context: "call doctor about appointment reschedule"
Message: Hello, this is calling about my appointment that's scheduled for this week. I'm really sorry for the short notice, but I need to reschedule it due to an unexpected work commitment that came up. I'm hoping we can find another time that works for both of us, maybe sometime next week if possible. Please give me a call back when you have a chance and we can figure out a new time. Thank you so much for understanding.

Context: "call friend about meeting today"
Message: Hey there! I hope you're having a good day. I'm calling about our meeting that we planned for today. I just wanted to double check that we're still on for it and make sure the timing still works for you. I know things can come up and schedules can change, so I figured I'd reach out to confirm. If something came up on your end, no worries at all, we can always reschedule. Just let me know what works best for you.

Context: "call office saying I'm sick"
Message: Hi, this is calling to let you know that I'm feeling pretty unwell today and won't be able to make it into the office. I woke up with what feels like the flu - fever, body aches, the whole thing. I don't want to risk getting anyone else sick, so I think it's best if I stay home and rest up. I'm hoping to feel better by tomorrow, but I'll keep you updated on my condition. If there's anything urgent that needs attention, you can reach me by email. Thanks for understanding.

Context: "call restaurant to make reservation"
Message: Hello! I'm calling to make a dinner reservation for this evening if possible. I'm looking for a table for two people, ideally around 7 or 7:30 PM if you have availability. This is actually for a special occasion, so I was hoping for a nice table if you have one available. If those times don't work, I'm flexible with the timing. Could you let me know what you have open? Thank you so much.

Context: "call landlord about maintenance issue"
Message: Hi, this is your tenant calling about a maintenance issue in my apartment. The kitchen faucet has been leaking pretty badly for the past couple of days, and it's getting worse. It's dripping constantly now and I'm worried it might cause water damage if we don't get it fixed soon. I tried tightening it myself but that didn't help. Could you please arrange for someone to come take a look at it? I'm usually available in the evenings or weekends. Thanks so much.

Your detailed voice message:"""
        )

    def generate_email_content(self, user_input: str, recipient: str = "", context: str = "") -> Dict[str, str]:
        """Generate intelligent email content"""
        try:
            print(f"🧠 Generating professional email content for: {user_input[:50]}...")
            
            response = self.llm.invoke(self.email_prompt.format(
                user_input=user_input,
                recipient=recipient,
                context=context
            ))
            
            # Clean up the response
            response = response.strip()
            
            # Remove common prefixes that Ollama adds
            prefixes_to_remove = [
                "Sure, here is a professional email based on your request:",
                "Of course, here is a professional email:",
                "Here is a professional email:",
                "Professional email:",
                "Your professional email:",
                "Email:",
                "Sure, here's a professional email:"
            ]
            
            for prefix in prefixes_to_remove:
                if response.startswith(prefix):
                    response = response[len(prefix):].strip()
            
            # Parse the response more robustly
            lines = response.split('\n')
            subject = ""
            body = ""
            body_started = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('SUBJECT:'):
                    subject = line.replace('SUBJECT:', '').strip()
                elif line.startswith('BODY:'):
                    body = line.replace('BODY:', '').strip()
                    body_started = True
                elif body_started and line:  # Continue body content
                    if body:
                        body += "\n" + line
                    else:
                        body = line
            
            # Clean up subject and body
            if subject.startswith('"') and subject.endswith('"'):
                subject = subject[1:-1].strip()
            
            # Remove placeholder names
            import re
            body = re.sub(r'\[Your Name\]', 'Your AI Assistant', body)
            body = re.sub(r'\[Boss Name\]', 'Sir/Madam', body)
            body = re.sub(r'\[Manager\]', 'Manager', body)
            body = re.sub(r'\[Today\'s Date\]', 'Today', body)
            
            # Fallback if parsing fails - create intelligent defaults
            if not subject or not body:
                print("⚠️ Parsing failed, creating intelligent fallback...")
                
                # Generate intelligent subject and body based on context
                user_lower = user_input.lower()
                if "interview" in user_lower:
                    subject = "Interview Scheduling Request"
                    if "tomorrow" in user_lower:
                        body = """Dear Hiring Manager,

I hope this email finds you well. I am writing to inquire about the possibility of scheduling an interview for tomorrow.

I am very interested in the position and would appreciate the opportunity to discuss my qualifications and how I can contribute to your team. I understand this is short notice, but I am flexible with timing and can accommodate your schedule.

Please let me know if tomorrow works for you, and if so, what time would be most convenient. I am available throughout the day and can meet either in person or via video call, whichever you prefer.

Thank you for considering my request. I look forward to hearing from you.

Best regards,
Your AI Assistant"""
                    else:
                        body = """Dear Hiring Manager,

I hope this email finds you well. I am writing to inquire about scheduling an interview at your earliest convenience.

I am very interested in the position and would appreciate the opportunity to discuss my qualifications and how I can contribute to your team. I am flexible with timing and can accommodate your schedule.

Please let me know what dates and times work best for you. I am available for either in-person or video call interviews, whichever you prefer.

Thank you for your time and consideration. I look forward to hearing from you.

Best regards,
Your AI Assistant"""
                
                elif "meeting" in user_lower:
                    if "postponed" in user_lower or "reschedule" in user_lower:
                        subject = "Meeting Postponement - Rescheduling Required"
                        body = """Dear Team,

I hope you are all doing well. I am writing to inform you that our scheduled meeting will need to be postponed due to unforeseen circumstances.

I apologize for any inconvenience this may cause and appreciate your understanding. I will send out a new meeting invitation with updated details once I have confirmed availability with all participants.

In the meantime, if there are any urgent matters that need immediate attention, please feel free to reach out to me directly.

Thank you for your flexibility and patience.

Best regards,
Your AI Assistant"""
                    else:
                        subject = "Meeting Update"
                        body = f"""Dear Team,

I hope you are doing well. I wanted to update you regarding our upcoming meeting.

{user_input}

Please let me know if you have any questions or if there's anything specific you'd like to discuss during our meeting.

Best regards,
Your AI Assistant"""
                
                elif "project" in user_lower:
                    if "completed" in user_lower or "finished" in user_lower:
                        subject = "Project Completion Notification - Ready for Review"
                        body = """Dear Team,

I am pleased to inform you that the project has been completed successfully and is now ready for your review.

All deliverables have been finished according to the specifications and timeline we discussed. The project includes all requested features and has been thoroughly tested to ensure quality and functionality.

Please take your time to examine the work and let me know if you have any questions or require any modifications. I would be happy to schedule a presentation or walkthrough session at your convenience to discuss the project details and outcomes.

Thank you for your support throughout this project. I look forward to your feedback.

Best regards,
Your AI Assistant"""
                    else:
                        subject = "Project Update"
                        body = f"""Dear Team,

I wanted to provide you with an update on the current project status.

{user_input}

Please feel free to reach out if you need any additional information or have any questions about the project progress.

Best regards,
Your AI Assistant"""
                
                elif "sick" in user_lower or "leave" in user_lower:
                    subject = "Sick Leave Request - Today"
                    body = """Dear Manager,

I am writing to inform you that I am feeling unwell today and will not be able to come to work.

I woke up with flu-like symptoms and believe it would be best for both my recovery and the health of my colleagues if I take a sick day to rest and recover properly.

I will monitor my condition throughout the day and keep you updated on my status for tomorrow. If there are any urgent matters that require immediate attention, please feel free to contact me via email, and I will respond as soon as I am able.

I apologize for any inconvenience this may cause and appreciate your understanding.

Thank you for your consideration.

Best regards,
Your AI Assistant"""
                
                elif "salary" in user_lower or "raise" in user_lower or "increase" in user_lower:
                    subject = "Request for Salary Discussion"
                    body = """Dear Manager,

I hope this email finds you well. I would like to request a meeting to discuss my current compensation and potential for a salary adjustment.

Over the past period, I have consistently delivered quality work and taken on additional responsibilities. I believe my contributions and performance warrant a review of my current salary.

I would appreciate the opportunity to discuss this matter with you in person at your convenience. Please let me know when you might be available for a brief meeting.

Thank you for your time and consideration.

Best regards,
Your AI Assistant"""
                
                elif "client" in user_lower:
                    if "reschedule" in user_lower:
                        subject = "Client Meeting Rescheduling Request"
                        body = """Dear Team,

I hope you are doing well. I wanted to inform you that our client has requested to reschedule our upcoming presentation/meeting.

I will coordinate with the client to find a new suitable time that works for everyone and will send out updated meeting details once confirmed.

Please let me know if you have any scheduling conflicts or preferences for the new meeting time.

Thank you for your flexibility.

Best regards,
Your AI Assistant"""
                    else:
                        subject = "Client Communication Update"
                        body = f"""Dear Team,

I wanted to update you regarding our recent client communication.

{user_input}

Please let me know if you need any additional information or if there are any actions we need to take.

Best regards,
Your AI Assistant"""
                
                else:
                    subject = "Important Communication"
                    body = f"""Dear Recipient,

I hope this email finds you well. I wanted to reach out regarding the following matter:

{user_input}

Please let me know if you need any additional information or if there's anything specific you'd like to discuss about this.

Thank you for your time and attention.

Best regards,
Your AI Assistant"""
            
            # Ensure body has proper structure
            if body and not body.startswith("Dear"):
                body = f"Dear Recipient,\n\nI hope this email finds you well.\n\n{body}\n\nBest regards,\nYour AI Assistant"
            
            print(f"✅ Generated professional email - Subject: {subject[:50]}...")
            print(f"📝 Body preview: {body[:100]}...")
            return {"subject": subject, "body": body}
            
        except Exception as e:
            print(f"❌ Email generation error: {e}")
            # Create a professional fallback
            return {
                "subject": "Important Message",
                "body": f"Dear Recipient,\n\nI hope this email finds you well.\n\n{user_input if user_input else 'I wanted to reach out to you regarding an important matter.'}\n\nPlease let me know if you need any additional information.\n\nBest regards,\nYour AI Assistant"
            }

    def generate_whatsapp_message(self, user_input: str, recipient: str = "", context: str = "") -> str:
        """Generate intelligent WhatsApp message"""
        try:
            print(f"🧠 Generating WhatsApp message for: {user_input[:50]}...")
            
            response = self.llm.invoke(self.whatsapp_prompt.format(
                user_input=user_input,
                recipient=recipient,
                context=context
            ))
            
            # Clean up the response more aggressively
            message = response.strip()
            
            # Remove common prefixes that Ollama adds
            prefixes_to_remove = [
                "Sure, here is a possible WhatsApp message based on your request:",
                "Of course, here is a possible response to your user request:",
                "Sure, here's a possible WhatsApp message based on your request:",
                "Of course! Here is a natural, conversational WhatsApp message based on the user's request:",
                "Here is a natural WhatsApp message:",
                "Message:",
                "Your message:",
                "WhatsApp message:"
            ]
            
            for prefix in prefixes_to_remove:
                if message.startswith(prefix):
                    message = message[len(prefix):].strip()
            
            # Remove quotes if the entire message is wrapped in quotes
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1].strip()
            
            # Remove placeholder names like [Friend's Name], [Your Name], etc.
            import re
            message = re.sub(r'\[[^\]]+\]', '', message)
            
            # Clean up extra spaces
            message = re.sub(r'\s+', ' ', message).strip()
            
            # If message is still too verbose or contains explanatory text, extract the actual message
            lines = message.split('\n')
            if len(lines) > 1:
                # Look for the line that looks most like a WhatsApp message
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(('Sure', 'Of course', 'Here', 'This', 'The message')):
                        if line.startswith('"') and line.endswith('"'):
                            line = line[1:-1].strip()
                        if len(line) > 5:  # Reasonable message length
                            message = line
                            break
            
            # Ensure we have content and it's reasonable
            if not message or len(message) < 5:
                # Create a simple fallback message
                if "traffic" in user_input.lower():
                    message = "Hey! Stuck in traffic 🚗 gonna be late"
                elif "sick" in user_input.lower():
                    message = "Hey! Not feeling well today 🤒 won't make it"
                elif "meeting" in user_input.lower():
                    message = "Hi! About our meeting - are we still on? 📅"
                elif "party" in user_input.lower():
                    message = "Hey! About the party tonight 🎉 still happening?"
                else:
                    message = "Hey! Just wanted to message you 👋"
            
            print(f"✅ Generated WhatsApp message: {message[:30]}...")
            return message
            
        except Exception as e:
            print(f"❌ WhatsApp generation error: {e}")
            return user_input if user_input else "Hello from your AI assistant!"

    def generate_voice_message(self, user_input: str, recipient: str = "", context: str = "") -> str:
        """Generate intelligent voice call message"""
        try:
            print(f"🧠 Generating detailed voice message for: {user_input[:50]}...")
            
            response = self.llm.invoke(self.call_prompt.format(
                user_input=user_input,
                recipient=recipient,
                context=context
            ))
            
            # Clean up the response more aggressively
            message = response.strip()
            
            # Remove common prefixes that Ollama adds
            prefixes_to_remove = [
                "Sure, here is a possible voice message based on your request:",
                "Of course, here is a natural voice message:",
                "Here is a voice message:",
                "Voice Message:",
                "Your voice message:",
                "Message:",
                "Sure, here's a voice message:",
                "Your message:",
                "Your detailed voice message:"
            ]
            
            for prefix in prefixes_to_remove:
                if message.startswith(prefix):
                    message = message[len(prefix):].strip()
            
            # Remove quotes if the entire message is wrapped in quotes
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1].strip()
            
            # Remove asterisk actions like *chuckles*, *giggles*, etc.
            import re
            message = re.sub(r'\*[^*]+\*', '', message)
            
            # Remove placeholder names like [Friend's Name], [Your Name], etc.
            message = re.sub(r'\[[^\]]+\]', '', message)
            
            # Clean up extra spaces and punctuation
            message = re.sub(r'\s+', ' ', message).strip()
            message = re.sub(r'\s*,\s*,', ',', message)  # Remove double commas
            message = re.sub(r'\s*\.\s*\.', '.', message)  # Remove double periods
            
            # If message is still too verbose, extract the actual message
            lines = message.split('\n')
            if len(lines) > 1:
                # Look for the line that looks most like a voice message
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(('Sure', 'Of course', 'Here', 'This', 'The message')):
                        if line.startswith('"') and line.endswith('"'):
                            line = line[1:-1].strip()
                        if len(line) > 20:  # Reasonable message length
                            message = line
                            break
            
            # Create intelligent fallbacks if message is too short or parsing failed
            if not message or len(message) < 20 or len(message) > 300:
                print("⚠️ Creating intelligent voice message fallback...")
                user_lower = user_input.lower()
                
                if "traffic" in user_lower:
                    message = "Hi! I hope you're doing well. I'm calling because I'm completely stuck in this crazy traffic right now and it's barely moving. I'm definitely going to be late, probably around 30 to 45 minutes behind schedule. I didn't want you to worry about where I was. I'll call you again when I'm closer. Thanks for understanding!"
                
                elif "sick" in user_lower:
                    message = "Hi, this is calling to let you know that I'm feeling pretty unwell today and won't be able to make it in. I woke up with what feels like the flu and don't want to risk getting anyone else sick. I'm hoping to feel better by tomorrow, but I'll keep you updated. If there's anything urgent, you can reach me by email. Thanks for understanding."
                
                elif "appointment" in user_lower and ("reschedule" in user_lower or "change" in user_lower):
                    message = "Hello, this is calling about my appointment that's scheduled. I'm really sorry for the short notice, but I need to reschedule it due to an unexpected commitment that came up. I'm hoping we can find another time that works for both of us. Please give me a call back when you have a chance and we can figure out a new time. Thank you so much for understanding."
                
                elif "meeting" in user_lower:
                    message = "Hey there! I hope you're having a good day. I'm calling about our meeting that we planned. I just wanted to double check that we're still on for it and make sure the timing still works for you. If something came up on your end, no worries at all, we can always reschedule. Just let me know what works best for you."
                
                elif "reservation" in user_lower or "restaurant" in user_lower:
                    message = "Hello! I'm calling to make a dinner reservation if possible. I'm looking for a table for two people, ideally around 7 or 7:30 PM if you have availability. If those times don't work, I'm flexible with the timing. Could you let me know what you have open? Thank you so much."
                
                elif "doctor" in user_lower or "medical" in user_lower:
                    message = "Hello, this is calling about my upcoming appointment. I need to discuss some scheduling changes and wanted to see what options are available. Please give me a call back when you have a moment so we can work out the details. Thank you very much."
                
                elif "work" in user_lower or "office" in user_lower:
                    message = "Hi, this is calling about a work-related matter. I wanted to discuss something important and see when might be a good time to talk. Please give me a call back when you're available. Thanks so much."
                
                elif "friend" in user_lower or "family" in user_lower:
                    message = "Hey! I hope you're doing well. I just wanted to give you a quick call to catch up and see how things are going with you. I've been thinking about you and wanted to reach out. Give me a call back when you get a chance. Talk to you soon!"
                
                else:
                    message = f"Hi! I hope you're doing well. I'm calling about something important. {user_input} Please give me a call back when you have a chance so we can discuss this further. Thanks so much for your time."
            
            print(f"✅ Generated detailed voice message: {message[:50]}...")
            return message
            
        except Exception as e:
            print(f"❌ Voice generation error: {e}")
            return f"Hi! I hope you're doing well. I'm calling about the following: {user_input} Please give me a call back when you have a chance. Thanks so much."

# Global message generator instance
message_generator = MessageGenerator()

def generate_email_content(user_input: str, recipient: str = "", context: str = "") -> Dict[str, str]:
    """Generate email content"""
    return message_generator.generate_email_content(user_input, recipient, context)

def generate_whatsapp_message(user_input: str, recipient: str = "", context: str = "") -> str:
    """Generate WhatsApp message"""
    return message_generator.generate_whatsapp_message(user_input, recipient, context)

def generate_voice_message(user_input: str, recipient: str = "", context: str = "") -> str:
    """Generate voice message"""
    return message_generator.generate_voice_message(user_input, recipient, context)