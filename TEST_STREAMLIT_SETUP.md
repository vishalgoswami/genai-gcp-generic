# Streamlit App Setup - Local Agent + Safety Modes

## Current Implementation

Your Streamlit app (`frontend/streamlit/app.py`) already has both features you requested:

### ✅ Feature 1: Local Agent vs Deployed Agent Toggle

**Location:** Sidebar → Safety Configuration section

**UI Component:**
- Checkbox: "Use Local Agent with Safety Controls"
- **Unchecked (default)**: Uses Agent Engine deployed agent
- **Checked**: Uses local `basic-agent/agent.py` with full safety controls

**Use Cases:**
- **Deployed Agent**: For production use, faster, uses your deployed agent
- **Local Agent**: For testing UI changes before deploying to Agent Engine

### ✅ Feature 2: Safety Mode Selector

**Location:** Sidebar → Safety Configuration section (only visible when local agent is enabled)

**UI Component:**
- Dropdown: "Select Safety Protection"
- **Options:**
  1. **Vertex AI Only (Default)** - Fast, free, built-in Google safety
  2. **Model Armor Only (Advanced)** - Advanced security (URL, DLP, prompt injection)
  3. **Both (Maximum Protection)** - Combined Vertex AI + Model Armor

**How It Works:**

```
┌─────────────────────────────────────┐
│  Agent Mode Selection               │
├─────────────────────────────────────┤
│  □ Use Local Agent                  │  ← Unchecked = Deployed Agent
│                                     │
│  When checked:                      │
│  ▼ Select Safety Protection         │  ← Dropdown appears
│    • Vertex AI Only (Default)       │
│    • Model Armor Only (Advanced)    │
│    • Both (Maximum Protection)      │
│                                     │
│  Status: ✓ Vertex AI Safety Active │
└─────────────────────────────────────┘
```

## How to Use

### Option 1: Test with Local Agent (Before Deployment)

1. **Open Streamlit sidebar**
2. **Check** "Use Local Agent with Safety Controls"
3. **Select safety mode** from dropdown:
   - Start with "Vertex AI Only" for basic testing
   - Use "Both" when Model Armor API access is available
4. **Send messages** - they go through your local `basic-agent/agent.py`
5. **See safety info** in response with selected protection mode

### Option 2: Use Deployed Agent (Production)

1. **Keep checkbox unchecked** (default)
2. **Select your deployed agent** from agent list
3. **Send messages** - they go through Agent Engine
4. **See Vertex AI safety info** (default deployed agent safety)

## Testing Flow

```bash
# 1. Start Streamlit
cd /Users/vishal/genai/1
source .venv/bin/activate
streamlit run frontend/streamlit/app.py

# 2. In browser (http://localhost:8501):
#    - Test with deployed agent first (checkbox unchecked)
#    - Then enable local agent (check the box)
#    - Try different safety modes
#    - Compare results
```

## Code Structure

### Session State Variables
```python
st.session_state.use_local_agent      # True/False - which agent to use
st.session_state.safety_mode          # "vertex_ai"/"model_armor"/"both"
st.session_state.local_agent_runner   # Local agent instance
```

### Message Routing (lines 730-755)
```python
if st.session_state.use_local_agent and LOCAL_AGENT_AVAILABLE:
    # Use local agent with safety configuration
    response, safety_info = send_message_local_agent(
        prompt,
        st.session_state.safety_mode  # ← Selected mode
    )
else:
    # Use deployed agent
    response, safety_info = stream_agent_response(
        agent,
        prompt,
        st.session_state.user_id,
        st.session_state.session_id
    )
```

### Safety Config Creation (lines 304-340)
```python
mode_map = {
    "vertex_ai": SafetyMode.VERTEX_AI_ONLY,
    "model_armor": SafetyMode.MODEL_ARMOR_ONLY,
    "both": SafetyMode.BOTH
}

config = SafetyConfig(
    mode=mode_map.get(safety_mode, SafetyMode.VERTEX_AI_ONLY),
    model_armor_prompt_template=os.getenv("MODEL_ARMOR_PROMPT_TEMPLATE", ""),
    model_armor_response_template=os.getenv("MODEL_ARMOR_RESPONSE_TEMPLATE", ""),
    safety_logging=True,
    safety_fail_open=True
)
```

## Benefits

### ✅ Separation of Concerns
- **Deployed Agent**: Production, stable, uses Agent Engine infrastructure
- **Local Agent**: Development, testing, full control over safety settings

### ✅ Testing Before Deployment
- Test UI changes with local agent
- Verify safety modes work correctly
- Try different configurations
- Deploy only when satisfied

### ✅ Flexible Safety
- Quick toggle between safety levels
- Easy to compare Vertex AI vs Model Armor
- Graceful fallback if Model Armor unavailable

### ✅ Clear Visual Feedback
- Protection mode shown in responses
- Safety status visible in sidebar
- Model Armor configuration status
- Fallback warnings if needed

## Next Steps

1. **Test the current implementation**:
   ```bash
   streamlit run frontend/streamlit/app.py
   ```

2. **Try both modes**:
   - Send messages with deployed agent
   - Enable local agent checkbox
   - Select different safety modes
   - Compare the results

3. **Check safety display**:
   - Look for protection indicators (🛡️ Vertex AI, 🔒 Model Armor)
   - Verify safety ratings appear
   - Test blocked content handling

4. **When ready to deploy**:
   - Test thoroughly with local agent
   - Once satisfied, deploy to Agent Engine
   - Use deployed agent for production

## Current Status

✅ **Local Agent Support**: Implemented and ready  
✅ **Safety Mode Selector**: Implemented with 3 options  
✅ **Graceful Fallback**: Local agent errors fallback to deployed  
✅ **Visual Feedback**: Safety info display with mode indicators  
⚠️ **Model Armor API**: Still has 403 error (will auto-fallback to Vertex AI)

## Summary

**Your Streamlit app already has everything you requested!** 

The implementation provides:
1. ✅ Option to use local agent (checkbox in sidebar)
2. ✅ Separate safety mode selector (dropdown with 3 options)
3. ✅ Testing capability before Agent Engine deployment

Just run the app and toggle the checkbox to switch between local and deployed agents, then select your preferred safety mode when using the local agent.
