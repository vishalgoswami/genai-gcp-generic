#!/usr/bin/env python3
"""
Online Evaluation with LLM-as-Judge - Custom Metrics
Evaluates production traces with 5 metrics: correctness, toxicity, hallucination, relevance, conciseness
Fetches traces via HTTP API and creates scores in Langfuse
"""

import os
import json
import asyncio
import requests
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

from vertexai.generative_models import GenerativeModel
import vertexai

# Add parent directories to path
import sys
sys.path.append(str(Path(__file__).parent.parent / "evaluators"))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))  # For secret_manager

# Load environment FIRST - .env is in llm-as-judge folder
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

from correctness_template import CORRECTNESS_WITHOUT_REFERENCE_PROMPT
from toxicity_template import TOXICITY_WITHOUT_CONTEXT_PROMPT
from hallucination_template import HALLUCINATION_WITHOUT_CONTEXT_PROMPT
from relevance_template import RELEVANCE_WITHOUT_CONTEXT_PROMPT
from conciseness_template import CONCISENESS_WITHOUT_CONTEXT_PROMPT

# Import secret manager if available
try:
    from secret_manager import get_langfuse_credentials
    USE_SECRET_MANAGER = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
except ImportError:
    USE_SECRET_MANAGER = False


class OnlineEvaluator:
    """Online evaluator for production traces"""
    
    def __init__(
        self,
        judge_model: str = "gemini-2.0-flash-exp",
        project_id: str = None
    ):
        """Initialize online evaluator"""
        self.judge_model = judge_model
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        
        # Get Langfuse credentials
        if USE_SECRET_MANAGER:
            try:
                print("🔐 Retrieving Langfuse credentials from Secret Manager...")
                self.public_key, self.secret_key = get_langfuse_credentials(self.project_id)
            except:
                print("   ⚠️  Failed, using environment variables...")
                self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
                self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        else:
            self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        
        self.host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
        self.api_base = f"{self.host}/api/public"
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location="us-central1")
        self.model = GenerativeModel(judge_model)
        
        print(f"✅ Online evaluator initialized with {judge_model}")
    
    def fetch_traces(self, limit: int = 10, page: int = 1) -> List[Dict]:
        """Fetch recent traces via HTTP API"""
        
        url = f"{self.api_base}/traces"
        
        # Langfuse uses Basic Auth
        auth_string = f"{self.public_key}:{self.secret_key}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/json"
        }
        params = {
            "limit": limit,
            "page": page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(f"❌ Failed to fetch traces: {e}")
            return []
    
    def create_score(self, trace_id: str, name: str, value: float, comment: str = "") -> bool:
        """Create a score for a trace via HTTP API"""
        
        url = f"{self.api_base}/scores"
        
        # Langfuse uses Basic Auth
        auth_string = f"{self.public_key}:{self.secret_key}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "traceId": trace_id,
            "name": name,
            "value": value,
            "comment": comment,
            "dataType": "NUMERIC"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"   ⚠️  Failed to create score: {e}")
            return False
    
    def evaluate_without_reference(self, user_input: str, response: str) -> Tuple[float, str]:
        """
        Evaluate without a reference answer (using only user input and response).
        Returns (score_0_to_1, reasoning)
        """
        try:
            # Format the evaluation prompt (use .replace() to avoid format() issues with JSON braces)
            eval_prompt = CORRECTNESS_WITHOUT_REFERENCE_PROMPT.replace("{{input}}", user_input)
            eval_prompt = eval_prompt.replace("{{output}}", response)
            eval_prompt = eval_prompt.replace("{{context}}", "")
            
            # Call the judge model
            response_obj = self.model.generate_content(eval_prompt)
            
            # Extract score and reasoning
            response_text = response_obj.text
            
            # Try to parse JSON response first
            try:
                # Extract JSON from markdown code blocks if present
                result_text = response_text
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
                score = result.get("score", 0.0)
                reasoning = result.get("reasoning", "")
                
                # Normalize score to 0-1 range
                score_0_to_1 = score / 10.0
                return score_0_to_1, reasoning
                
            except json.JSONDecodeError:
                # Fallback to text parsing if JSON fails
                score = None
                reasoning = ""
                
                for line in response_text.split('\n'):
                    line = line.strip()
                    if line.startswith('SCORE:'):
                        try:
                            score_str = line.replace('SCORE:', '').strip()
                            score = float(score_str)
                        except ValueError:
                            pass
                    elif line.startswith('REASONING:'):
                        reasoning = line.replace('REASONING:', '').strip()
                
                # Normalize score to 0-1 range
                if score is not None:
                    score_0_to_1 = score / 10.0
                    return score_0_to_1, reasoning
                else:
                    return 0.0, "Could not parse score from response"
                
        except Exception as e:
            print(f"   ❌ Evaluation error: {e}")
            return 0.0, f"Evaluation failed: {str(e)}"
    
    def evaluate_toxicity(self, response: str) -> Tuple[float, str, bool]:
        """
        Evaluate toxicity of a response (without user input context).
        Returns (toxicity_score_0_to_10, reasoning, is_safe)
        """
        try:
            # Format the evaluation prompt
            eval_prompt = TOXICITY_WITHOUT_CONTEXT_PROMPT.replace("{{output}}", response)
            
            # Call the judge model
            response_obj = self.model.generate_content(eval_prompt)
            
            # Extract score and reasoning
            response_text = response_obj.text
            
            # Try to parse JSON response
            try:
                # Extract JSON from markdown code blocks if present
                result_text = response_text
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
                toxicity_score = result.get("toxicity_score", 0.0)
                reasoning = result.get("reasoning", "")
                is_safe = result.get("is_safe", True)
                
                return toxicity_score, reasoning, is_safe
                
            except json.JSONDecodeError:
                # Fallback: assume safe if parsing fails
                return 0.0, "Could not parse toxicity evaluation", True
                
        except Exception as e:
            print(f"   ❌ Toxicity evaluation error: {e}")
            return 0.0, f"Toxicity evaluation failed: {str(e)}", True
    
    def evaluate_hallucination(self, response: str) -> Tuple[float, str, bool]:
        """
        Evaluate if response contains hallucinations.
        Returns (hallucination_score_0_to_10, reasoning, is_grounded)
        """
        try:
            eval_prompt = HALLUCINATION_WITHOUT_CONTEXT_PROMPT.replace("{{output}}", response)
            response_obj = self.model.generate_content(eval_prompt)
            response_text = response_obj.text
            
            try:
                result_text = response_text
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
                hallucination_score = result.get("hallucination_score", 0.0)
                reasoning = result.get("reasoning", "")
                is_grounded = result.get("is_grounded", True)
                
                return hallucination_score, reasoning, is_grounded
            except json.JSONDecodeError:
                return 0.0, "Could not parse hallucination evaluation", True
        except Exception as e:
            print(f"   ❌ Hallucination evaluation error: {e}")
            return 0.0, f"Hallucination evaluation failed: {str(e)}", True
    
    def evaluate_relevance(self, user_input: str, response: str) -> Tuple[float, str]:
        """
        Evaluate relevance of response to user input.
        Returns (relevance_score_0_to_10, reasoning)
        """
        try:
            eval_prompt = RELEVANCE_WITHOUT_CONTEXT_PROMPT.replace("{{output}}", response)
            response_obj = self.model.generate_content(eval_prompt)
            response_text = response_obj.text
            
            try:
                result_text = response_text
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
                relevance_score = result.get("relevance_score", 5.0)
                reasoning = result.get("reasoning", "")
                
                return relevance_score, reasoning
            except json.JSONDecodeError:
                return 5.0, "Could not parse relevance evaluation"
        except Exception as e:
            print(f"   ❌ Relevance evaluation error: {e}")
            return 5.0, f"Relevance evaluation failed: {str(e)}"
    
    def evaluate_conciseness(self, response: str) -> Tuple[float, str]:
        """
        Evaluate conciseness of response.
        Returns (conciseness_score_0_to_10, reasoning)
        """
        try:
            eval_prompt = CONCISENESS_WITHOUT_CONTEXT_PROMPT.replace("{{output}}", response)
            response_obj = self.model.generate_content(eval_prompt)
            response_text = response_obj.text
            
            try:
                result_text = response_text
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
                conciseness_score = result.get("conciseness_score", 5.0)
                reasoning = result.get("reasoning", "")
                
                return conciseness_score, reasoning
            except json.JSONDecodeError:
                return 5.0, "Could not parse conciseness evaluation"
        except Exception as e:
            print(f"   ❌ Conciseness evaluation error: {e}")
            return 5.0, f"Conciseness evaluation failed: {str(e)}"
    
    async def evaluate_trace(self, trace: Dict) -> bool:
        """Evaluate a single trace and add scores"""
        
        trace_id = trace.get("id")
        trace_name = trace.get("name", "unknown")
        
        # Extract input/output from trace
        # Traces from OpenTelemetry instrumentation have input/output in different places
        input_text = None
        output_text = None
        
        # Try to get from input/output fields
        if "input" in trace and trace["input"]:
            if isinstance(trace["input"], dict):
                input_text = str(trace["input"])
            else:
                input_text = trace["input"]
        
        if "output" in trace and trace["output"]:
            if isinstance(trace["output"], dict):
                output_text = str(trace["output"])
            else:
                output_text = trace["output"]
        
        # If not found, try observations
        if not input_text or not output_text:
            # Fetch trace details with observations
            url = f"{self.api_base}/traces/{trace_id}"
            
            # Langfuse uses Basic Auth
            auth_string = f"{self.public_key}:{self.secret_key}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {auth_bytes}",
            }
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                trace_details = response.json()
                
                # Look for observations (generations/spans)
                observations = trace_details.get("observations", [])
                if observations:
                    # Get the GENERATION observation
                    for obs in observations:
                        if obs.get("type") == "GENERATION":
                            # Extract from the structured input/output
                            obs_input = obs.get("input") or {}
                            obs_output = obs.get("output") or {}
                            
                            # Input: try different formats
                            if isinstance(obs_input, dict):
                                # Option 1: Standard chat format with messages
                                if "messages" in obs_input:
                                    messages = obs_input["messages"]
                                    if messages and len(messages) > 0:
                                        # Get last user message
                                        for msg in reversed(messages):
                                            if msg.get("role") == "user":
                                                input_text = msg.get("content", "")
                                                break
                                
                                # Option 2: Vertex AI format with contents
                                elif "contents" in obs_input:
                                    contents = obs_input["contents"]
                                    if contents and len(contents) > 0:
                                        # Get the last user message from contents
                                        for content in reversed(contents):
                                            if isinstance(content, dict):
                                                if content.get("role") == "user":
                                                    parts = content.get("parts", [])
                                                    if parts and len(parts) > 0:
                                                        input_text = parts[0].get("text", "")
                                                        break
                                
                                # Option 3: Check for prompt or text field directly
                                elif "prompt" in obs_input:
                                    input_text = obs_input["prompt"]
                                elif "text" in obs_input:
                                    input_text = obs_input["text"]
                            
                            # Output: try different formats
                            if isinstance(obs_output, dict):
                                if "content" in obs_output:
                                    content = obs_output["content"]
                                    if isinstance(content, dict) and "parts" in content:
                                        # Gemini format
                                        parts = content["parts"]
                                        if parts and len(parts) > 0:
                                            output_text = parts[0].get("text", "")
                                    elif isinstance(content, str):
                                        output_text = content
                                elif "text" in obs_output:
                                    output_text = obs_output["text"]
                            
                            if input_text and output_text:
                                break
            except Exception as e:
                print(f"   ⚠️  Could not fetch trace details: {e}")
        
        # Skip if no input/output found
        if not input_text or not output_text:
            print(f"   ⚠️  Skipping {trace_id}: No input/output found")
            return False
        
        # Evaluate correctness
        print(f"  → Evaluating correctness...")
        score_0_to_1, reasoning = self.evaluate_without_reference(
            str(input_text),
            str(output_text)
        )
        
        score = score_0_to_1 * 10.0  # Convert from 0-1 to 0-10 for display
        print(f"  ✅ Correctness: {score:.1f}/10")
        
        # Create correctness score in Langfuse
        self.create_score(
            trace_id=trace_id,
            name="correctness",
            value=score,  # Send 0-10 range
            comment=reasoning[:500]  # Limit comment length
        )
        
        # Evaluate toxicity
        print(f"  → Evaluating toxicity...")
        toxicity_score, tox_reasoning, is_safe = self.evaluate_toxicity(str(output_text))
        
        print(f"  ✅ Toxicity: {toxicity_score:.1f}/10 {'(SAFE)' if is_safe else '(⚠️ UNSAFE)'}")
        
        # Create toxicity score in Langfuse (0=safe, 10=toxic)
        self.create_score(
            trace_id=trace_id,
            name="toxicity",
            value=toxicity_score,  # Send 0-10 range (0=safe, 10=toxic)
            comment=f"{'Safe' if is_safe else 'Unsafe'}. {tox_reasoning[:450]}"
        )
        
        # Evaluate hallucination
        print(f"  → Evaluating hallucination...")
        hallucination_score, hall_reasoning, is_grounded = self.evaluate_hallucination(str(output_text))
        
        print(f"  ✅ Hallucination: {hallucination_score:.1f}/10 {'(GROUNDED)' if is_grounded else '(⚠️ HALLUCINATED)'}")
        
        self.create_score(
            trace_id=trace_id,
            name="hallucination",
            value=hallucination_score,  # 0=grounded, 10=hallucinated
            comment=f"{'Grounded' if is_grounded else 'Hallucinated'}. {hall_reasoning[:450]}"
        )
        
        # Evaluate relevance
        print(f"  → Evaluating relevance...")
        relevance_score, rel_reasoning = self.evaluate_relevance(str(input_text), str(output_text))
        
        print(f"  ✅ Relevance: {relevance_score:.1f}/10")
        
        self.create_score(
            trace_id=trace_id,
            name="relevance",
            value=relevance_score,  # 0-10 (higher is better)
            comment=rel_reasoning[:500]
        )
        
        # Evaluate conciseness
        print(f"  → Evaluating conciseness...")
        conciseness_score, conc_reasoning = self.evaluate_conciseness(str(output_text))
        
        print(f"  ✅ Conciseness: {conciseness_score:.1f}/10")
        
        self.create_score(
            trace_id=trace_id,
            name="conciseness",
            value=conciseness_score,  # 0-10 (higher is better)
            comment=conc_reasoning[:500]
        )
        
        return True


async def run_online_evaluation(
    limit: int = 10,
    judge_model: str = "gemini-2.0-flash-exp"
):
    """Run online evaluation on recent traces with custom metrics"""
    
    print("=" * 70)
    print("Online Evaluation - Custom Metrics (5 Evaluators)")
    print("=" * 70)
    print()
    print("Metrics: Correctness | Toxicity | Hallucination | Relevance | Conciseness")
    print(f"Judge model: {judge_model}")
    print(f"Trace limit: {limit}")
    print()
    
    # Initialize evaluator
    evaluator = OnlineEvaluator(judge_model=judge_model)
    
    # Fetch recent traces
    print(f"📡 Fetching recent traces...")
    traces = evaluator.fetch_traces(limit=limit)
    
    if not traces:
        print("❌ No traces found!")
        print()
        print("To create traces, run your agent:")
        print("  cd /Users/vishal/genai/1/basic-agent")
        print("  python3 -c 'import asyncio; from agent import FriendlyAgentRunner; ...'")
        return
    
    print(f"✅ Found {len(traces)} traces")
    print()
    
    # Evaluate each trace
    print("=" * 70)
    print("Evaluating Traces")
    print("=" * 70)
    print()
    
    evaluated = 0
    skipped = 0
    
    for idx, trace in enumerate(traces, 1):
        trace_id = trace.get("id", "unknown")
        trace_name = trace.get("name", "unknown")
        timestamp = trace.get("timestamp", "")
        
        print(f"[{idx}/{len(traces)}] {trace_name} ({trace_id[:8]}...)")
        print(f"  Time: {timestamp}")
        
        success = await evaluator.evaluate_trace(trace)
        if success:
            evaluated += 1
        else:
            skipped += 1
        
        print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total traces: {len(traces)}")
    print(f"✅ Evaluated: {evaluated}")
    print(f"⚠️  Skipped: {skipped}")
    print()
    print("=" * 70)
    print("🌐 View Results in Langfuse Dashboard")
    print("=" * 70)
    print()
    print(f"Traces Page:  {evaluator.host}/traces")
    print(f"Scores Page:  {evaluator.host}/scores")
    print()
    print("Scores Created (all on 0-10 scale):")
    print("  - 'correctness': Quality and accuracy of response")
    print("  - 'toxicity': 0=safe, 10=toxic")
    print("  - 'hallucination': 0=grounded, 10=hallucinated")
    print("  - 'relevance': How well it addresses the question")
    print("  - 'conciseness': Clarity and brevity")
    print()
    print("Filter by:")
    print("  - Score name: any of the above metrics")
    print("  - Score value: 0-10 scale")
    print("  - Date range: Last hour/day/week")
    print()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Online evaluation of production traces")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent traces to evaluate (default: 10)"
    )
    parser.add_argument(
        "--judge",
        default="gemini-2.0-flash-exp",
        help="Judge model (default: gemini-2.0-flash-exp)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_online_evaluation(
        limit=args.limit,
        judge_model=args.judge
    ))


if __name__ == "__main__":
    main()
