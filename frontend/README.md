# ADK Agent Frontend Applications

Professional user interfaces for interacting with Google ADK Agent Engine.

## Available Frontends

### 🎨 Streamlit Chat UI

Professional conversational interface with real-time streaming.

**Location:** `streamlit/`

**Features:**
- Multi-agent support
- Real-time streaming responses
- Session management
- Auto-discovery of deployed agents
- Professional UI with custom styling

**Quick Start:**
```bash
cd streamlit
./run.sh
```

Or manually:
```bash
cd streamlit
pip install -r requirements.txt
streamlit run app.py
```

**Access:** http://localhost:8501

## Requirements

- Python 3.9+
- Google Cloud SDK
- Application Default Credentials
- Deployed ADK agents in Vertex AI Agent Engine

## Authentication

```bash
gcloud auth application-default login
gcloud config set project vg-pp-001
```

## Project Structure

```
frontend/
├── streamlit/           # Streamlit chat UI
│   ├── app.py          # Main application
│   ├── requirements.txt # Dependencies
│   ├── run.sh          # Launch script
│   ├── .env           # Configuration
│   └── README.md       # Documentation
└── README.md           # This file
```

## Adding New Frontends

Future frontend options could include:
- **Gradio** - Alternative web UI framework
- **Flask/FastAPI** - Custom REST API + React frontend
- **Terminal UI** - Rich terminal interface with textual
- **Slack Bot** - Integration with Slack
- **Discord Bot** - Integration with Discord

## Development

Each frontend is self-contained with its own:
- `requirements.txt` - Python dependencies
- `README.md` - Specific documentation
- `.env.example` - Configuration template
- Launch scripts

## Links

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google ADK](https://google.github.io/adk-docs/)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine)

---

**Choose your preferred frontend and start chatting!** 🚀
