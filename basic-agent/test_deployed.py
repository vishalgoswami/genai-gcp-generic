#!/usr/bin/env python3
"""
Test Deployed ADK Agent

This script tests a deployed ADK agent on Vertex AI Agent Engine.
ADK agents support specific operations like async_stream_query.

Reference: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/use/adk
"""

import vertexai
from vertexai import agent_engines
import asyncio

# Configuration
PROJECT_ID = "vg-pp-001"
LOCATION = "us-central1"

# Read the deployed resource name
try:
    with open("deployed_agent_resource.txt", "r") as f:
        RESOURCE_NAME = f.read().strip()
except FileNotFoundError:
    print("❌ Error: deployed_agent_resource.txt not found")
    print("Please deploy the agent first using: python deploy_from_source.py")
    exit(1)

print("="*70)
print("🧪 Testing Deployed ADK Agent")
print("="*70)
print(f"\nProject:       {PROJECT_ID}")
print(f"Location:      {LOCATION}")
print(f"Resource Name: {RESOURCE_NAME}")
print()


async def test_agent():
    """Test the deployed agent using ADK operations."""
    
    # Initialize Vertex AI
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    # Get the deployed agent
    print("📡 Connecting to deployed agent...")
    adk_app = agent_engines.get(RESOURCE_NAME)
    print("✓ Connected successfully!")
    print(f"  Agent type: {type(adk_app).__name__}")
    
    # List supported operations
    print("\n🔧 Supported Operations:")
    try:
        operations = adk_app.operation_schemas()
        # operation_schemas() returns a list, not a dict
        if isinstance(operations, list):
            for op in operations:
                if isinstance(op, dict) and 'name' in op:
                    print(f"  • {op['name']}")
                else:
                    print(f"  • {op}")
        elif isinstance(operations, dict):
            for op_name in operations.keys():
                print(f"  • {op_name}")
        else:
            print(f"  Operations: {operations}")
    except Exception as e:
        print(f"  (Could not retrieve operations: {e})")
    
    # Test 1: Create a session
    print("\n" + "="*70)
    print("Test 1: Create a new session")
    print("="*70)
    
    user_id = "test_user_001"
    
    try:
        session = await adk_app.async_create_session(user_id=user_id)
        session_id = session.get("id")
        print(f"✓ Session created successfully!")
        print(f"  User ID:    {user_id}")
        print(f"  Session ID: {session_id}")
    except Exception as e:
        print(f"✗ Failed to create session: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Stream a query (primary ADK operation)
    print("\n" + "="*70)
    print("Test 2: Stream a query to the agent (Server-Side Streaming)")
    print("="*70)
    
    test_queries = [
        "Hi! What's your name?",
        "Explain the concept of machine learning in detail, including supervised learning, unsupervised learning, reinforcement learning, and give examples of each. Make it comprehensive.",
        "List and explain 10 different types of neural networks used in deep learning.",
    ]
    
    for i, message in enumerate(test_queries, 1):
        print(f"\n📤 Query {i}: {message}")
        print(f"📥 Streaming Response:")
        print("-" * 70)
        
        try:
            # Use async_stream_query - the primary ADK operation
            # Reference: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/use/adk#stream-responses
            full_response = []
            chunk_count = 0
            total_chars = 0
            
            async for chunk in adk_app.async_stream_query(
                message=message,
                user_id=user_id,
                session_id=session_id,
            ):
                chunk_count += 1
                
                # Each chunk is a dictionary with content parts
                if isinstance(chunk, dict):
                    content = chunk.get("content", {})
                    parts = content.get("parts", [])
                    for part in parts:
                        if isinstance(part, dict) and "text" in part:
                            text = part["text"]
                            chunk_size = len(text)
                            total_chars += chunk_size
                            
                            # Show chunk metadata for first few chunks
                            if chunk_count <= 3:
                                print(f"\n[Chunk {chunk_count}: {chunk_size} chars]", flush=True)
                            
                            # Print the text immediately as received from server
                            print(text, end="", flush=True)
                            full_response.append(text)
            
            print()  # New line after response
            print("-" * 70)
            
            if not full_response:
                print("⚠️  Warning: No response text received")
            else:
                print(f"✓ Streaming complete!")
                print(f"  Total chunks received: {chunk_count}")
                print(f"  Total characters: {total_chars}")
                print(f"  Average chunk size: {total_chars // chunk_count if chunk_count > 0 else 0} chars")
                
        except Exception as e:
            print(f"\n✗ Query failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Test 3: List sessions
    print("\n" + "="*70)
    print("Test 3: List sessions for user")
    print("="*70)
    
    try:
        sessions = await adk_app.async_list_sessions(user_id=user_id)
        print(f"✓ Found {len(sessions)} session(s) for user {user_id}")
        for session in sessions:
            # Sessions can be either strings (session IDs) or dicts (session objects)
            if isinstance(session, str):
                print(f"  • Session ID: {session}")
            elif isinstance(session, dict):
                print(f"  • Session ID: {session.get('id', session)}")
            else:
                print(f"  • Session: {session}")
    except Exception as e:
        print(f"✗ Failed to list sessions: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Get specific session
    print("\n" + "="*70)
    print("Test 4: Get specific session")
    print("="*70)
    
    try:
        session = await adk_app.async_get_session(user_id=user_id, session_id=session_id)
        print(f"✓ Retrieved session {session_id}")
        print(f"  Turn count: {len(session.get('turns', []))}")
    except Exception as e:
        print(f"✗ Failed to get session: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Delete session
    print("\n" + "="*70)
    print("Test 5: Delete session")
    print("="*70)
    
    try:
        await adk_app.async_delete_session(user_id=user_id, session_id=session_id)
        print(f"✓ Session {session_id} deleted successfully")
    except Exception as e:
        print(f"✗ Failed to delete session: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ Testing Complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_agent())
