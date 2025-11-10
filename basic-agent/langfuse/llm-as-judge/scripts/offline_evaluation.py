#!/usr/bin/env python3
"""
Offline Evaluation with LLM-as-Judge
Evaluates a dataset using correctness evaluator
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

from langfuse import Langfuse
from vertexai.generative_models import GenerativeModel
import vertexai

# Load environment FIRST - .env is in llm-as-judge folder
# scripts -> llm-as-judge
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

# Add parent directories to path
import sys
sys.path.append(str(Path(__file__).parent.parent / "evaluators"))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))  # For secret_manager

from correctness_template import get_evaluator_prompt, EVALUATOR_CONFIG

# Import secret manager if available
try:
    from secret_manager import get_langfuse_credentials
    USE_SECRET_MANAGER = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
except ImportError:
    USE_SECRET_MANAGER = False


def get_langfuse_client():
    """Get Langfuse client with Secret Manager support"""
    if USE_SECRET_MANAGER:
        try:
            print("🔐 Retrieving Langfuse credentials from Secret Manager...")
            project_id = os.getenv("GCP_PROJECT_ID", "vg-pp-001")
            public_key, secret_key = get_langfuse_credentials(project_id)
            langfuse_host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
            
            client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=langfuse_host
            )
            
            # Verify auth before returning
            if not client.auth_check():
                raise Exception("Authentication failed after client creation")
                
            return client
        except Exception as e:
            print(f"⚠️  Failed to retrieve from Secret Manager: {e}")
            print("   Falling back to environment variables...")
    
    # Fallback to environment variables
    client = Langfuse()
    
    # Verify auth
    if not client.auth_check():
        raise Exception("Langfuse authentication failed. Check your credentials.")
    
    return client



class CorrectnessEvaluator:
    """LLM-as-Judge evaluator for correctness"""
    
    def __init__(
        self,
        judge_model: str = "gemini-1.5-flash",
        evaluator_type: str = "comprehensive",
        project_id: str = None
    ):
        """
        Initialize the evaluator
        
        Args:
            judge_model: Model to use as judge
            evaluator_type: Type of evaluator prompt
            project_id: GCP project ID
        """
        self.judge_model = judge_model
        self.evaluator_type = evaluator_type
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location="us-central1")
        self.model = GenerativeModel(judge_model)
        
        # Get evaluator prompt
        self.prompt_template = get_evaluator_prompt(evaluator_type)
        
        print(f"✅ Evaluator initialized with {judge_model}")
    
    def _format_prompt(
        self,
        input_text: str,
        output_text: str,
        expected_output: str = "",
        evaluation_criteria: str = "",
        context: str = ""
    ) -> str:
        """Format the evaluation prompt with variables"""
        
        prompt = self.prompt_template
        prompt = prompt.replace("{{input}}", input_text)
        prompt = prompt.replace("{{output}}", output_text)
        prompt = prompt.replace("{{expected_output}}", expected_output or "Not provided")
        prompt = prompt.replace("{{evaluation_criteria}}", evaluation_criteria or "Not provided")
        prompt = prompt.replace("{{context}}", context or "Not provided")
        
        return prompt
    
    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: str = "",
        evaluation_criteria: str = "",
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single response
        
        Args:
            input_text: The question/input
            output_text: The response to evaluate
            expected_output: Expected/reference answer
            evaluation_criteria: Criteria for evaluation
            metadata: Additional metadata
        
        Returns:
            Evaluation results dict
        """
        
        # Format prompt
        prompt = self._format_prompt(
            input_text=input_text,
            output_text=output_text,
            expected_output=expected_output,
            evaluation_criteria=evaluation_criteria
        )
        
        try:
            # Call judge model
            response = await self.model.generate_content_async(prompt)
            result_text = response.text
            
            # Try to parse JSON response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a simple result
                result = {
                    "reasoning": result_text,
                    "overall_score": 5.0,  # Default mid-range score
                    "raw_response": result_text
                }
            
            # Add metadata
            result["metadata"] = metadata or {}
            result["judge_model"] = self.judge_model
            result["evaluator_type"] = self.evaluator_type
            result["timestamp"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            return {
                "error": str(e),
                "overall_score": 0.0,
                "metadata": metadata or {}
            }


async def run_offline_evaluation(
    dataset_name: str = "correctness-eval-golden",
    model_to_test: str = "gemini-1.5-flash",
    judge_model: str = "gemini-1.5-pro",
    run_name: str = None,
    sample_size: int = None
):
    """
    Run offline evaluation on a Langfuse dataset
    
    Args:
        dataset_name: Name of dataset in Langfuse
        model_to_test: Model to generate responses for evaluation
        judge_model: Model to use as judge
        run_name: Name for this evaluation run
        sample_size: Number of items to evaluate (None = all)
    """
    
    print("=" * 70)
    print("Offline Evaluation with LLM-as-Judge")
    print("=" * 70)
    print()
    print(f"Dataset: {dataset_name}")
    print(f"Model to test: {model_to_test}")
    print(f"Judge model: {judge_model}")
    print()
    
    # Initialize Langfuse
    try:
        langfuse = get_langfuse_client()
        print("✅ Langfuse authenticated")
        print()
    except Exception as e:
        print(f"❌ Langfuse authentication failed: {e}")
        return    
    # Get dataset from Langfuse
    print(f"Fetching dataset '{dataset_name}'...")
    
    try:
        dataset = langfuse.get_dataset(dataset_name)
        print(f"✅ Dataset loaded")
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")
        print("   Run: python scripts/upload_dataset.py")
        return
    
    # Get dataset items
    items = list(dataset.items)
    
    if sample_size:
        import random
        items = random.sample(items, min(sample_size, len(items)))
    
    print(f"   Items to evaluate: {len(items)}")
    print()
    
    # Initialize evaluator
    evaluator = CorrectnessEvaluator(
        judge_model=judge_model,
        evaluator_type="comprehensive"
    )
    
    # Initialize model to test
    vertexai.init(project=os.getenv("GCP_PROJECT_ID"), location="us-central1")
    test_model = GenerativeModel(model_to_test)
    
    # Generate run name
    if run_name is None:
        run_name = f"{model_to_test}-eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print(f"📊 Starting evaluation run: {run_name}")
    print()
    
    # Results tracking
    results = []
    total_score = 0.0
    category_scores = {}
    
    # Process each item
    for idx, item in enumerate(items, 1):
        print(f"[{idx}/{len(items)}] Evaluating: {item.metadata.get('id', 'unknown')}")
        
        # Get test case details
        input_text = item.input
        expected_output = item.expected_output
        metadata = item.metadata or {}
        category = metadata.get("category", "unknown")
        evaluation_criteria = metadata.get("evaluation_criteria", "")
        
        try:
            # Generate response from model to test
            print(f"  → Generating response with {model_to_test}...")
            response = await test_model.generate_content_async(input_text)
            output_text = response.text
            
            # Evaluate the response
            print(f"  → Evaluating with {judge_model}...")
            eval_result = await evaluator.evaluate(
                input_text=input_text,
                output_text=output_text,
                expected_output=expected_output,
                evaluation_criteria=evaluation_criteria,
                metadata=metadata
            )
            
            score = eval_result.get("overall_score", 0.0)
            print(f"  ✅ Score: {score:.1f}/10")
            
            # Note: Langfuse dataset runs require newer SDK or different approach
            # Results are saved to local JSON file for now
            
            # Track results
            total_score += score
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(score)
            
            results.append({
                "id": metadata.get("id"),
                "category": category,
                "score": score,
                "eval_result": eval_result
            })
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                "id": metadata.get("id"),
                "category": category,
                "score": 0.0,
                "error": str(e)
            })
        
        print()
    
    # Flush Langfuse
    langfuse.flush()
    
    # Print results summary
    print("=" * 70)
    print("Evaluation Results")
    print("=" * 70)
    print()
    
    avg_score = total_score / len(items) if items else 0
    print(f"Overall Average Score: {avg_score:.2f}/10")
    print()
    
    print("Scores by Category:")
    print("─" * 70)
    for category, scores in sorted(category_scores.items()):
        cat_avg = sum(scores) / len(scores)
        print(f"  {category:30s}: {cat_avg:.2f}/10 ({len(scores)} items)")
    print()
    
    # Save results
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    results_file = results_dir / f"{run_name}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "run_name": run_name,
            "dataset": dataset_name,
            "model_tested": model_to_test,
            "judge_model": judge_model,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_items": len(items),
                "average_score": avg_score,
                "category_scores": {
                    cat: sum(scores) / len(scores)
                    for cat, scores in category_scores.items()
                }
            },
            "results": results
        }, f, indent=2)
    
    print(f"📊 Results saved to: {results_file}")
    print()
    
    print("View detailed results in Langfuse:")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
    print(f"  {langfuse_host}/datasets/{dataset_name}")
    print()
    
    return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run offline evaluation with LLM-as-Judge")
    parser.add_argument(
        "--dataset",
        default="correctness-eval-golden",
        help="Dataset name in Langfuse"
    )
    parser.add_argument(
        "--model",
        default="gemini-1.5-flash",
        help="Model to test"
    )
    parser.add_argument(
        "--judge",
        default="gemini-1.5-pro",
        help="Judge model"
    )
    parser.add_argument(
        "--run-name",
        help="Name for this evaluation run"
    )
    parser.add_argument(
        "--sample",
        type=int,
        help="Sample size (number of items to evaluate)"
    )
    
    args = parser.parse_args()
    
    # Run evaluation
    asyncio.run(run_offline_evaluation(
        dataset_name=args.dataset,
        model_to_test=args.model,
        judge_model=args.judge,
        run_name=args.run_name,
        sample_size=args.sample
    ))


if __name__ == "__main__":
    main()
