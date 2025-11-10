# How to View Offline Evaluation Results

## 📊 Current Results (Local JSON Files)

### Quick Summary

Your evaluation completed with **excellent scores**:
- **Average Score**: 9.7/10 ✅
- **Test Cases Evaluated**: 2 (from sample run)
- **Categories**:
  - Logical Reasoning: 10.0/10
  - System Design: 9.4/10

### View Local Results

#### 1. List All Evaluation Runs
```bash
cd /Users/vishal/genai/1/basic-agent/langfuse/llm-as-judge/results
ls -lt *.json
```

#### 2. View Summary (Python)
```bash
python3 << 'EOF'
import json
from pathlib import Path

# Get most recent result
results_dir = Path(".")
latest_file = max(results_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)

with open(latest_file) as f:
    data = json.load(f)
    
print(f"{'='*70}")
print(f"Evaluation Run: {data['run_name']}")
print(f"{'='*70}")
print()
print(f"Dataset: {data['dataset']}")
print(f"Model Tested: {data['model_tested']}")
print(f"Judge Model: {data['judge_model']}")
print(f"Timestamp: {data['timestamp']}")
print()
print(f"{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")
print(f"Total Items: {data['summary']['total_items']}")
print(f"Average Score: {data['summary']['average_score']:.2f}/10")
print()
print("Category Scores:")
for cat, score in data['summary']['category_scores'].items():
    print(f"  {cat:30s}: {score:.1f}/10")
print()
print(f"{'='*70}")
print("DETAILED RESULTS")
print(f"{'='*70}")
for result in data['results']:
    print(f"\n[{result['id']}] {result['category']}")
    print(f"  Score: {result['score']:.1f}/10")
    print(f"  Verdict: {result['eval_result'].get('verdict', 'N/A')}")
    print(f"  Reasoning: {result['eval_result']['reasoning'][:200]}...")
    
    if result['eval_result'].get('key_issues'):
        print(f"  Issues: {', '.join(result['eval_result']['key_issues'])}")
    if result['eval_result'].get('strengths'):
        print(f"  Strengths: {', '.join(result['eval_result']['strengths'])}")
EOF
```

#### 3. View Specific Result File
```bash
# Replace with actual filename
cat gemini-2.0-flash-exp-eval-20251110-142048.json | python3 -m json.tool
```

#### 4. Extract Specific Information
```bash
# Find all failing tests (score < 7)
python3 << 'EOF'
import json
from pathlib import Path

latest_file = max(Path(".").glob("*.json"), key=lambda p: p.stat().st_mtime)
with open(latest_file) as f:
    data = json.load(f)
    
failing = [r for r in data['results'] if r['score'] < 7]
if failing:
    print(f"Found {len(failing)} failing tests:")
    for r in failing:
        print(f"  - {r['id']} ({r['category']}): {r['score']:.1f}/10")
        print(f"    Reason: {r['eval_result']['reasoning'][:150]}...")
else:
    print("✅ All tests passed! (score >= 7)")
EOF
```

---

## 🌐 Langfuse Dashboard (NOT YET IMPLEMENTED)

### Current Status
⚠️ The offline evaluation script **does NOT currently create traces in Langfuse** due to SDK compatibility issues. The Langfuse Python SDK v3.x uses a different API than our script was designed for.

### What You WON'T See (Yet)
- ❌ Individual evaluation traces in Langfuse UI
- ❌ Scores attached to traces
- ❌ Visual analytics in Langfuse dashboard
- ❌ Dataset run comparisons in Langfuse

### How to Enable Langfuse Dashboard Viewing

To view results in the Langfuse dashboard, we need to update the offline evaluation script to use the correct Langfuse SDK v3.x API. Here's what needs to be done:

#### Option 1: Use Langfuse Decorators (Recommended)

Update `offline_evaluation.py` to use the `@observe()` decorator:

```python
from langfuse.decorators import observe, langfuse_context

@observe()
async def evaluate_single_item(
    item,
    test_model,
    evaluator,
    model_to_test,
    judge_model,
    dataset_name,
    run_name
):
    """Evaluate a single dataset item with Langfuse tracing"""
    
    # Get test case details
    input_text = item.input
    expected_output = item.expected_output
    metadata = item.metadata or {}
    
    # Set trace metadata
    langfuse_context.update_current_trace(
        name=f"eval-{metadata.get('id', 'unknown')}",
        metadata={
            "dataset": dataset_name,
            "run_name": run_name,
            "category": metadata.get("category"),
            "model": model_to_test
        },
        tags=["offline-eval", metadata.get("category", "unknown")]
    )
    
    # Generate response (automatically logged as generation)
    response = await test_model.generate_content_async(input_text)
    output_text = response.text
    
    langfuse_context.update_current_observation(
        input=input_text,
        output=output_text,
        metadata={"model": model_to_test}
    )
    
    # Evaluate
    eval_result = await evaluator.evaluate(
        input_text=input_text,
        output_text=output_text,
        expected_output=expected_output,
        evaluation_criteria=metadata.get("evaluation_criteria", ""),
        metadata=metadata
    )
    
    # Add scores to trace
    langfuse_context.score_current_trace(
        name="correctness",
        value=eval_result.get("overall_score", 0) / 10,  # Normalize to 0-1
        comment=eval_result.get("reasoning", "")
    )
    
    for metric in ["factual_accuracy", "completeness", "relevance", "reasoning_quality", "safety"]:
        if metric in eval_result:
            langfuse_context.score_current_trace(
                name=metric,
                value=eval_result[metric] / 10,  # Normalize to 0-1
                comment=f"{metric}: {eval_result[metric]}/10"
            )
    
    return eval_result
```

#### Option 2: Use Low-Level API

```python
from langfuse import Langfuse

langfuse = Langfuse()

# Create a generation (not trace)
generation = langfuse.generation(
    name="model_response",
    model=model_to_test,
    input=input_text,
    output=output_text,
    metadata={
        "dataset": dataset_name,
        "category": category,
        "item_id": item.id
    }
)

# Add scores
langfuse.score(
    name="correctness",
    value=eval_result["overall_score"] / 10,
    data_type="numeric",
    comment=eval_result.get("reasoning", ""),
    trace_id=generation.trace_id
)
```

#### Option 3: Use Dataset Experiments (Best for Offline Eval)

```python
from langfuse import Langfuse

langfuse = Langfuse()

# Create experiment
experiment = langfuse.create_experiment(
    name=f"eval-{run_name}",
    dataset_name=dataset_name,
    metadata={
        "model": model_to_test,
        "judge": judge_model,
        "timestamp": datetime.now().isoformat()
    }
)

# For each item
for item in dataset.items:
    # Run evaluation...
    
    # Log to experiment
    experiment.log_run(
        dataset_item_id=item.id,
        input=input_text,
        output=output_text,
        expected_output=expected_output,
        metadata={
            "eval_result": eval_result,
            "score": eval_result["overall_score"]
        }
    )
```

---

## 🔧 Quick Fix: Enable Langfuse Dashboard

### Update the Script (Coming Soon)

We'll update `offline_evaluation.py` to use the `@observe()` decorator pattern. This will:

1. ✅ Create proper traces in Langfuse
2. ✅ Attach scores to traces
3. ✅ Enable dashboard visualization
4. ✅ Allow filtering and analytics

### Workaround: Manual Upload

For now, you can manually review results:

1. **Local JSON Files** (Current Method)
   - View: `results/*.json`
   - Analyze: Use Python scripts above
   - Pros: Works now, detailed data
   - Cons: No web UI, no aggregation

2. **Langfuse Dataset View**
   - URL: https://us.cloud.langfuse.com/datasets/correctness-eval-golden
   - Shows: Original test cases
   - Limitation: No evaluation results yet

---

## 📈 What You WILL See After Fix

Once we implement proper Langfuse integration:

### 1. Traces Page
```
https://us.cloud.langfuse.com/traces
```

**Features:**
- List of all evaluation runs
- Filter by:
  - Date range
  - Run name
  - Score range (e.g., score < 7)
  - Category
  - Model used
- Search by test ID

**Each trace shows:**
- Input question
- Model response
- Judge evaluation
- Scores (overall + detailed)
- Judge reasoning
- Metadata (category, difficulty, etc.)

### 2. Scores Page
```
https://us.cloud.langfuse.com/scores
```

**Features:**
- Score distribution histogram
- Average score over time
- Filter by score name (correctness, factual_accuracy, etc.)
- Identify low-scoring traces

### 3. Dataset Experiments
```
https://us.cloud.langfuse.com/datasets/correctness-eval-golden/experiments
```

**Features:**
- Compare multiple evaluation runs
- Side-by-side comparison
- See which model performs better
- Track improvements over time

### 4. Analytics Dashboard
```
https://us.cloud.langfuse.com/analytics
```

**Custom views:**
- Average score by category
- Pass rate (score >= 7)
- Trend over time
- Cost per evaluation
- Performance regression detection

---

## 🎯 Immediate Actions

### View Current Results (Works Now)
```bash
cd /Users/vishal/genai/1/basic-agent/langfuse/llm-as-judge/results

# Quick summary
python3 << 'EOF'
import json
from pathlib import Path

latest = max(Path(".").glob("*.json"), key=lambda p: p.stat().st_mtime)
with open(latest) as f:
    d = json.load(f)
    print(f"Run: {d['run_name']}")
    print(f"Score: {d['summary']['average_score']:.1f}/10")
    print(f"Items: {d['summary']['total_items']}")
EOF
```

### View in Langfuse (After Fix)
1. Update `offline_evaluation.py` with `@observe()` decorator
2. Re-run evaluation
3. Visit: https://us.cloud.langfuse.com/traces
4. Filter by your run name
5. Explore scores and analytics

---

## 📚 Next Steps

1. **Short-term** (This Week):
   - ✅ View results in local JSON files
   - ⏳ Update offline_evaluation.py for Langfuse v3.x SDK
   - ⏳ Test Langfuse dashboard integration

2. **Medium-term** (Next Week):
   - ⏳ Create custom dashboards in Langfuse
   - ⏳ Set up alerts for low scores
   - ⏳ Integrate with CI/CD pipeline

3. **Long-term** (Next Month):
   - ⏳ A/B test different models
   - ⏳ Track performance trends
   - ⏳ Automated regression detection

---

## 🔗 Quick Links

- **Local Results**: `/Users/vishal/genai/1/basic-agent/langfuse/llm-as-judge/results/`
- **Langfuse Dashboard**: https://us.cloud.langfuse.com
- **Dataset Page**: https://us.cloud.langfuse.com/datasets/correctness-eval-golden
- **Langfuse Docs**: https://langfuse.com/docs
- **Evaluation Docs**: `SOLUTION_PLAN.md`

---

**Need Help?**
- Check `SOLUTION_PLAN.md` for complete workflow
- Review `README.md` for technical details  
- Check `QUICKSTART.md` for quick commands
