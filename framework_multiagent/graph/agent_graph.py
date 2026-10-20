"""
LangGraph Multi-Agent System
Orchestrates different agents based on task type
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.email_agent import send_email
from agents.call_agent import make_call
from agents.whatsapp_agent import send_whatsapp
from agents.task_agent import create_task, get_live_tasks, complete_task
from agents.flight_agent import book_flight_autonomous, search_flights, get_flight_bookings
from agents.music_agent import analyze_mood_and_play_music, get_music_library, get_playlist_history
from agents.mcq_agent import generate_mcq_questions, create_exam_session, analyze_mcq_question, scan_external_platform, get_mcq_statistics

from memory.task_memory import memory

class AgentState(TypedDict):
    """State shared between agents"""
    task_id: int
    task_type: str
    task_data: dict
    result: str
    error: str

def router(state: AgentState) -> Literal["email", "call", "whatsapp", "task", "flight", "music", "mcq", "unknown"]:
    """Route tasks to appropriate agents"""
    task_type = state["task_type"]
    print(f"🎯 Routing task {state['task_id']}: {task_type}")
    
    if task_type == "email":
        return "email"
    elif task_type == "call":
        return "call"
    elif task_type == "whatsapp":
        return "whatsapp"
    elif task_type == "task":
        return "task"
    elif task_type == "flight":
        return "flight"
    elif task_type == "music":
        return "music"
    elif task_type == "mcq":
        return "mcq"
    else:
        return "unknown"

def email_node(state: AgentState) -> AgentState:
    """Execute intelligent email tasks"""
    print(f"📧 Intelligent Email Agent processing task {state['task_id']}")
    
    try:
        task_data = state["task_data"]
        to = task_data.get("to", "")
        user_request = task_data.get("original_input", "")
        subject = task_data.get("subject", "")
        body = task_data.get("body", "")
        
        # Execute the intelligent email tool
        result = send_email.invoke({
            "to": to,
            "user_request": user_request,
            "subject": subject,
            "body": body
        })
        
        state["result"] = result
        
        # Update memory
        memory.mark_task_completed(state["task_id"], result)
        
    except Exception as e:
        error_msg = f"Intelligent email agent error: {str(e)}"
        state["error"] = error_msg
        memory.mark_task_failed(state["task_id"], error_msg)
    
    return state

def call_node(state: AgentState) -> AgentState:
    """Execute intelligent call tasks"""
    print(f"📞 Intelligent Call Agent processing task {state['task_id']}")
    
    try:
        task_data = state["task_data"]
        to = task_data.get("to", "")
        user_request = task_data.get("original_input", "")
        
        # Execute the intelligent call tool
        result = make_call.invoke({
            "to": to,
            "user_request": user_request
        })
        
        state["result"] = result
        
        # Update memory
        memory.mark_task_completed(state["task_id"], result)
        
    except Exception as e:
        error_msg = f"Intelligent call agent error: {str(e)}"
        state["error"] = error_msg
        memory.mark_task_failed(state["task_id"], error_msg)
    
    return state

def whatsapp_node(state: AgentState) -> AgentState:
    """Execute intelligent WhatsApp tasks"""
    print(f"📱 Intelligent WhatsApp Agent processing task {state['task_id']}")

    try:
        task_data = state["task_data"]
        to = task_data.get("to", "")
        user_request = task_data.get("original_input", "")
        message = task_data.get("message", "")

        # Execute the intelligent WhatsApp tool
        result = send_whatsapp.invoke({
            "to": to,
            "user_request": user_request,
            "message": message,
        })

        state["result"] = result

        # Update memory
        memory.mark_task_completed(state["task_id"], result)

    except Exception as e:
        error_msg = f"WhatsApp agent error: {str(e)}"
        state["error"] = error_msg
        memory.mark_task_failed(state["task_id"], error_msg)

    return state

def task_node(state: AgentState) -> AgentState:
    """Execute task management operations"""
    print(f"📋 Task Management Agent processing task {state['task_id']}")
    
    try:
        task_data = state["task_data"]
        operation = task_data.get("operation", "create")
        
        if operation == "create":
            task_name = task_data.get("task_name", "")
            task_description = task_data.get("task_description", "")
            deadline = task_data.get("deadline", "")
            
            result = create_task.invoke({
                "task_name": task_name,
                "task_description": task_description,
                "deadline": deadline
            })
            
        elif operation == "list":
            result = get_live_tasks.invoke({})
            
        elif operation == "complete":
            task_id = task_data.get("target_task_id", 0)
            result = complete_task.invoke({"task_id": task_id})
            
        else:
            result = "Unknown task operation"
        
        state["result"] = result
        
        # Update memory
        memory.mark_task_completed(state["task_id"], result)
        
    except Exception as e:
        error_msg = f"Task management agent error: {str(e)}"
        state["error"] = error_msg
        memory.mark_task_failed(state["task_id"], error_msg)
    
    return state

def flight_node(state: AgentState) -> AgentState:
    """Execute flight booking tasks"""
    print(f"✈️ Flight Booking Agent processing task {state['task_id']}")
    
    try:
        task_data = state["task_data"]
        operation = task_data.get("operation", "book")
        
        if operation == "book":
            user_request = task_data.get("original_input", "")
            passenger_name = task_data.get("passenger_name", "AI User")
            
            result = book_flight_autonomous.invoke({
                "user_request": user_request,
                "passenger_name": passenger_name
            })
            
        elif operation == "search":
            from_city = task_data.get("from_city", "")
            to_city = task_data.get("to_city", "")
            travel_date = task_data.get("travel_date", "")
            passengers = task_data.get("passengers", 1)
            
            result = search_flights.invoke({
                "from_city": from_city,
                "to_city": to_city,
                "travel_date": travel_date,
                "passengers": passengers
            })
            
        elif operation == "history":
            passenger_name = task_data.get("passenger_name", "")
            result = get_flight_bookings.invoke({"passenger_name": passenger_name})
            
        else:
            # Default autonomous booking
            user_request = task_data.get("original_input", "")
            result = book_flight_autonomous.invoke({
                "user_request": user_request,
                "passenger_name": "AI User"
            })
        
        state["result"] = result
        
        # Update memory
        memory.mark_task_completed(state["task_id"], result)
        
    except Exception as e:
        error_msg = f"Flight booking agent error: {str(e)}"
        state["error"] = error_msg
        memory.mark_task_failed(state["task_id"], error_msg)
    
    return state

def music_node(state: AgentState) -> AgentState:
    """Execute mood-aware music tasks"""
    print(f"🎵 Music Agent processing task {state['task_id']}")
    
    try:
        task_data = state["task_data"]
        operation = task_data.get("operation", "play")
        
        if operation == "play":
            user_mood_input = task_data.get("user_mood_input", "") or task_data.get("original_input", "")
            
            result = analyze_mood_and_play_music.invoke({
                "user_input": user_mood_input
            })
            
        elif operation == "library":
            result = get_music_library.invoke({})
            
        elif operation == "history":
            result = get_playlist_history.invoke({})
            
        else:
            # Default mood-based music playing
            user_mood_input = task_data.get("user_mood_input", "") or task_data.get("original_input", "")
            result = analyze_mood_and_play_music.invoke({
                "user_input": user_mood_input
            })
        
        state["result"] = result
        
        # Update memory
        memory.mark_task_completed(state["task_id"], result)
        
    except Exception as e:
        error_msg = f"Music agent error: {str(e)}"
        state["error"] = error_msg
        memory.mark_task_failed(state["task_id"], error_msg)
    
    return state

def mcq_node(state: AgentState) -> AgentState:
    """Execute MCQ Intelligence Platform tasks"""
    print(f"🧠 MCQ Intelligence Agent processing task {state['task_id']}")
    
    try:
        task_data = state["task_data"]
        operation = task_data.get("operation", "generate")
        
        if operation == "generate":
            topic = task_data.get("topic", "General Knowledge")
            difficulty = task_data.get("difficulty", "medium")
            count = task_data.get("count", 5)
            
            result = generate_mcq_questions.invoke({
                "topic": topic,
                "difficulty": difficulty,
                "count": count
            })
            
        elif operation == "create_exam":
            topic = task_data.get("topic", "General Knowledge")
            difficulty = task_data.get("difficulty", "medium")
            num_questions = task_data.get("num_questions", 10)
            user_name = task_data.get("user_name", "Anonymous")
            
            result = create_exam_session.invoke({
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": num_questions,
                "user_name": user_name
            })
            
        elif operation == "analyze":
            question_id = task_data.get("question_id", 1)
            
            result = analyze_mcq_question.invoke({
                "question_id": question_id
            })
            
        elif operation == "scan":
            platform_name = task_data.get("platform_name", "External Platform")
            topic = task_data.get("topic", "general")
            
            result = scan_external_platform.invoke({
                "platform_name": platform_name,
                "topic": topic
            })
            
        elif operation == "stats":
            result = get_mcq_statistics.invoke({})
            
        else:
            # Default: generate questions from original input
            original_input = task_data.get("original_input", "")
            
            # Try to extract topic from input
            topic = "General Knowledge"
            if "python" in original_input.lower():
                topic = "Python Programming"
            elif "machine learning" in original_input.lower() or "ml" in original_input.lower():
                topic = "Machine Learning"
            elif "data structure" in original_input.lower():
                topic = "Data Structures"
            elif "algorithm" in original_input.lower():
                topic = "Algorithms"
            
            result = generate_mcq_questions.invoke({
                "topic": topic,
                "difficulty": "medium",
                "count": 5
            })
        
        state["result"] = result
        
        # Update memory
        memory.mark_task_completed(state["task_id"], result)
        
    except Exception as e:
        error_msg = f"MCQ Intelligence agent error: {str(e)}"
        state["error"] = error_msg
        memory.mark_task_failed(state["task_id"], error_msg)
    
    return state

def unknown_node(state: AgentState) -> AgentState:
    """Handle unknown tasks"""
    print(f"❓ Unknown task type: {state['task_type']}")

    error_msg = f"Unknown task type: {state['task_type']}"
    state["error"] = error_msg
    memory.mark_task_failed(state["task_id"], error_msg)

    return state

# Create the LangGraph
def create_agent_graph():
    """Create and configure the multi-agent graph"""
    
    # Initialize the graph
    graph = StateGraph(AgentState)
    
    # Add nodes (agents)
    graph.add_node("email", email_node)
    graph.add_node("call", call_node)
    graph.add_node("whatsapp", whatsapp_node)
    graph.add_node("task", task_node)
    graph.add_node("flight", flight_node)
    graph.add_node("music", music_node)
    graph.add_node("mcq", mcq_node)
    graph.add_node("unknown", unknown_node)
    
    # Set conditional entry point (router)
    graph.set_conditional_entry_point(
        router,
        {
            "email": "email",
            "call": "call", 
            "whatsapp": "whatsapp",
            "task": "task",
            "flight": "flight",
            "music": "music",
            "mcq": "mcq",
            "unknown": "unknown"
        }
    )
    
    # All nodes end the graph
    graph.add_edge("email", END)
    graph.add_edge("call", END)
    graph.add_edge("whatsapp", END)
    graph.add_edge("task", END)
    graph.add_edge("flight", END)
    graph.add_edge("music", END)
    graph.add_edge("mcq", END)
    graph.add_edge("unknown", END)
    
    # Compile the graph
    return graph.compile()

# Global graph instance
agent_graph = create_agent_graph()

def execute_task(task_id: int, task_type: str, task_data: dict) -> dict:
    """Execute a task using the multi-agent graph"""
    print(f"\n🚀 Executing task {task_id}: {task_type}")
    print(f"📋 Data: {task_data}")
    
    # Create initial state
    initial_state = {
        "task_id": task_id,
        "task_type": task_type,
        "task_data": task_data,
        "result": "",
        "error": ""
    }
    
    # Execute the graph
    final_state = agent_graph.invoke(initial_state)
    
    print(f"✅ Task {task_id} execution completed")
    return final_state