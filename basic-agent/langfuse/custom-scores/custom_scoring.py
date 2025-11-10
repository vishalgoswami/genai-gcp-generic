"""
Custom Scoring Script - Programmatic Evaluations (No LLM Required)

This script applies custom programmatic scores to Langfuse traces:
1. Token Count (Categorical: LOW/MEDIUM/HIGH)
2. Response Latency (Numeric: 0-10)

Unlike LLM-as-judge evaluations, these scores are computed directly from trace data
without requiring additional LLM calls, making them fast and cost-effective.

Usage:
    python custom_scoring.py --limit 10
    python custom_scoring.py --limit 5 --page 2
    python custom_scoring.py --trace-id abc123
"""

import os
import sys
import json
import base64
import argparse
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent / ".env"
load_dotenv(env_file)

# Check if we should use Secret Manager
try:
    USE_SECRET_MANAGER = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
except:
    USE_SECRET_MANAGER = False

# Import custom scorers
from token_count_scorer import TokenCountScorer
from response_latency_scorer import ResponseLatencyScorer


class CustomScoreManager:
    """
    Manages custom programmatic scoring for Langfuse traces.
    
    Applies token count and latency scores without using LLM evaluation.
    """
    
    def __init__(self, project_id: str = None):
        """
        Initialize the custom score manager.
        
        Args:
            project_id: Google Cloud project ID for Secret Manager
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "genai-gcp-generic")
        self.langfuse_public_key = None
        self.langfuse_secret_key = None
        self.base_url = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
        
        # Initialize scorers
        self.token_scorer = TokenCountScorer()
        self.latency_scorer = ResponseLatencyScorer()
        
        # Load credentials
        self._load_credentials()
    
    def _load_credentials(self):
        """Load Langfuse credentials from Secret Manager or environment."""
        if USE_SECRET_MANAGER:
            try:
                from google.cloud import secretmanager
                
                print("🔐 Retrieving Langfuse credentials from Secret Manager...")
                client = secretmanager.SecretManagerServiceClient()
                
                # Get public key
                public_key_path = f"projects/{self.project_id}/secrets/langfuse-public-key/versions/latest"
                public_response = client.access_secret_version(request={"name": public_key_path})
                self.langfuse_public_key = public_response.payload.data.decode("UTF-8")
                
                # Get secret key
                secret_key_path = f"projects/{self.project_id}/secrets/langfuse-secret-key/versions/latest"
                secret_response = client.access_secret_version(request={"name": secret_key_path})
                self.langfuse_secret_key = secret_response.payload.data.decode("UTF-8")
                
                print("✅ Loaded credentials from Secret Manager")
                
            except Exception as e:
                print(f"   ⚠️  Failed to load from Secret Manager: {e}")
                print("   ⚠️  Falling back to environment variables...")
                self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
                self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        else:
            # Use environment variables
            self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            print("✅ Loaded credentials from environment variables")
        
        if not self.langfuse_public_key or not self.langfuse_secret_key:
            raise ValueError(
                "❌ Langfuse credentials not found!\n"
                "Please set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env file\n"
                "Get your keys from: https://us.cloud.langfuse.com/settings"
            )
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get Basic Auth header for Langfuse API."""
        credentials = f"{self.langfuse_public_key}:{self.langfuse_secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}
    
    def fetch_traces(
        self, 
        limit: int = 10, 
        page: int = 1,
        trace_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch traces from Langfuse.
        
        Args:
            limit: Number of traces to fetch per page
            page: Page number (1-indexed)
            trace_id: Specific trace ID to fetch (ignores limit/page)
            
        Returns:
            List of trace dictionaries
        """
        if trace_id:
            # Fetch specific trace
            url = f"{self.base_url}/api/public/traces/{trace_id}"
            try:
                response = requests.get(url, headers=self._get_auth_header())
                response.raise_for_status()
                return [response.json()]
            except Exception as e:
                print(f"❌ Error fetching trace {trace_id}: {e}")
                return []
        
        # Fetch multiple traces
        url = f"{self.base_url}/api/public/traces"
        params = {"limit": limit, "page": page}
        
        try:
            response = requests.get(url, headers=self._get_auth_header(), params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(f"❌ Error fetching traces: {e}")
            return []
    
    def create_score(
        self,
        trace_id: str,
        name: str,
        value: Any,
        data_type: str,
        comment: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> bool:
        """
        Create a score in Langfuse.
        
        Args:
            trace_id: ID of the trace to score
            name: Score name
            value: Score value (string for categorical, float for numeric)
            data_type: "CATEGORICAL" or "NUMERIC"
            comment: Optional explanatory comment
            data: Optional additional data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/public/scores"
        
        payload = {
            "traceId": trace_id,
            "name": name,
            "value": value,
            "dataType": data_type
        }
        
        if comment:
            payload["comment"] = comment
        
        if data:
            payload["data"] = data
        
        try:
            response = requests.post(
                url,
                headers=self._get_auth_header(),
                json=payload
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Error creating score '{name}': {e}")
            return False
    
    def fetch_trace_details(self, trace_id: str) -> Optional[Dict]:
        """
        Fetch full trace details including observations.
        
        Args:
            trace_id: ID of the trace to fetch
            
        Returns:
            Full trace dictionary or None
        """
        url = f"{self.base_url}/api/public/traces/{trace_id}"
        
        try:
            response = requests.get(url, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Warning: Could not fetch trace details for {trace_id}: {e}")
            return None
    
    def extract_input_output(self, trace: Dict) -> Optional[tuple]:
        """
        Extract input and output text from trace.
        
        Args:
            trace: Trace dictionary
            
        Returns:
            Tuple of (input_text, output_text) or None
        """
        try:
            input_text = None
            output_text = None
            
            # First try to get from trace-level fields
            if "input" in trace and trace["input"]:
                if isinstance(trace["input"], str):
                    input_text = trace["input"]
                elif isinstance(trace["input"], dict):
                    input_text = str(trace["input"])
            
            if "output" in trace and trace["output"]:
                if isinstance(trace["output"], str):
                    output_text = trace["output"]
                elif isinstance(trace["output"], dict):
                    output_text = str(trace["output"])
            
            # If not found, try observations
            if not input_text or not output_text:
                observations = trace.get("observations", [])
                
                # Find the GENERATION observation
                for obs in observations:
                    if obs.get("type") == "GENERATION":
                        # Extract input
                        obs_input = obs.get("input")
                        
                        if isinstance(obs_input, str):
                            input_text = obs_input
                        elif isinstance(obs_input, dict):
                            # Handle Vertex AI format with contents
                            if "contents" in obs_input:
                                for content in obs_input["contents"]:
                                    if isinstance(content, dict) and content.get("role") == "user":
                                        parts = content.get("parts", [])
                                        if parts:
                                            input_text = parts[0].get("text", "")
                                            break
                            # Handle messages format
                            elif "messages" in obs_input:
                                for msg in reversed(obs_input["messages"]):
                                    if msg.get("role") == "user":
                                        input_text = msg.get("content", "")
                                        break
                            # Handle simple text field
                            elif "text" in obs_input:
                                input_text = obs_input["text"]
                            elif "prompt" in obs_input:
                                input_text = obs_input["prompt"]
                        
                        # Extract output
                        obs_output = obs.get("output")
                        
                        if isinstance(obs_output, str):
                            output_text = obs_output
                        elif isinstance(obs_output, dict):
                            # Handle Vertex AI/Gemini format
                            if "content" in obs_output:
                                content = obs_output["content"]
                                if isinstance(content, dict) and "parts" in content:
                                    parts = content["parts"]
                                    if parts:
                                        output_text = parts[0].get("text", "")
                                elif isinstance(content, str):
                                    output_text = content
                            # Handle simple text field
                            elif "text" in obs_output:
                                output_text = obs_output["text"]
                        
                        if input_text and output_text:
                            break
            
            if input_text and output_text:
                return input_text.strip(), output_text.strip()
            
            return None
            
        except Exception as e:
            print(f"Warning: Error extracting input/output: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def score_trace(self, trace: Dict) -> Dict[str, bool]:
        """
        Apply all custom scores to a trace.
        
        Args:
            trace: Trace dictionary
            
        Returns:
            Dictionary mapping score names to success status
        """
        trace_id = trace.get("id")
        trace_name = trace.get("name", "unnamed")
        results = {}
        
        # Fetch full trace details if observations are not present or are strings
        if "observations" not in trace or not trace["observations"] or isinstance(trace.get("observations", [None])[0] if trace.get("observations") else None, str):
            trace = self.fetch_trace_details(trace_id)
            if not trace:
                print(f"⚠️  Could not fetch trace details for {trace_id}")
                return results
        
        # Extract input and output
        extracted = self.extract_input_output(trace)
        if not extracted:
            print(f"⚠️  No input/output found in trace {trace_id}")
            return results
        
        input_text, output_text = extracted
        
        # 1. Token Count Score (Categorical)
        try:
            category, data, comment = self.token_scorer.score_input_and_response(
                input_text, output_text
            )
            
            success = self.create_score(
                trace_id=trace_id,
                name="token_count",
                value=category,
                data_type="CATEGORICAL",
                comment=comment,
                data=data
            )
            
            results["token_count"] = success
            
            if success:
                print(f"  ✅ Token Count: {category} ({data['response_tokens']} tokens)")
            
        except Exception as e:
            print(f"  ❌ Token Count scoring failed: {e}")
            results["token_count"] = False
        
        # 2. Response Latency Score (Numeric)
        try:
            latency_result = self.latency_scorer.score_from_trace_data(trace)
            
            if latency_result:
                score, latency_seconds, comment = latency_result
                
                success = self.create_score(
                    trace_id=trace_id,
                    name="response_latency",
                    value=score,
                    data_type="NUMERIC",
                    comment=comment,
                    data={"latency_seconds": latency_seconds}
                )
                
                results["response_latency"] = success
                
                if success:
                    print(f"  ✅ Response Latency: {score:.1f}/10 ({latency_seconds:.2f}s)")
            else:
                print(f"  ⚠️  No latency data available")
                results["response_latency"] = False
                
        except Exception as e:
            print(f"  ❌ Latency scoring failed: {e}")
            results["response_latency"] = False
        
        return results
    
    def run(
        self, 
        limit: int = 10, 
        page: int = 1,
        trace_id: Optional[str] = None
    ):
        """
        Run custom scoring on traces.
        
        Args:
            limit: Number of traces to process
            page: Page number
            trace_id: Specific trace ID to score
        """
        print("\n" + "=" * 80)
        print("Custom Scoring - Programmatic Evaluations (No LLM)")
        print("=" * 80)
        print("\nScores to apply:")
        print("  1. token_count (CATEGORICAL: LOW/MEDIUM/HIGH)")
        print("  2. response_latency (NUMERIC: 0-10)")
        print("\n" + "=" * 80 + "\n")
        
        # Fetch traces
        if trace_id:
            print(f"Fetching trace: {trace_id}\n")
        else:
            print(f"Fetching traces (limit: {limit}, page: {page})\n")
        
        traces = self.fetch_traces(limit=limit, page=page, trace_id=trace_id)
        
        if not traces:
            print("❌ No traces found")
            return
        
        print(f"Found {len(traces)} trace(s)\n")
        
        # Score each trace
        total_scores = {"token_count": 0, "response_latency": 0}
        
        for i, trace in enumerate(traces, 1):
            trace_id = trace.get("id", "unknown")
            trace_name = trace.get("name", "unnamed")
            
            print(f"[{i}/{len(traces)}] {trace_name} ({trace_id[:12]}...)")
            
            results = self.score_trace(trace)
            
            # Update totals
            for score_name, success in results.items():
                if success:
                    total_scores[score_name] += 1
            
            print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"\nTotal traces processed: {len(traces)}")
        print(f"\nScores created:")
        print(f"  - token_count: {total_scores['token_count']}/{len(traces)}")
        print(f"  - response_latency: {total_scores['response_latency']}/{len(traces)}")
        
        print(f"\n✅ Custom scoring complete!")
        print(f"\nView scores in Langfuse dashboard:")
        print(f"  {self.base_url}/scores")
        print("\n" + "=" * 80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Apply custom programmatic scores to Langfuse traces"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of traces to process (default: 10)"
    )
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number for pagination (default: 1)"
    )
    parser.add_argument(
        "--trace-id",
        type=str,
        help="Specific trace ID to score (ignores --limit and --page)"
    )
    
    args = parser.parse_args()
    
    # Create manager and run
    manager = CustomScoreManager()
    manager.run(
        limit=args.limit,
        page=args.page,
        trace_id=args.trace_id
    )


if __name__ == "__main__":
    main()
