#!/usr/bin/env python3
"""
Upload Golden Dataset to Langfuse
Creates a dataset in Langfuse for offline evaluation
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment FIRST - .env is in llm-as-judge folder
# scripts -> llm-as-judge
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

# Add parent directory to path for secret_manager import
# Path: scripts -> llm-as-judge -> langfuse -> basic-agent
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from langfuse import Langfuse

# Import secret manager if available
try:
    from secret_manager import get_langfuse_credentials
    USE_SECRET_MANAGER = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
except ImportError:
    USE_SECRET_MANAGER = False

def load_golden_dataset(dataset_path: str = None):
    """Load golden dataset from JSON file"""
    if dataset_path is None:
        dataset_path = Path(__file__).parent.parent / "datasets" / "golden_dataset.json"
    
    with open(dataset_path, 'r') as f:
        return json.load(f)


def upload_dataset_to_langfuse(
    dataset_name: str = "correctness-eval-golden",
    dataset_description: str = "Golden dataset for correctness evaluation with LLM-as-Judge",
    overwrite: bool = False
):
    """
    Upload golden dataset to Langfuse
    
    Args:
        dataset_name: Name of the dataset in Langfuse
        dataset_description: Description of the dataset
        overwrite: If True, delete existing dataset and create new one
    
    Returns:
        Dataset object from Langfuse
    """
    
    print("=" * 70)
    print("Uploading Golden Dataset to Langfuse")
    print("=" * 70)
    print()
    
    # Debug environment
    print(f"USE_SECRET_MANAGER: {USE_SECRET_MANAGER}")
    print(f"LANGFUSE_ENABLED: {os.getenv('LANGFUSE_ENABLED')}")
    print()
    
    # Get Langfuse credentials
    if USE_SECRET_MANAGER:
        try:
            print("🔐 Retrieving Langfuse credentials from Secret Manager...")
            project_id = os.getenv("GCP_PROJECT_ID", "vg-pp-001")
            public_key, secret_key = get_langfuse_credentials(project_id)
            langfuse_host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
            
            langfuse = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=langfuse_host
            )
            print("   ✓ Retrieved from Secret Manager")
        except Exception as e:
            print(f"❌ Failed to retrieve from Secret Manager: {e}")
            print("   Falling back to environment variables...")
            langfuse = Langfuse()
    else:
        # Initialize Langfuse client from environment variables
        langfuse = Langfuse()
    
    print()
    
    # Verify authentication
    if not langfuse.auth_check():
        print("❌ Langfuse authentication failed!")
        print("   Check your LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        return None
    
    print("✅ Langfuse authenticated")
    print()
    
    # Load golden dataset
    print("Loading golden dataset...")
    golden_data = load_golden_dataset()
    print(f"✅ Loaded {len(golden_data)} test cases")
    print()
    
    # Create or get dataset
    print(f"Creating dataset: {dataset_name}")
    
    try:
        # Try to create dataset
        dataset = langfuse.create_dataset(
            name=dataset_name,
            description=dataset_description,
            metadata={
                "version": "1.0.0",
                "total_items": len(golden_data),
                "categories": list(set(item["category"] for item in golden_data)),
                "difficulty_levels": list(set(item["difficulty"] for item in golden_data))
            }
        )
        print(f"✅ Created new dataset: {dataset_name}")
    except Exception as e:
        if "already exists" in str(e).lower() or "unique constraint" in str(e).lower():
            print(f"⚠️  Dataset '{dataset_name}' already exists")
            
            if overwrite:
                print("🔄 Deleting existing dataset and recreating...")
                # Note: Langfuse doesn't have direct delete API yet
                # You may need to delete manually from the UI
                print("⚠️  Please delete the dataset manually from Langfuse UI and re-run")
                return None
            else:
                print("   Use --overwrite flag to replace it")
                print("   Or use a different dataset name")
                return None
        else:
            print(f"❌ Error creating dataset: {e}")
            return None
    
    print()
    print("Uploading dataset items...")
    print()
    
    # Upload each item
    uploaded_count = 0
    failed_count = 0
    
    for idx, item in enumerate(golden_data, 1):
        try:
            # Create dataset item
            langfuse.create_dataset_item(
                dataset_name=dataset_name,
                input=item["input"],
                expected_output=item["expected_output"],
                metadata={
                    "id": item["id"],
                    "category": item["category"],
                    "difficulty": item["difficulty"],
                    "evaluation_criteria": item["evaluation_criteria"]
                }
            )
            
            uploaded_count += 1
            print(f"  [{idx}/{len(golden_data)}] ✅ {item['id']} ({item['category']})")
            
        except Exception as e:
            failed_count += 1
            print(f"  [{idx}/{len(golden_data)}] ❌ {item['id']}: {e}")
    
    print()
    print("=" * 70)
    print("Upload Summary")
    print("=" * 70)
    print(f"Total items: {len(golden_data)}")
    print(f"✅ Uploaded: {uploaded_count}")
    print(f"❌ Failed: {failed_count}")
    print()
    
    # Flush to ensure all items are uploaded
    langfuse.flush()
    
    print(f"✅ Dataset '{dataset_name}' ready for evaluation!")
    print()
    print("View in Langfuse:")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
    print(f"  {langfuse_host}/datasets/{dataset_name}")
    print()
    
    # Show dataset statistics
    print("Dataset Statistics:")
    print("─" * 70)
    
    # Category breakdown
    categories = {}
    for item in golden_data:
        cat = item["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nBy Category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat:30s}: {count:2d} items")
    
    # Difficulty breakdown
    difficulty = {}
    for item in golden_data:
        diff = item["difficulty"]
        difficulty[diff] = difficulty.get(diff, 0) + 1
    
    print("\nBy Difficulty:")
    for diff, count in sorted(difficulty.items()):
        print(f"  {diff:10s}: {count:2d} items")
    
    print()
    print("=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print()
    print("1. Run offline evaluation on this dataset:")
    print("   python scripts/offline_evaluation.py")
    print()
    print("2. View results in Langfuse dashboard")
    print()
    print("3. Set up online evaluation for production traces:")
    print("   python scripts/online_evaluation.py")
    print()
    
    return dataset


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload golden dataset to Langfuse")
    parser.add_argument(
        "--name",
        default="correctness-eval-golden",
        help="Dataset name in Langfuse"
    )
    parser.add_argument(
        "--description",
        default="Golden dataset for correctness evaluation with LLM-as-Judge",
        help="Dataset description"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing dataset"
    )
    parser.add_argument(
        "--dataset-path",
        help="Path to custom golden dataset JSON file"
    )
    
    args = parser.parse_args()
    
    # Upload dataset
    dataset = upload_dataset_to_langfuse(
        dataset_name=args.name,
        dataset_description=args.description,
        overwrite=args.overwrite
    )
    
    if dataset:
        print("✅ Success!")
        exit(0)
    else:
        print("❌ Failed to upload dataset")
        exit(1)


if __name__ == "__main__":
    main()
