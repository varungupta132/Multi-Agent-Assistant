#!/usr/bin/env python3
"""
Safe project runner with error handling and diagnostics
"""
import sys
import os
import subprocess
import time

def check_ollama():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running with {len(models)} models")
            
            # Check if llama2 is available
            llama2_found = any('llama2' in model['name'] for model in models)
            if llama2_found:
                print("✅ llama2 model is available")
                return True
            else:
                print("⚠️ llama2 model not found")
                print("💡 Run: ollama pull llama2")
                return False
        else:
            print(f"⚠️ Ollama server returned HTTP {response.status_code}")
            return False
    except ImportError:
        print("❌ requests library not installed")
        print("💡 Run: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Ollama not running: {e}")
        print("💡 Run: ollama serve")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        ('flask', 'Flask'),
        ('twilio', 'Twilio'),
        ('langchain_ollama', 'LangChain Ollama'),
        ('langchain_core', 'LangChain Core'),
        ('requests', 'Requests')
    ]
    
    missing_packages = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name} is installed")
        except ImportError:
            print(f"❌ {name} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_config():
    """Check if configuration is valid"""
    try:
        sys.path.append('framework_multiagent')
        from config import (
            TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, 
            EMAIL_ADDRESS, EMAIL_PASSWORD,
            OLLAMA_MODEL
        )
        
        print("✅ Configuration loaded successfully")
        
        # Check if values are not empty
        if not TWILIO_ACCOUNT_SID or TWILIO_ACCOUNT_SID == 'your_account_sid':
            print("⚠️ Twilio Account SID not configured")
        
        if not TWILIO_AUTH_TOKEN or TWILIO_AUTH_TOKEN == 'your_auth_token':
            print("⚠️ Twilio Auth Token not configured")
        
        if not EMAIL_ADDRESS or '@' not in EMAIL_ADDRESS:
            print("⚠️ Email address not configured properly")
        
        if not EMAIL_PASSWORD:
            print("⚠️ Email password not configured")
        
        print(f"📋 Using Ollama model: {OLLAMA_MODEL}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def run_app():
    """Run the Flask application with error handling"""
    try:
        print("\n🚀 Starting Multi-Agent AI Framework...")
        print("🌐 Web interface will be available at: http://localhost:5000")
        print("⏹️ Press Ctrl+C to stop the server")
        print("-" * 60)
        
        # Import and run the app
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all files are in the correct location")
    except Exception as e:
        print(f"❌ Application error: {e}")
        print("💡 Check the error details above")

def main():
    """Main function to run diagnostics and start the app"""
    print("🔍 Multi-Agent AI Framework - Startup Diagnostics")
    print("=" * 60)
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        return
    
    # Check Ollama
    print("\n🤖 Checking Ollama...")
    ollama_ok = check_ollama()
    if not ollama_ok:
        print("\n⚠️ Ollama issues detected, but continuing...")
        print("   (The app will use fallback messages if Ollama fails)")
    
    # Check configuration
    print("\n⚙️ Checking Configuration...")
    if not check_config():
        print("\n❌ Configuration issues detected")
        print("💡 Please check framework_multiagent/config.py")
        return
    
    # All checks passed, run the app
    print("\n✅ All checks completed!")
    time.sleep(2)
    run_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Server stopped.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Please share this error message for help")