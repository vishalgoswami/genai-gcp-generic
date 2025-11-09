# ADK Agent Chat UI

Professional conversational interface for Google ADK Agent Engine built with Streamlit.

## Features

- 🤖 **Multi-Agent Support** - Select from all deployed agents in your project
- 💬 **Real-time Chat** - Streaming responses from Agent Engine
- 📊 **Session Management** - View and manage conversation sessions
- 🔄 **Auto-Discovery** - Automatically lists all deployed agents
- 📈 **Session Info** - Track conversation turns and session details
- 🎨 **Professional UI** - Clean, modern interface with custom styling

## Screenshots

### Main Chat Interface
- Real-time streaming responses
- Message history with timestamps
- User/Assistant message differentiation

### Sidebar Features
- Agent selection and switching
- Session information display
- Session management (new session, view all)
- Project configuration

## Setup

### 1. Install Dependencies

```bash
cd /Users/vishal/genai/1/frontend/streamlit
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
GCP_PROJECT_ID=vg-pp-001
GCP_LOCATION=us-central1
```

### 3. Authenticate with Google Cloud

```bash
gcloud auth application-default login
```

## Run the Application

```bash
# From the streamlit directory
streamlit run app.py

# Or specify port
streamlit run app.py --server.port 8501
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Select an Agent

1. Click "🔄 Refresh Agents" to load deployed agents
2. Click "Select" on an agent card to activate it
3. A new session will be created automatically

### Chat with Agent

1. Type your message in the chat input at the bottom
2. Press Enter to send
3. Watch the response stream in real-time

### Manage Sessions

- **New Session**: Click "🆕 New Session" to start fresh
- **View Sessions**: Expand "📋 View All Sessions" to see session history
- **Session Info**: Current session details shown in sidebar

### Switch Agents

1. Click "Select" on a different agent
2. Chat history will be cleared
3. New session created for new agent

## Architecture

```
┌─────────────────────────────────────────────┐
│         Streamlit Frontend (app.py)         │
│  ┌───────────────┐     ┌─────────────────┐ │
│  │   Sidebar     │     │   Main Chat     │ │
│  │               │     │                 │ │
│  │ • Agent List  │     │ • Messages      │ │
│  │ • Session Info│     │ • Input Field   │ │
│  │ • Config      │     │ • Streaming     │ │
│  └───────┬───────┘     └────────┬────────┘ │
└──────────┼──────────────────────┼──────────┘
           │                      │
           └──────────┬───────────┘
                      │
                      ↓
         ┌────────────────────────┐
         │   Vertex AI SDK        │
         │   (agent_engines)      │
         └────────────┬───────────┘
                      │
                      ↓
         ┌────────────────────────┐
         │  Vertex AI Agent       │
         │  Engine (Production)   │
         │                        │
         │  • Deployed Agents     │
         │  • Sessions            │
         │  • Streaming Responses │
         └────────────────────────┘
```

## Features in Detail

### Agent Discovery

The app automatically discovers all deployed agents in your GCP project:

```python
agents = agent_engines.list()
```

Displays:
- Agent display name
- Resource ID (last 12 characters)
- Create/update timestamps

### Session Management

**Create Session:**
```python
session = await agent.async_create_session(user_id=user_id)
```

**List Sessions:**
```python
sessions = await agent.async_list_sessions(user_id=user_id)
```

**Get Session Info:**
```python
session_info = await agent.async_get_session(user_id, session_id)
```

### Streaming Responses

Real-time streaming from Agent Engine:

```python
async for chunk in agent.async_stream_query(
    message=message,
    user_id=user_id,
    session_id=session_id,
):
    # Process and display chunks
```

## Customization

### Styling

Edit the CSS in the `st.markdown()` section of `app.py`:

```python
st.markdown("""
<style>
    .chat-message {
        /* Your custom styles */
    }
</style>
""", unsafe_allow_html=True)
```

### Configuration

Modify these constants in `app.py`:

```python
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "vg-pp-001")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
```

## Troubleshooting

### No Agents Found

- Ensure you have deployed agents using `deploy.py`
- Check project ID and location are correct
- Verify authentication: `gcloud auth application-default login`

### Connection Errors

- Verify Vertex AI API is enabled
- Check network connectivity
- Ensure correct GCP project permissions

### Session Not Created

- Check agent is properly deployed
- Verify user_id format
- Review Cloud Logs for errors

## Development

### Project Structure

```
frontend/streamlit/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
└── README.md          # This file
```

### Adding Features

1. **New UI Components**: Add to `render_chat_interface()` or `render_sidebar()`
2. **Agent Operations**: Extend async functions (create_session, etc.)
3. **Styling**: Update CSS in main `st.markdown()` block

## Requirements

- Python 3.9+
- Google Cloud SDK
- Deployed ADK agents in Vertex AI Agent Engine
- Application Default Credentials configured

## Links

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine)
- [Google ADK](https://google.github.io/adk-docs/)

## License

This UI connects to Google Cloud services subject to [Google Cloud Terms](https://cloud.google.com/terms).

---

**Built with ❤️ using Streamlit and Google ADK**
