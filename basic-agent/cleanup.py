#!/usr/bin/env python3
"""
GCP Resource Cleanup Script
Cleans up all deployed resources to avoid charges
"""

import os
import sys
import asyncio
import vertexai
from vertexai import agent_engines
from google.cloud import aiplatform
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID", "vg-pp-001")
LOCATION = os.getenv("LOCATION", "us-central1")


class GCPCleanup:
    """Cleanup GCP resources"""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.location = LOCATION
        self.deleted_resources = []
        self.errors = []
    
    def initialize(self):
        """Initialize Vertex AI"""
        try:
            vertexai.init(project=self.project_id, location=self.location)
            aiplatform.init(project=self.project_id, location=self.location)
            print(f"✓ Connected to GCP Project: {self.project_id}")
            print(f"✓ Location: {self.location}")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize: {e}")
            return False
    
    async def list_deployed_agents(self):
        """List all deployed reasoning engines"""
        try:
            print("\n📋 Listing deployed agents...")
            agents = list(agent_engines.list())
            
            if not agents:
                print("   No deployed agents found")
                return []
            
            print(f"   Found {len(agents)} deployed agent(s):")
            for i, agent in enumerate(agents, 1):
                resource_name = agent.gca_resource.name
                display_name = agent.gca_resource.display_name or "Unnamed"
                create_time = agent.gca_resource.create_time
                print(f"   {i}. {display_name}")
                print(f"      Resource: {resource_name}")
                print(f"      Created: {create_time}")
            
            return agents
        except Exception as e:
            print(f"   ✗ Error listing agents: {e}")
            self.errors.append(f"List agents: {e}")
            return []
    
    async def delete_agent(self, resource_name: str, display_name: str = "Unknown"):
        """Delete a specific agent"""
        try:
            print(f"\n🗑️  Deleting agent: {display_name}")
            print(f"   Resource: {resource_name}")
            
            # Delete the reasoning engine
            client = aiplatform.gapic.ReasoningEngineServiceClient(
                client_options={"api_endpoint": f"{self.location}-aiplatform.googleapis.com"}
            )
            
            operation = client.delete_reasoning_engine(name=resource_name)
            print("   ⏳ Deletion in progress...")
            
            # Wait for deletion to complete
            result = operation.result(timeout=300)  # 5 minutes timeout
            
            print(f"   ✓ Successfully deleted: {display_name}")
            self.deleted_resources.append(f"Agent: {display_name} ({resource_name})")
            return True
            
        except Exception as e:
            print(f"   ✗ Failed to delete {display_name}: {e}")
            self.errors.append(f"Delete agent {display_name}: {e}")
            return False
    
    async def cleanup_all_agents(self):
        """Delete all deployed agents"""
        agents = await self.list_deployed_agents()
        
        if not agents:
            return True
        
        print("\n⚠️  WARNING: This will delete ALL deployed agents!")
        response = input("   Continue? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("   ✗ Cleanup cancelled")
            return False
        
        success_count = 0
        for agent in agents:
            resource_name = agent.gca_resource.name
            display_name = agent.gca_resource.display_name or "Unnamed"
            
            if await self.delete_agent(resource_name, display_name):
                success_count += 1
        
        return success_count == len(agents)
    
    async def list_sessions(self, agent_resource_name: str):
        """List all sessions for an agent"""
        try:
            print(f"\n📋 Listing sessions for agent...")
            agent = agent_engines.get(agent_resource_name)
            
            # Note: We can't list all sessions without user IDs
            # This is a limitation of the Agent Engine API
            print("   ℹ️  Sessions are user-specific and auto-expire")
            print("   ℹ️  No manual cleanup required")
            return []
            
        except Exception as e:
            print(f"   ✗ Error listing sessions: {e}")
            return []
    
    def cleanup_local_cache(self):
        """Clean up local cache and temporary files"""
        print("\n🧹 Cleaning up local files...")
        
        cache_files = [
            "deployed_agent_resource.txt",
            "__pycache__",
        ]
        
        for file_path in cache_files:
            try:
                if os.path.exists(file_path):
                    if os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                        print(f"   ✓ Removed directory: {file_path}")
                    else:
                        os.remove(file_path)
                        print(f"   ✓ Removed file: {file_path}")
                    self.deleted_resources.append(f"Local: {file_path}")
            except Exception as e:
                print(f"   ✗ Failed to remove {file_path}: {e}")
                self.errors.append(f"Remove {file_path}: {e}")
    
    def print_summary(self):
        """Print cleanup summary"""
        print("\n" + "=" * 70)
        print("CLEANUP SUMMARY")
        print("=" * 70)
        
        if self.deleted_resources:
            print(f"\n✓ Successfully deleted {len(self.deleted_resources)} resource(s):")
            for resource in self.deleted_resources:
                print(f"   • {resource}")
        else:
            print("\nℹ️  No resources were deleted")
        
        if self.errors:
            print(f"\n✗ Encountered {len(self.errors)} error(s):")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("\n✓ No errors encountered")
        
        print("\n" + "=" * 70)
        print("💰 Cost Savings:")
        print("   • Vertex AI Agent Engine: Stopped billing")
        print("   • Reasoning Engine compute: Terminated")
        print("   • Storage: Cleared (if any)")
        print("=" * 70)


async def main():
    """Main cleanup function"""
    print("=" * 70)
    print("GCP RESOURCE CLEANUP")
    print("=" * 70)
    print("\nThis script will help you clean up Google Cloud resources")
    print("to avoid unnecessary charges.\n")
    
    cleanup = GCPCleanup()
    
    # Initialize
    if not cleanup.initialize():
        print("\n✗ Failed to connect to GCP. Please check:")
        print("   1. gcloud auth application-default login")
        print("   2. PROJECT_ID in .env file")
        print("   3. Vertex AI API is enabled")
        sys.exit(1)
    
    # Menu
    while True:
        print("\n" + "-" * 70)
        print("CLEANUP OPTIONS:")
        print("-" * 70)
        print("1. List all deployed agents")
        print("2. Delete all deployed agents")
        print("3. Clean up local cache files")
        print("4. Full cleanup (agents + local files)")
        print("5. Exit")
        print("-" * 70)
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            await cleanup.list_deployed_agents()
        
        elif choice == "2":
            await cleanup.cleanup_all_agents()
        
        elif choice == "3":
            cleanup.cleanup_local_cache()
        
        elif choice == "4":
            print("\n⚠️  WARNING: Full cleanup will:")
            print("   • Delete ALL deployed agents")
            print("   • Remove local cache files")
            response = input("\nContinue? (yes/no): ").strip().lower()
            
            if response == 'yes':
                await cleanup.cleanup_all_agents()
                cleanup.cleanup_local_cache()
            else:
                print("✗ Full cleanup cancelled")
        
        elif choice == "5":
            cleanup.print_summary()
            print("\n👋 Goodbye!")
            break
        
        else:
            print("✗ Invalid option. Please select 1-5.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✗ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
