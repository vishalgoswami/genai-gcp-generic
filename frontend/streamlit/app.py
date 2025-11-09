"""
Agent Engine Chat UI
Professional conversational interface for Google ADK Agent Engine
"""

import streamlit as st
import vertexai
from vertexai import agent_engines
import asyncio
from datetime import datetime
import os
import sys
from typing import Optional, Dict, Any
import json

# Add basic-agent to path for local agent support
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'basic-agent'))

# Try to import local agent with safety support
try:
    from agent import FriendlyAgentRunner
    from safety_config import SafetyConfig, SafetyMode
    LOCAL_AGENT_AVAILABLE = True
except ImportError:
    LOCAL_AGENT_AVAILABLE = False
    FriendlyAgentRunner = None
    SafetyConfig = None
    SafetyMode = None

# Page configuration
st.set_page_config(
    page_title="ADK Agent Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .message-time {
        font-size: 0.8rem;
        color: #999;
    }
    .stats-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .agent-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.3s;
    }
    .agent-card:hover {
        border-color: #2196f3;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .agent-card-selected {
        border-color: #2196f3;
        background-color: #e3f2fd;
    }
    .safety-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
    }
    .safety-blocked {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
    }
    .safety-info {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 0.8rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
    .safety-rating {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        margin: 0.2rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        background-color: #e9ecef;
    }
    .safety-rating-high {
        background-color: #f8d7da;
        color: #721c24;
    }
    .safety-rating-medium {
        background-color: #fff3cd;
        color: #856404;
    }

</style>
""", unsafe_allow_html=True)

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "vg-pp-001")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None
if "agent_list" not in st.session_state:
    st.session_state.agent_list = []
if "sessions_list" not in st.session_state:
    st.session_state.sessions_list = []
if "safety_mode" not in st.session_state:
    st.session_state.safety_mode = "vertex_ai"
if "use_local_agent" not in st.session_state:
    st.session_state.use_local_agent = False
if "local_agent_runner" not in st.session_state:
    st.session_state.local_agent_runner = None


def initialize_vertexai():
    """Initialize Vertex AI"""
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        return True
    except Exception as e:
        st.error(f"Failed to initialize Vertex AI: {e}")
        return False


def list_deployed_agents():
    """List all deployed agents in the project"""
    try:
        agents = agent_engines.list()
        agent_list = []
        for agent in agents:
            agent_info = {
                "resource_name": agent.gca_resource.name,
                "display_name": agent.gca_resource.display_name or "Unnamed Agent",
                "create_time": agent.gca_resource.create_time,
                "update_time": agent.gca_resource.update_time,
            }
            agent_list.append(agent_info)
        return agent_list
    except Exception as e:
        st.error(f"Failed to list agents: {e}")
        return []


async def create_session(agent, user_id: str):
    """Create a new session"""
    try:
        session = await agent.async_create_session(user_id=user_id)
        return session.get("id")
    except Exception as e:
        st.error(f"Failed to create session: {e}")
        return None


async def list_sessions(agent, user_id: str):
    """List all sessions for a user"""
    try:
        sessions = await agent.async_list_sessions(user_id=user_id)
        return sessions
    except Exception as e:
        st.error(f"Failed to list sessions: {e}")
        return []


async def get_session_info(agent, user_id: str, session_id: str):
    """Get detailed session information"""
    try:
        session = await agent.async_get_session(user_id=user_id, session_id=session_id)
        return session
    except Exception as e:
        st.error(f"Failed to get session info: {e}")
        return None


async def stream_agent_response(agent, message: str, user_id: str, session_id: str):
    """Stream response from agent and extract safety information"""
    response_placeholder = st.empty()
    full_response = []
    safety_info = {
        "is_blocked": False,
        "block_reason": None,
        "finish_reason": None,
        "safety_ratings": [],
        "prompt_blocked": False,
        "response_blocked": False
    }
    
    try:
        async for chunk in agent.async_stream_query(
            message=message,
            user_id=user_id,
            session_id=session_id,
        ):
            if isinstance(chunk, dict):
                # Extract content
                content = chunk.get("content", {})
                parts = content.get("parts", [])
                for part in parts:
                    if isinstance(part, dict) and "text" in part:
                        text = part["text"]
                        full_response.append(text)
                        # Update placeholder with accumulated response
                        response_placeholder.markdown("".join(full_response))
                
                # Extract safety ratings
                if "safety_ratings" in chunk:
                    for rating in chunk["safety_ratings"]:
                        safety_info["safety_ratings"].append({
                            "category": rating.get("category", "UNKNOWN"),
                            "probability": rating.get("probability", "UNKNOWN"),
                            "severity": rating.get("severity"),
                            "blocked": rating.get("blocked", False)
                        })
                        if rating.get("blocked"):
                            safety_info["response_blocked"] = True
                            safety_info["is_blocked"] = True
                
                # Extract prompt feedback for input blocking
                if "prompt_feedback" in chunk:
                    prompt_feedback = chunk["prompt_feedback"]
                    if "block_reason" in prompt_feedback:
                        safety_info["block_reason"] = prompt_feedback["block_reason"]
                        safety_info["prompt_blocked"] = True
                        safety_info["is_blocked"] = True
                
                # Extract finish reason
                if "finish_reason" in chunk:
                    finish_reason = chunk["finish_reason"]
                    safety_info["finish_reason"] = finish_reason
                    
                    # Check if finish reason indicates safety block
                    if finish_reason in ["SAFETY", "SPII", "PROHIBITED_CONTENT"]:
                        safety_info["response_blocked"] = True
                        safety_info["is_blocked"] = True
        
        final_response = "".join(full_response)
        
        # If response was blocked, provide user-friendly message
        if safety_info["is_blocked"]:
            if safety_info["prompt_blocked"]:
                final_response = "⚠️ Your message was blocked due to safety concerns. Please rephrase your question."
            elif safety_info["response_blocked"]:
                final_response = "⚠️ I cannot provide a response to this query due to safety policies."
        
        return final_response, safety_info
        
    except Exception as e:
        st.error(f"Failed to get response: {e}")
        return f"Error: {e}", safety_info


async def send_message_local_agent(message: str, safety_mode: str = "vertex_ai"):
    """Send message using local agent with configurable safety"""
    if not LOCAL_AGENT_AVAILABLE:
        st.error("Local agent not available. Using deployed agent instead.")
        return None, None
    
    try:
        # Get or create local agent runner
        if st.session_state.local_agent_runner is None or \
           st.session_state.local_agent_runner.safety_config.mode.value != safety_mode:
            # Create safety config based on mode
            mode_map = {
                "vertex_ai": SafetyMode.VERTEX_AI_ONLY,
                "model_armor": SafetyMode.MODEL_ARMOR_ONLY,
                "both": SafetyMode.BOTH
            }
            
            config = SafetyConfig(
                mode=mode_map.get(safety_mode, SafetyMode.VERTEX_AI_ONLY),
                model_armor_prompt_template=os.getenv("MODEL_ARMOR_PROMPT_TEMPLATE", ""),
                model_armor_response_template=os.getenv("MODEL_ARMOR_RESPONSE_TEMPLATE", ""),
                enable_logging=True,
                fail_open=True
            )
            
            # Create new runner
            runner = FriendlyAgentRunner(safety_config=config)
            
            # Initialize
            init_success = await runner.initialize()
            if not init_success:
                st.error("Failed to initialize local agent")
                return None, None
            
            st.session_state.local_agent_runner = runner
        
        runner = st.session_state.local_agent_runner
        
        # Send message
        response, safety_info_obj = await runner.send_message(message)
        
        # Convert SafetyInfo object to dict for compatibility
        safety_info = {
            "is_blocked": safety_info_obj.is_blocked,
            "block_reason": safety_info_obj.block_reason,
            "finish_reason": safety_info_obj.finish_reason,
            "safety_ratings": safety_info_obj.safety_ratings,
            "prompt_blocked": safety_info_obj.prompt_blocked,
            "response_blocked": safety_info_obj.response_blocked,
            "safety_mode": safety_info_obj.safety_mode,
            "model_armor_available": runner.model_armor_available,
        }
        
        # Add Model Armor results if available
        if safety_info_obj.model_armor_prompt_result:
            safety_info["model_armor_prompt_violations"] = len(safety_info_obj.model_armor_prompt_result.violations)
        if safety_info_obj.model_armor_response_result:
            safety_info["model_armor_response_violations"] = len(safety_info_obj.model_armor_response_result.violations)
        
        return response, safety_info
        
    except Exception as e:
        st.error(f"Local agent error: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None, None


def render_sidebar():
    """Render the sidebar with agent selection and session info"""
    with st.sidebar:
        st.markdown("### 🤖 Agent Selection")
        
        # Refresh agents button
        if st.button("🔄 Refresh Agents", use_container_width=True):
            st.session_state.agent_list = list_deployed_agents()
            st.rerun()
        
        # Load agents if not already loaded
        if not st.session_state.agent_list:
            st.session_state.agent_list = list_deployed_agents()
        
        # Display agents
        if st.session_state.agent_list:
            st.markdown(f"**Found {len(st.session_state.agent_list)} agent(s)**")
            
            for idx, agent_info in enumerate(st.session_state.agent_list):
                # Extract resource ID from full name
                resource_id = agent_info["resource_name"].split("/")[-1]
                display_name = agent_info["display_name"]
                
                # Create agent card
                is_selected = st.session_state.selected_agent == agent_info["resource_name"]
                card_class = "agent-card-selected" if is_selected else ""
                
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{display_name}**")
                        st.caption(f"ID: ...{resource_id[-12:]}")
                    with col2:
                        if st.button("Select", key=f"select_{idx}", use_container_width=True):
                            st.session_state.selected_agent = agent_info["resource_name"]
                            st.session_state.messages = []  # Clear chat history
                            st.session_state.session_id = None  # Reset session
                            st.rerun()
        else:
            st.info("No deployed agents found. Deploy an agent first.")
        
        st.markdown("---")
        
        # Session Information
        if st.session_state.selected_agent:
            st.markdown("### 📊 Session Info")
            
            st.markdown(f"**User ID:** `{st.session_state.user_id}`")
            
            if st.session_state.session_id:
                st.markdown(f"**Session ID:** `{st.session_state.session_id[-12:]}`")
                
                # Get session details
                try:
                    agent = agent_engines.get(st.session_state.selected_agent)
                    session_info = asyncio.run(get_session_info(
                        agent, 
                        st.session_state.user_id, 
                        st.session_state.session_id
                    ))
                    
                    if session_info:
                        turns = session_info.get("turns", [])
                        st.metric("Conversation Turns", len(turns))
                        
                        # Show create time if available
                        if "create_time" in session_info:
                            st.caption(f"Created: {session_info['create_time']}")
                except Exception as e:
                    st.caption(f"Session active")
            else:
                st.info("No active session")
            
            # New session button
            if st.button("🆕 New Session", use_container_width=True):
                st.session_state.session_id = None
                st.session_state.messages = []
                st.rerun()
            
            # List all sessions button
            with st.expander("📋 View All Sessions"):
                if st.button("Load Sessions", use_container_width=True):
                    try:
                        agent = agent_engines.get(st.session_state.selected_agent)
                        sessions = asyncio.run(list_sessions(agent, st.session_state.user_id))
                        st.session_state.sessions_list = sessions
                    except Exception as e:
                        st.error(f"Failed to load sessions: {e}")
                
                if st.session_state.sessions_list:
                    st.markdown(f"**Total Sessions:** {len(st.session_state.sessions_list)}")
                    for session in st.session_state.sessions_list:
                        if isinstance(session, str):
                            st.caption(f"• Session: {session[-12:]}")
                        else:
                            st.caption(f"• {session}")
        
        st.markdown("---")
        
        # Safety Configuration
        with st.expander("🛡️ Safety Configuration", expanded=True):
            st.markdown("### Agent Mode")
            
            # Agent mode selector (Local vs Deployed)
            if LOCAL_AGENT_AVAILABLE:
                use_local = st.checkbox(
                    "Use Local Agent with Safety Controls",
                    value=st.session_state.use_local_agent,
                    help="Enable to use local agent with configurable safety modes (Vertex AI + Model Armor)",
                    key="use_local_checkbox"
                )
                
                if use_local != st.session_state.use_local_agent:
                    st.session_state.use_local_agent = use_local
                    if not use_local:
                        # Clear local agent when switching back to deployed
                        st.session_state.local_agent_runner = None
                    st.rerun()
            else:
                st.info("💡 Local agent not available. Using deployed agent.")
                st.caption("To enable local agent with safety controls, ensure basic-agent is accessible.")
                st.session_state.use_local_agent = False
            
            # Only show safety mode selector if using local agent
            if st.session_state.use_local_agent and LOCAL_AGENT_AVAILABLE:
                st.markdown("---")
                st.markdown("### Safety Mode")
                
                # Safety mode selector
                safety_mode = st.selectbox(
                    "Select Safety Protection",
                    options=["Vertex AI Only (Default)", "Model Armor Only (Advanced)", "Both (Maximum Protection)"],
                    index=0,
                    help="Choose your safety protection level:\n"
                         "• Vertex AI Only: Fast, free, built-in Google safety filters\n"
                         "• Model Armor Only: Advanced URL/DLP/prompt injection detection (requires setup)\n"
                         "• Both: Maximum protection combining all safety features",
                    key="safety_mode_selector"
                )
                
                # Map selection to mode value
                mode_mapping = {
                    "Vertex AI Only (Default)": "vertex_ai",
                    "Model Armor Only (Advanced)": "model_armor",
                    "Both (Maximum Protection)": "both"
                }
                selected_mode = mode_mapping[safety_mode]
                
                if selected_mode != st.session_state.safety_mode:
                    st.session_state.safety_mode = selected_mode
                    # Clear runner to force recreation with new mode
                    st.session_state.local_agent_runner = None
                    st.info(f"✓ Safety mode changed to: {safety_mode}")
                
                # Show current mode info
                st.markdown("---")
                st.markdown("**Current Protection:**")
                if selected_mode == "vertex_ai":
                    st.success("✓ Vertex AI Safety (Free & Fast)")
                    st.caption("Hate speech, harassment, dangerous content, PII detection")
                elif selected_mode == "model_armor":
                    st.warning("⚠️ Model Armor (Requires API Access)")
                    st.caption("URL detection, DLP, prompt injection, advanced security")
                else:  # both
                    st.success("✓ Maximum Protection")
                    st.caption("Vertex AI + Model Armor combined")
                
                # Model Armor status
                if selected_mode in ["model_armor", "both"]:
                    st.markdown("---")
                    st.markdown("**Model Armor Status:**")
                    
                    # Check if Model Armor templates are configured
                    model_armor_template = os.getenv("MODEL_ARMOR_PROMPT_TEMPLATE", "")
                    if model_armor_template:
                        st.info(f"✓ Template configured")
                        st.caption(f"Using: {model_armor_template.split('/')[-1]}")
                    else:
                        st.error("✗ No template configured")
                        st.caption("Set MODEL_ARMOR_PROMPT_TEMPLATE in .env")
                        st.caption("Will fallback to Vertex AI only")
            else:
                st.caption("Using deployed agent with default Vertex AI safety")
        
        st.markdown("---")
        
        # Configuration
        with st.expander("⚙️ Project Configuration"):
            st.markdown(f"**Project:** {PROJECT_ID}")
            st.markdown(f"**Location:** {LOCATION}")
            st.caption("Set via environment variables")


def render_safety_info(safety_info: Dict[str, Any]) -> str:
    """Render safety information as HTML"""
    if not safety_info:
        return ""
    
    html = []
    
    # Safety mode indicator
    if safety_info.get("safety_mode"):
        mode_icons = {
            "vertex_ai": "🛡️ Vertex AI",
            "model_armor": "🔒 Model Armor",
            "both": "🛡️🔒 Vertex AI + Model Armor"
        }
        mode_text = mode_icons.get(safety_info["safety_mode"], safety_info["safety_mode"])
        html.append(f"""
        <div style="background-color: #e8f4f8; padding: 0.5rem; border-radius: 0.3rem; margin-bottom: 0.5rem; font-size: 0.85rem;">
            <strong>Protection:</strong> {mode_text}
            {' ✓ Model Armor Active' if safety_info.get("model_armor_available") else ''}
        </div>
        """)
    
    # Blocked content warning
    if safety_info.get("is_blocked"):
        if safety_info.get("prompt_blocked"):
            html.append(f"""
            <div class="safety-blocked">
                🛡️ <strong>INPUT BLOCKED:</strong> {safety_info.get("block_reason", "UNKNOWN")}
                <br><small>Your input was flagged for security concerns. Please rephrase your question.</small>
            </div>
            """)
        elif safety_info.get("response_blocked"):
            html.append(f"""
            <div class="safety-blocked">
                🛡️ <strong>OUTPUT BLOCKED:</strong> {safety_info.get("finish_reason", "SAFETY")}
                <br><small>The response was flagged for security concerns and cannot be displayed.</small>
            </div>
            """)
    
    # Model Armor violations
    if safety_info.get("model_armor_prompt_violations") or safety_info.get("model_armor_response_violations"):
        violations_html = ['<div class="safety-info">🔒 <strong>Model Armor Scan:</strong><br>']
        
        if safety_info.get("model_armor_prompt_violations", 0) > 0:
            violations_html.append(f'<span class="safety-rating safety-rating-high">Prompt: {safety_info["model_armor_prompt_violations"]} violations detected</span>')
        
        if safety_info.get("model_armor_response_violations", 0) > 0:
            violations_html.append(f'<span class="safety-rating safety-rating-high">Response: {safety_info["model_armor_response_violations"]} violations detected</span>')
        
        violations_html.append('</div>')
        html.append(''.join(violations_html))
    
    # Safety ratings (Vertex AI)
    if safety_info.get("safety_ratings"):
        ratings_html = ['<div class="safety-info">🛡️ <strong>Vertex AI Safety Ratings:</strong><br>']
        
        for rating in safety_info["safety_ratings"]:
            category = rating.get("category", "UNKNOWN").replace("HARM_CATEGORY_", "")
            probability = rating.get("probability", "UNKNOWN")
            severity = rating.get("severity", "")
            blocked = rating.get("blocked", False)
            
            # Determine CSS class based on probability
            rating_class = "safety-rating"
            if probability in ["HIGH", "MEDIUM"]:
                rating_class += f" safety-rating-{probability.lower()}"
            
            rating_text = f"{category}: {probability}"
            if severity:
                rating_text += f" (Severity: {severity.replace('HARM_SEVERITY_', '')})"
            if blocked:
                rating_text += " ⚠️ BLOCKED"
            
            ratings_html.append(f'<span class="{rating_class}">{rating_text}</span>')
        
        ratings_html.append('</div>')
        html.append(''.join(ratings_html))
    
    return ''.join(html)


def render_chat_interface():
    """Render the main chat interface"""
    # Header
    st.markdown('<div class="main-header">🤖 ADK Agent Chat</div>', unsafe_allow_html=True)
    
    # Check if we can start chatting (either local agent or deployed agent selected)
    can_chat = st.session_state.use_local_agent or st.session_state.selected_agent
    
    if not can_chat:
        st.markdown('<div class="sub-header">Select an agent from the sidebar to start chatting</div>', unsafe_allow_html=True)
        
        # Show welcome message
        if LOCAL_AGENT_AVAILABLE:
            st.info("👈 Choose a deployed agent from the sidebar OR enable 'Use Local Agent' to begin your conversation.")
        else:
            st.info("👈 Choose a deployed agent from the sidebar to begin your conversation.")
        
        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Available Agents", len(st.session_state.agent_list))
        with col2:
            st.metric("Active Sessions", 0)
        with col3:
            st.metric("Messages Sent", 0)
        
        return
    
    # Display selected agent info
    if st.session_state.use_local_agent:
        st.markdown(f'<div class="sub-header">Chatting with: Local Agent ({st.session_state.safety_mode.replace("_", " ").title()})</div>', unsafe_allow_html=True)
    elif st.session_state.selected_agent:
        selected_agent_info = next(
            (a for a in st.session_state.agent_list if a["resource_name"] == st.session_state.selected_agent),
            None
        )
        
        if selected_agent_info:
            st.markdown(f'<div class="sub-header">Chatting with: {selected_agent_info["display_name"]}</div>', unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        message_class = "user-message" if message["role"] == "user" else "assistant-message"
        icon = "👤" if message["role"] == "user" else "🤖"
        
        message_html = f"""
        <div class="chat-message {message_class}">
            <div class="message-header">
                <span>{icon} {message["role"].title()}</span>
                <span class="message-time">{message.get("timestamp", "")}</span>
            </div>
            <div>{message["content"]}</div>
        """
        
        # Add safety information if present
        safety_info = message.get("safety_info")
        if safety_info and (safety_info.get("is_blocked") or safety_info.get("safety_ratings")):
            message_html += render_safety_info(safety_info)
        
        message_html += "</div>"
        st.markdown(message_html, unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": timestamp
        })
        
        # Display user message immediately
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="message-header">
                <span>👤 User</span>
                <span class="message-time">{timestamp}</span>
            </div>
            <div>{prompt}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Get and display assistant response
        with st.spinner("🤔 Thinking..."):
            # Choose agent based on mode
            if st.session_state.use_local_agent and LOCAL_AGENT_AVAILABLE:
                # Use local agent with safety configuration
                response, safety_info = asyncio.run(send_message_local_agent(
                    prompt,
                    st.session_state.safety_mode
                ))
                
                if response is None:
                    # Fallback to deployed agent if local agent fails and deployed agent is available
                    if st.session_state.selected_agent:
                        st.warning("Local agent failed, falling back to deployed agent")
                        agent = agent_engines.get(st.session_state.selected_agent)
                        
                        # Create session if needed
                        if not st.session_state.session_id:
                            session_id = asyncio.run(create_session(agent, st.session_state.user_id))
                            st.session_state.session_id = session_id
                        
                        response, safety_info = asyncio.run(stream_agent_response(
                            agent,
                            prompt,
                            st.session_state.user_id,
                            st.session_state.session_id
                        ))
                    else:
                        st.error("Local agent failed and no deployed agent selected.")
                        return
            else:
                # Use deployed agent
                agent = agent_engines.get(st.session_state.selected_agent)
                
                # Create session if needed
                if not st.session_state.session_id:
                    session_id = asyncio.run(create_session(agent, st.session_state.user_id))
                    st.session_state.session_id = session_id
                
                response, safety_info = asyncio.run(stream_agent_response(
                    agent,
                    prompt,
                    st.session_state.user_id,
                    st.session_state.session_id
                ))
        
        # Add assistant message with safety info
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": timestamp,
            "safety_info": safety_info
        })
        
        st.rerun()


def main():
    """Main application"""
    # Initialize Vertex AI
    if not initialize_vertexai():
        st.error("Please configure your Google Cloud credentials")
        st.stop()
    
    # Render UI
    render_sidebar()
    render_chat_interface()
    
    # Footer
    st.markdown("---")
    st.caption("Powered by Google ADK & Vertex AI Agent Engine")


if __name__ == "__main__":
    main()
