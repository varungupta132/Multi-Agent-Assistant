#!/usr/bin/env python3
"""
Multi-Agent Framework Main Application
Industry-grade AI agent architecture using LangChain + LangGraph + Ollama
"""
import sys
import os
import time
import threading
from typing import Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm.task_parser import parse_task
from memory.task_memory import memory
from followup.scheduler import scheduler, start_scheduler, stop_scheduler, process_task_immediately
from graph.agent_graph import agent_graph

class MultiAgentFramework:
    def __init__(self):
        """Initialize the multi-agent framework"""
        print("🚀 Initializing Multi-Agent Framework...")
        print("=" * 60)
        
        self.running = False
        self._check_dependencies()
        
        print("✅ Multi-Agent Framework Ready!")
        print("=" * 60)

    def _check_dependencies(self):
        """Check if all dependencies are working"""
        try:
            # Test Ollama connection
            from llm.task_parser import parser
            test_result = parser.parse_task("test")
            print("✅ Ollama LLM connection working")
            
            # Test database
            stats = memory.get_stats()
            print(f"✅ Database working (Total tasks: {stats['total']})")
            
            # Test agent graph
            print("✅ LangGraph multi-agent system ready")
            
        except Exception as e:
            print(f"❌ Dependency check failed: {e}")
            raise

    def start(self):
        """Start the framework with background scheduler"""
        if self.running:
            print("⚠️ Framework already running")
            return
        
        self.running = True
        start_scheduler()
        print("🎯 Multi-Agent Framework started with background processing")

    def stop(self):
        """Stop the framework"""
        self.running = False
        stop_scheduler()
        print("⏹️ Multi-Agent Framework stopped")

    def process_user_input(self, user_input: str, immediate: bool = True) -> Dict[str, Any]:
        """
        Process user input through the complete pipeline
        
        Args:
            user_input: Natural language input from user
            immediate: If True, process immediately. If False, add to queue
        
        Returns:
            Result dictionary with task info and execution result
        """
        print(f"\n🎤 User Input: '{user_input}'")
        
        try:
            # Step 1: Parse with LLM
            parsed_data = parse_task(user_input)
            task_type = parsed_data.get('task', 'unknown')
            
            if task_type == 'unknown':
                return {
                    'success': False,
                    'error': 'Could not understand the request',
                    'parsed_data': parsed_data
                }
            
            # Step 2: Add to memory with original input
            parsed_data["original_input"] = user_input  # Add original input for context
            task_id = memory.add_task(task_type, parsed_data)
            
            # Step 3: Execute immediately or queue for later
            if immediate:
                print("⚡ Processing immediately...")
                success = process_task_immediately(task_id, task_type, parsed_data)
                
                return {
                    'success': success,
                    'task_id': task_id,
                    'task_type': task_type,
                    'parsed_data': parsed_data,
                    'execution_mode': 'immediate'
                }
            else:
                print("📋 Added to processing queue...")
                return {
                    'success': True,
                    'task_id': task_id,
                    'task_type': task_type,
                    'parsed_data': parsed_data,
                    'execution_mode': 'queued'
                }
                
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def get_status(self) -> Dict[str, Any]:
        """Get framework status"""
        scheduler_status = scheduler.get_status()
        return {
            'framework_running': self.running,
            'scheduler': scheduler_status,
            'recent_tasks': memory.get_task_history(5)
        }

    def interactive_mode(self):
        """Run in interactive mode"""
        print("\n" + "="*60)
        print("🎤 MULTI-AGENT FRAMEWORK - INTERACTIVE MODE")
        print("="*60)
        print("🗣️ Commands:")
        print("   📧 'Send email to john@gmail.com saying hello'")
        print("   📱 'WhatsApp to +917318018232 saying meeting tomorrow'")
        print("   📞 'Call +917318018232'")
        print("   📊 'status' - Show framework status")
        print("   📋 'history' - Show recent tasks")
        print("   🚪 'quit' - Exit")
        print("="*60)
        
        # Start background processing
        self.start()
        
        try:
            while True:
                user_input = input("\n🎯 Enter command: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'status':
                    status = self.get_status()
                    print(f"\n📊 Framework Status:")
                    print(f"   Running: {status['framework_running']}")
                    print(f"   Scheduler: {status['scheduler']['running']}")
                    print(f"   Tasks: {status['scheduler']['task_stats']}")
                
                elif user_input.lower() == 'history':
                    history = memory.get_task_history(10)
                    print(f"\n📋 Recent Tasks ({len(history)}):")
                    for task in history:
                        status_icon = "✅" if task['status'] == 'completed' else "❌" if task['status'] == 'failed' else "⏳"
                        print(f"   {status_icon} [{task['id']}] {task['task_type']} - {task['status']}")
                
                else:
                    # Process the command
                    result = self.process_user_input(user_input, immediate=True)
                    
                    if result['success']:
                        print(f"✅ Task {result['task_id']} ({result['task_type']}) processed successfully!")
                    else:
                        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        finally:
            self.stop()

def main():
    """Main function"""
    print("🚀 Starting Multi-Agent Framework...")
    
    try:
        # Initialize framework
        framework = MultiAgentFramework()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            # Process single command
            command = ' '.join(sys.argv[1:])
            framework.start()
            result = framework.process_user_input(command, immediate=True)
            
            if result['success']:
                print(f"✅ Command executed successfully!")
            else:
                print(f"❌ Command failed: {result.get('error', 'Unknown error')}")
            
            framework.stop()
        else:
            # Interactive mode
            framework.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()