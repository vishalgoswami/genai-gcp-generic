#!/usr/bin/env python3
"""
Google ADK-based Friendly Agent
Uses Google Agent Development Kit with Gemini 2.0 Flash and in-memory sessions
Supports dual safety modes: Vertex AI Safety Filters + Model Armor
Supports DLP for sensitive data detection and protection
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.genai import types
from safety_config import SafetyConfig, SafetyMode
from model_armor_scanner import ModelArmorScanner
from dlp_scanner import DLPScanner, DLPMode, DLPMethod, DLPResult

# Load environment variables
load_dotenv()

# Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "vg-pp-001")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash-exp")

# Set environment variables for Vertex AI
os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = GCP_LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

# Define comprehensive safety settings following Google Cloud best practices
# This implements a multi-layered security approach:
# 1. Input scanning: Detects harmful prompts, jailbreak attempts, prohibited content
# 2. Output filtering: Blocks unsafe responses based on harm categories
# 3. PII/SPII detection: Prevents leakage of personally identifiable information
safety_settings = [
    # Block hate speech content
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    # Block dangerous content (violence, weapons, etc.)
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    # Block harassment and bullying
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    # Block sexually explicit content
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
]

# Define the root agent using ADK with comprehensive safety features
root_agent = LlmAgent(
    model=MODEL_NAME,
    name="friendly_agent",
    description="A friendly and helpful AI assistant that provides warm, conversational responses.",
    instruction="""You are a friendly and helpful AI assistant. 
You provide clear, concise, and accurate responses while maintaining a warm and conversational tone.
You're knowledgeable, patient, and always aim to be helpful. 
Engage naturally with users and remember context from the conversation.""",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.9,
        top_p=0.95,
        top_k=40,
        max_output_tokens=2048,
        safety_settings=safety_settings,
    ),
)


class SafetyInfo:
    """Container for safety information from responses."""
    
    def __init__(self):
        self.is_blocked = False
        self.block_reason = None
        self.finish_reason = None
        self.safety_ratings = []
        self.prompt_blocked = False
        self.response_blocked = False
        # Model Armor results
        self.model_armor_prompt_result = None
        self.model_armor_response_result = None
        self.safety_mode = "vertex_ai"
        # DLP results
        self.dlp_prompt_result = None
        self.dlp_enabled = False
        
    def add_safety_rating(self, category: str, probability: str, severity: str = None, blocked: bool = False):
        """Add a safety rating."""
        self.safety_ratings.append({
            "category": category,
            "probability": probability,
            "severity": severity,
            "blocked": blocked
        })
        if blocked:
            self.is_blocked = True
            self.response_blocked = True
    
    def set_prompt_feedback(self, block_reason: str):
        """Set prompt feedback if input was blocked."""
        self.block_reason = block_reason
        self.prompt_blocked = True
        self.is_blocked = True
    
    def get_summary(self) -> str:
        """Get a human-readable summary of safety info."""
        if not self.is_blocked and not self.safety_ratings and not self.model_armor_prompt_result and not self.model_armor_response_result and not self.dlp_prompt_result:
            return None
        
        summary = []
        
        # Add safety mode indicator
        if self.safety_mode:
            mode_display = {
                "vertex_ai": "Vertex AI Safety Filters",
                "model_armor": "Model Armor Only",
                "both": "Vertex AI + Model Armor"
            }
            summary.append(f"🔒 Safety Mode: {mode_display.get(self.safety_mode, self.safety_mode)}")
        
        # DLP findings
        if self.dlp_prompt_result and self.dlp_prompt_result.has_findings:
            summary.append(f"🔍 DLP SCAN: {self.dlp_prompt_result.get_summary()}")
            if self.dlp_prompt_result.info_type_summary:
                summary.append(f"   Detected: {self.dlp_prompt_result.info_type_summary}")
        
        # Vertex AI blocks
        if self.prompt_blocked:
            summary.append(f"🛡️  INPUT BLOCKED (Vertex AI): {self.block_reason}")
            summary.append("   Reason: Your input was flagged for security concerns.")
            
            # Provide specific guidance based on block reason
            if self.block_reason == "PROHIBITED_CONTENT":
                summary.append("   This content violates content policy (e.g., CSAM).")
            elif self.block_reason == "JAILBREAK":
                summary.append("   Your input appears to attempt to bypass safety guidelines.")
            elif self.block_reason == "OTHER":
                summary.append("   Your input was blocked for policy violations.")
        
        if self.response_blocked:
            summary.append(f"🛡️  OUTPUT BLOCKED (Vertex AI): {self.finish_reason or 'SAFETY'}")
            summary.append("   Reason: The model's response was flagged for security concerns.")
            
            # Show which categories triggered
            for rating in self.safety_ratings:
                if rating.get('blocked'):
                    cat_name = rating['category'].replace('HARM_CATEGORY_', '')
                    summary.append(f"   - {cat_name}: {rating.get('probability', 'N/A')} probability")
        
        # Model Armor blocks
        if self.model_armor_prompt_result and self.model_armor_prompt_result.is_blocked:
            summary.append(f"🛡️  INPUT BLOCKED (Model Armor): {self.model_armor_prompt_result.block_reason}")
            summary.append(f"{self.model_armor_prompt_result.get_violation_summary()}")
        
        if self.model_armor_response_result and self.model_armor_response_result.is_blocked:
            summary.append(f"🛡️  OUTPUT BLOCKED (Model Armor): {self.model_armor_response_result.block_reason}")
            summary.append(f"{self.model_armor_response_result.get_violation_summary()}")
        
        # Safety ratings (if not blocked)
        if self.safety_ratings and not self.response_blocked:
            summary.append("ℹ️  SAFETY RATINGS (Vertex AI):")
            for rating in self.safety_ratings:
                cat_name = rating['category'].replace('HARM_CATEGORY_', '')
                prob = rating.get('probability', 'N/A')
                summary.append(f"   - {cat_name}: {prob}")
        
        # Model Armor violations (if not blocked)
        if self.model_armor_prompt_result and self.model_armor_prompt_result.has_violations() and not self.model_armor_prompt_result.is_blocked:
            summary.append("ℹ️  MODEL ARMOR DETECTIONS (Prompt):")
            summary.append(f"{self.model_armor_prompt_result.get_violation_summary()}")
        
        if self.model_armor_response_result and self.model_armor_response_result.has_violations() and not self.model_armor_response_result.is_blocked:
            summary.append("ℹ️  MODEL ARMOR DETECTIONS (Response):")
            summary.append(f"{self.model_armor_response_result.get_violation_summary()}")
        
        return '\n'.join(summary) if summary else None


class FriendlyAgentRunner:
    """Interactive runner for the friendly agent with in-memory session management."""
    
    def __init__(self, safety_config: SafetyConfig = None):
        """Initialize the agent runner with session service and safety configuration."""
        self.session_service = InMemorySessionService()
        self.app_name = "friendly_agent_app"
        self.user_id = "user_001"
        self.runner = Runner(
            app_name=self.app_name,
            agent=root_agent,
            session_service=self.session_service
        )
        self.session = None
        
        # Safety configuration with fallback
        self.safety_config = safety_config or SafetyConfig.from_env()
        self.model_armor_available = False  # Track if Model Armor is actually working
        
        # Initialize Model Armor scanner if needed
        self.model_armor_scanner = None
        if self.safety_config.requires_model_armor():
            try:
                self.model_armor_scanner = ModelArmorScanner(
                    project_id=GCP_PROJECT_ID,
                    location=GCP_LOCATION,
                    prompt_template_id=self.safety_config.model_armor_prompt_template,
                    response_template_id=self.safety_config.model_armor_response_template
                )
                if self.safety_config.enable_logging:
                    print(f"✓ Model Armor scanner initialized")
                    print(f"  Mode: {self.safety_config.mode.get_short_name()}")
            except Exception as e:
                if self.safety_config.enable_logging:
                    print(f"⚠️  Model Armor initialization failed: {e}")
                    if self.safety_config.auto_fallback:
                        print(f"⚠️  Falling back to Vertex AI only mode")
                        self.safety_config.mode = SafetyMode.VERTEX_AI_ONLY
                self.model_armor_scanner = None
        
        # Initialize DLP scanner if needed
        self.dlp_scanner = None
        if self.safety_config.dlp_enabled:
            try:
                # Convert config values to DLP enums
                dlp_mode = DLPMode[self.safety_config.dlp_mode.upper()] if self.safety_config.dlp_mode else DLPMode.INSPECT_ONLY
                dlp_method = DLPMethod[self.safety_config.dlp_method.upper()] if self.safety_config.dlp_method else DLPMethod.MASKING
                
                self.dlp_scanner = DLPScanner(
                    project_id=GCP_PROJECT_ID,
                    mode=dlp_mode,
                    method=dlp_method,
                    info_types=self.safety_config.dlp_info_types
                )
                if self.safety_config.enable_logging:
                    print(f"✓ DLP scanner initialized")
                    print(f"  Mode: {dlp_mode.value}")
                    print(f"  Method: {dlp_method.value}")
            except Exception as e:
                if self.safety_config.enable_logging:
                    print(f"⚠️  DLP initialization failed: {e}")
                    print(f"⚠️  Continuing without DLP protection")
                self.dlp_scanner = None

        
    async def initialize(self):
        """Initialize the session for the agent."""
        try:
            # Create a new session
            self.session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                state={}
            )
            print(f"✓ Connected to GCP project: {GCP_PROJECT_ID}")
            print(f"✓ Location: {GCP_LOCATION}")
            print(f"✓ Using model: {MODEL_NAME}")
            print(f"✓ Authentication: Application Default Credentials (ADC)")
            print(f"✓ Session ID: {self.session.id}")
            print(f"✓ Session Service: InMemorySessionService (ephemeral)")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize agent: {e}")
            print("\nMake sure you have:")
            print("1. Installed Google Cloud SDK")
            print("2. Run: gcloud auth application-default login")
            print("3. Set the correct project: gcloud config set project vg-pp-001")
            print("4. Enabled Vertex AI API: gcloud services enable aiplatform.googleapis.com")
            return False
    
    async def send_message(self, message: str) -> tuple[str, SafetyInfo]:
        """
        Send a message to the agent and get a response with safety information.
        
        Args:
            message: User's message
            
        Returns:
            Tuple of (agent's response, safety information)
        """
        safety_info = SafetyInfo()
        safety_info.safety_mode = self.safety_config.mode.value
        safety_info.dlp_enabled = self.safety_config.dlp_enabled
        
        # Original message for potential use
        original_message = message
        
        try:
            # Step 0: Scan message with DLP if enabled
            if self.safety_config.dlp_enabled and self.dlp_scanner:
                try:
                    dlp_result = self.dlp_scanner.process_text(message)
                    safety_info.dlp_prompt_result = dlp_result
                    
                    # Use the processed text (deidentified/redacted) for sending to LLM
                    # In INSPECT_ONLY mode, processed_text == original_text
                    message = dlp_result.processed_text
                    
                    if self.safety_config.enable_logging and dlp_result.has_findings:
                        print(f"🔍 DLP: {dlp_result.get_summary()}")
                        print(f"   Detected: {dlp_result.info_type_summary}")
                        
                except Exception as e:
                    # Fail-open: DLP errors should not block the conversation
                    if self.safety_config.enable_logging:
                        print(f"⚠️  DLP scan error: {e}")
                    # Continue with original message
                    message = original_message
            
            # Step 1: Scan prompt with Model Armor if required
            if self.safety_config.requires_model_armor() and self.model_armor_scanner:
                try:
                    ma_prompt_result = self.model_armor_scanner.scan_prompt(message)
                    safety_info.model_armor_prompt_result = ma_prompt_result
                    self.model_armor_available = True  # Mark as working
                    
                    if ma_prompt_result.is_blocked:
                        safety_info.prompt_blocked = True
                        safety_info.is_blocked = True
                        safety_info.prompt_feedback = f"Model Armor: {ma_prompt_result.block_reason}"
                        
                        # If Model Armor blocks, return immediately
                        return "⚠️  Your message was blocked by Model Armor due to safety concerns. Please rephrase your question.", safety_info
                except Exception as e:
                    # Handle Model Armor errors gracefully
                    if self.safety_config.enable_logging:
                        print(f"⚠️  Model Armor prompt scan error: {e}")
                    
                    # Mark Model Armor as unavailable
                    self.model_armor_available = False
                    
                    # Auto-fallback to Vertex AI only if enabled
                    if self.safety_config.auto_fallback and self.safety_config.mode == SafetyMode.MODEL_ARMOR_ONLY:
                        if self.safety_config.enable_logging:
                            print(f"⚠️  Falling back to Vertex AI only mode for this request")
                        # Don't permanently change mode, just skip Model Armor for this request
                    
                    # Fail-open: continue with Vertex AI if enabled
                    if not self.safety_config.fail_open:
                        raise

                        raise
            
            # Step 2: Create a Content object for the message
            user_message = types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
            
            # Step 3: Run the agent with the message (Vertex AI safety applied here if enabled)
            result_generator = self.runner.run(
                user_id=self.user_id,
                session_id=self.session.id,
                new_message=user_message
            )
            
            # Step 4: Iterate through the generator to get the final result and analyze Vertex AI safety
            final_result = None
            for event in result_generator:
                final_result = event
                
                # Check for Vertex AI safety information in the event
                if hasattr(event, 'safety_ratings'):
                    for rating in event.safety_ratings:
                        category = rating.category if hasattr(rating, 'category') else str(rating.get('category', 'UNKNOWN'))
                        probability = rating.probability if hasattr(rating, 'probability') else rating.get('probability', 'UNKNOWN')
                        severity = getattr(rating, 'severity', rating.get('severity', None))
                        blocked = getattr(rating, 'blocked', rating.get('blocked', False))
                        safety_info.add_safety_rating(str(category), str(probability), str(severity) if severity else None, blocked)
                
                # Check for blocked prompts (Vertex AI)
                if hasattr(event, 'prompt_feedback'):
                    prompt_feedback = event.prompt_feedback
                    if hasattr(prompt_feedback, 'block_reason') and prompt_feedback.block_reason:
                        vertex_ai_block_reason = str(prompt_feedback.block_reason)
                        # Append to existing feedback if Model Armor also flagged
                        if safety_info.prompt_feedback:
                            safety_info.prompt_feedback += f" | Vertex AI: {vertex_ai_block_reason}"
                        else:
                            safety_info.prompt_feedback = f"Vertex AI: {vertex_ai_block_reason}"
                
                # Check finish reason for blocked responses (Vertex AI)
                if hasattr(event, 'finish_reason'):
                    finish_reason = str(event.finish_reason) if event.finish_reason else None
                    safety_info.finish_reason = finish_reason
                    
                    # Mark as blocked if finish reason indicates safety block
                    if finish_reason in ['SAFETY', 'FINISH_REASON_SAFETY', 'SPII', 'FINISH_REASON_SPII', 
                                        'PROHIBITED_CONTENT', 'FINISH_REASON_PROHIBITED_CONTENT']:
                        safety_info.response_blocked = True
                        safety_info.is_blocked = True
            
            # Step 5: Extract the response text from the final event
            response_text = "No response received."
            
            if final_result:
                if hasattr(final_result, 'text'):
                    response_text = final_result.text
                elif hasattr(final_result, 'content'):
                    # Content object - extract text from parts
                    if hasattr(final_result.content, 'parts'):
                        text_parts = [part.text for part in final_result.content.parts if hasattr(part, 'text')]
                        response_text = ''.join(text_parts) if text_parts else str(final_result.content)
                    else:
                        response_text = str(final_result.content)
                elif hasattr(final_result, 'agent_output'):
                    response_text = final_result.agent_output
                else:
                    response_text = str(final_result)
            
            # Step 6: Scan response with Model Armor if required
            if self.safety_config.requires_model_armor() and self.model_armor_scanner and response_text and self.model_armor_available:
                try:
                    ma_response_result = self.model_armor_scanner.scan_response(response_text)
                    safety_info.model_armor_response_result = ma_response_result
                    
                    if ma_response_result.is_blocked:
                        safety_info.response_blocked = True
                        safety_info.is_blocked = True
                        response_text = "⚠️  The response was blocked by Model Armor due to safety concerns."
                except Exception as e:
                    # Handle Model Armor errors gracefully
                    if self.safety_config.enable_logging:
                        print(f"⚠️  Model Armor response scan error: {e}")
                    
                    # Mark as unavailable
                    self.model_armor_available = False
                    
                    # Fail-open: continue with response if enabled
                    if not self.safety_config.fail_open:
                        raise
            
            # Step 7: If response was blocked by Vertex AI, provide user-friendly message
            if safety_info.is_blocked:
                if safety_info.prompt_blocked and not safety_info.model_armor_prompt_result:
                    response_text = "⚠️  Your message was blocked by Vertex AI due to safety concerns. Please rephrase your question."
                elif safety_info.response_blocked and not safety_info.model_armor_response_result:
                    response_text = "⚠️  I cannot provide a response to this query due to Vertex AI safety policies."
            
            return response_text, safety_info
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Sorry, I encountered an error: {e}", safety_info
    
    async def clear_session(self):
        """Clear the current session and create a new one."""
        try:
            # Delete the old session
            await self.session_service.delete_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session.id
            )
            
            # Create a new session
            self.session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                state={}
            )
            print(f"✓ New session created: {self.session.id}\n")
        except Exception as e:
            print(f"✗ Error clearing session: {e}\n")
    
    async def show_history(self):
        """Display the conversation history from the session."""
        try:
            # Retrieve the current session to get latest events
            session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session.id
            )
            
            print("\n" + "="*60)
            print("Conversation History:")
            print("="*60)
            
            if not session.events:
                print("\nNo conversation history yet.")
            else:
                for event in session.events:
                    if hasattr(event, 'user_input') and event.user_input:
                        print(f"\nYou: {event.user_input}")
                    if hasattr(event, 'agent_output') and event.agent_output:
                        print(f"Agent: {event.agent_output}")
            
            print("\n" + "="*60 + "\n")
        except Exception as e:
            print(f"✗ Error retrieving history: {e}\n")
    
    async def run_interactive(self):
        """Run the agent in interactive mode."""
        print("\n" + "="*60)
        print("🤖 Friendly Agent - Powered by Google ADK & Gemini")
        print("="*60)
        print("\nType 'quit', 'exit', or 'bye' to end the conversation.")
        print("Type 'clear' to clear conversation history and start fresh.")
        print("Type 'history' to view conversation history.")
        print("Type 'session' to view session information.")
        print("\n" + "-"*60 + "\n")
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("\n👋 Goodbye! Have a great day!")
                    break
                
                if user_input.lower() == "clear":
                    await self.clear_session()
                    continue
                
                if user_input.lower() == "history":
                    await self.show_history()
                    continue
                
                if user_input.lower() == "session":
                    print(f"\n📋 Session Info:")
                    print(f"   Session ID: {self.session.id}")
                    print(f"   App Name: {self.app_name}")
                    print(f"   User ID: {self.user_id}")
                    print(f"   Last Updated: {self.session.last_update_time}\n")
                    continue
                
                # Get response from agent
                response, safety_info = await self.send_message(user_input)
                print(f"\nAgent: {response}\n")
                
                # Display safety information if available
                safety_summary = safety_info.get_summary()
                if safety_summary:
                    print("─" * 60)
                    print(safety_summary)
                    print("─" * 60 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n✗ Error: {e}\n")


async def main():
    """Main entry point for the agent."""
    runner = FriendlyAgentRunner()
    
    if not await runner.initialize():
        return
    
    await runner.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
