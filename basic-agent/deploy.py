#!/usr/bin/env python3
"""
Deploy Friendly Agent to Vertex AI Agent Engine

This script deploys the friendly agent to Vertex AI Agent Engine using the
official ADK deployment method from:
https://docs.cloud.google.com/agent-builder/agent-engine/deploy

Uses agent object deployment with source files packaged via extra_packages.
"""

import vertexai
from vertexai import agent_engines
import sys
import os

# Configuration - Update these values for your deployment
PROJECT_ID = "vg-pp-001"
LOCATION = "us-central1"  # Supported regions: us-central1, europe-west1, asia-northeast1
DISPLAY_NAME = "Friendly Agent (Source Deploy)"


def deploy_agent():
    """Deploy the agent to Vertex AI Agent Engine."""
    
    print("="*70)
    print("🚀 Deploying Friendly Agent to Vertex AI Agent Engine")
    print("="*70)
    
    # Step 1: Import the agent
    print(f"\n📋 Step 1: Importing agent from agent.py")
    
    try:
        from agent import root_agent
        print(f"  ✓ Successfully imported root_agent")
        print(f"  Agent type:  {type(root_agent).__name__}")
        print(f"  Agent name:  {root_agent.name}")
        print(f"  Model:       {root_agent.model}")
    except Exception as e:
        print(f"  ✗ Failed to import agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 2: Initialize Vertex AI
    print(f"\n� Step 2: Initializing Vertex AI")
    print(f"  Project ID:      {PROJECT_ID}")
    print(f"  Location:        {LOCATION}")
    print(f"  Staging Bucket:  gs://vg-pp-001-agent-staging")
    
    try:
        vertexai.init(
            project=PROJECT_ID,
            location=LOCATION,
            staging_bucket="gs://vg-pp-001-agent-staging",
        )
        print("  ✓ Vertex AI initialized successfully")
    except Exception as e:
        print(f"  ✗ Failed to initialize Vertex AI: {e}")
        print("\nMake sure:")
        print("1. You've run: gcloud auth application-default login")
        print("2. APIs are enabled: gcloud services enable aiplatform.googleapis.com")
        print("3. Staging bucket exists: gsutil ls gs://vg-pp-001-agent-staging")
        sys.exit(1)
    
    # Step 3: Deploy to Agent Engine
    print(f"\n🔨 Step 3: Deploying to Agent Engine")
    print("  This process includes:")
    print("    • Packaging the agent and source files")
    print("    • Building a container image")
    print("    • Deploying to managed infrastructure")
    print("    • Setting up auto-scaling")
    print("    • Enabling Cloud Trace for observability")
    print("\n  ⏱️  This may take 5-10 minutes...")
    print("  Please wait...\n")
    
    try:
        # Deploy using agent_engines.create()
        # Reference: https://docs.cloud.google.com/agent-builder/agent-engine/deploy
        remote_agent = agent_engines.create(
            agent_engine=root_agent,
            
            # Requirements from requirements.txt
            requirements="requirements.txt",
            
            # Optional: Include source files for reference/debugging
            # extra_packages=["."],  # Uncomment to include all files
            
            # Display metadata
            display_name=DISPLAY_NAME,
            description="Friendly AI assistant powered by Google ADK and Gemini 2.0 Flash",
            
            # Environment variables for tracing
            # Per https://docs.cloud.google.com/agent-builder/agent-engine/manage/tracing#adk
            env_vars={
                "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
                "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
                "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            },
        )
        print("  ✓ Deployment completed successfully!")
        
        # Step 4: Display deployment info
        print(f"\n📊 Deployment Information")
        print(f"  Resource Name:   {remote_agent.gca_resource.name}")
        print(f"  Display Name:    {DISPLAY_NAME}")
        print(f"  Project:         {PROJECT_ID}")
        print(f"  Location:        {LOCATION}")
        print(f"  Framework:       Google ADK")
        print(f"  Tracing:         Enabled ✓")
        
        # Show supported operations
        print(f"\n🔧 Supported Operations:")
        try:
            operations = remote_agent.operation_schemas()
            for op_name in operations.keys():
                print(f"  • {op_name}")
        except Exception as e:
            print(f"  (Could not retrieve operations: {e})")
        
        print(f"\n✅ Deployment Complete!")
        print(f"\nNext Steps:")
        print(f"1. Test your deployed agent:")
        print(f"   python test_deployed_adk.py")
        print(f"\n2. View in Cloud Console:")
        print(f"   https://console.cloud.google.com/vertex-ai/reasoning-engines?project={PROJECT_ID}")
        print(f"\n3. View Traces:")
        print(f"   https://console.cloud.google.com/traces/list?project={PROJECT_ID}")
        print(f"\n4. Monitor with Cloud Logging:")
        print(f"   gcloud logging read 'resource.type=aiplatform.googleapis.com/ReasoningEngine' --limit 50 --project={PROJECT_ID}")
        
        # Save resource name for testing
        resource_name = remote_agent.gca_resource.name
        with open("deployed_agent_resource.txt", "w") as f:
            f.write(resource_name)
        print(f"\n💾 Resource name saved to: deployed_agent_resource.txt")
        
        return remote_agent
        
    except Exception as e:
        print(f"  ✗ Deployment failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check that you're in the basic-agent directory")
        print("2. Verify requirements.txt exists and has correct packages")
        print("3. Ensure agent.py defines 'root_agent' at module level")
        print("4. Check Cloud Build permissions")
        print("5. Review error logs:")
        print(f"   gcloud logging read 'resource.type=aiplatform.googleapis.com/ReasoningEngine AND severity>=ERROR' --limit=10 --project={PROJECT_ID}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we're in the basic-agent directory
    import os
    current_dir = os.path.basename(os.getcwd())
    if current_dir != "basic-agent":
        print("❌ Error: This script must be run from the basic-agent directory")
        print(f"   Current directory: {os.getcwd()}")
        print("\n   Please run:")
        print("   cd /Users/vishal/genai/1/basic-agent")
        print("   python deploy_from_source.py")
        sys.exit(1)
    
    # Verify required files exist
    required_files = ["agent.py", "requirements.txt"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Error: Required files missing: {', '.join(missing_files)}")
        sys.exit(1)
    
    print("🏁 Starting deployment process...\n")
    print("-"*70)
    
    # Test locally first
    test_local = input("Would you like to test locally first? (y/n) [y]: ").strip().lower()
    if test_local == "" or test_local == "y":
        print("\n🧪 Testing agent locally first...")
        try:
            from agent import root_agent, FriendlyAgentRunner
            
            print(f"✓ Successfully imported root_agent from agent.py")
            print(f"✓ Agent type: {type(root_agent).__name__}")
            print(f"✓ Agent name: {root_agent.name}")
            
            local_runner = FriendlyAgentRunner()
            test_message = "Hi!"
            response = local_runner.send_message(test_message)
            print(f"✓ Local test successful!")
            print(f"  Test query: {test_message}")
            print(f"  Response: {response}")
        except Exception as e:
            print(f"✗ Local test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        print("\n" + "-"*70 + "\n")
    
    # Confirm deployment
    print("⚠️  You are about to deploy to production!")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Region:  {LOCATION}")
    print(f"   Method:  Source Files (Recommended)")
    print()
    
    confirm = input("Proceed with deployment? (yes/no) [yes]: ").strip().lower()
    if confirm and confirm not in ["yes", "y"]:
        print("Deployment cancelled.")
        sys.exit(0)
    
    # Deploy the agent
    deploy_agent()
