# LLM-as-Judge Quick Start Guide

## What You Have

✅ **Complete LLM-as-Judge Implementation** following Langfuse best practices

### Files Created

```
basic-agent/langfuse/llm-as-judge/
├── datasets/
│   └── golden_dataset.json           # 25 test cases across 20+ categories
├── evaluators/
│   └── correctness_template.py       # 4 evaluator templates
├── scripts/
│   ├── upload_dataset.py             # Upload to Langfuse
│   ├── offline_evaluation.py         # Evaluate on datasets
│   └── online_evaluation.py          # Evaluate production traces
├── results/                           # Auto-generated results
└── README.md                          # Full documentation
```

## 3-Step Quick Start

### Step 1: Upload Golden Dataset

```bash
cd basic-agent/langfuse/llm-as-judge/scripts
python upload_dataset.py
```

This creates a dataset `correctness-eval-golden` in Langfuse with 25 test cases.

### Step 2: Run Offline Evaluation

Test your model against the golden dataset:

```bash
# Evaluate with default settings
python offline_evaluation.py

# Or test just 5 samples
python offline_evaluation.py --sample 5

# Use different models
python offline_evaluation.py --model gemini-1.5-pro --judge gemini-1.5-flash
```

### Step 3: Set Up Online Evaluation

Evaluate production traces:

```bash
# Evaluate recent traces
python online_evaluation.py --limit 10

# With sampling (10% of traces)
python online_evaluation.py --sampling 0.1 --limit 100

# Filter by trace name
python online_evaluation.py --trace-name "friendly_agent"
```

## What Gets Evaluated

### Golden Dataset Categories (25 test cases)

1. **Factual Knowledge** - "What is the capital of France?"
2. **Math Reasoning** - "If I have 5 apples..."
3. **Programming** - "Explain Python decorators"
4. **Logic** - "All birds fly. Penguins are birds..."
5. **Safety (Harmful)** - "How do I make a weapon?"
6. **Safety (PII)** - SSN handling
7. **Multi-step Reasoning** - Train problems
8. **Code Generation** - Fibonacci function
9. **Context Understanding** - Trip planning
10. **Ambiguity** - "Bank" (multiple meanings)
11. **Instruction Following** - "List 3 languages starting with P"
12. **Creative** - Write a haiku
13. **Data Analysis** - Sales trends
14. **Edge Cases** - "What is 0/0?"
15. **Comparison** - Python vs JavaScript
16. **Historical Facts** - When did WW2 end?
17. **Scientific Concepts** - Photosynthesis
18. **Ethical Reasoning** - AI replacing workers
19. **API Usage** - HTTP GET request
20. **Troubleshooting** - KeyError fix
21. **Conceptual** - ML vs Deep Learning
22. **Practical Advice** - Code performance
23. **Business Logic** - Compound interest
24. **System Design** - URL shortener
25. **Language Nuance** - Affect vs Effect

## Evaluation Metrics

Each response is scored 0-10 on:

- **Factual Accuracy** (0-10)
- **Completeness** (0-10)
- **Relevance** (0-10)
- **Reasoning Quality** (0-10)
- **Safety** (0-10)
- **Overall Correctness** (0-10)

### Score Interpretation

- **9-10**: Excellent - Perfect or near-perfect answer
- **7-8**: Good - Mostly correct, minor issues
- **5-6**: Fair - Partially correct, notable gaps
- **3-4**: Poor - Significant errors
- **0-2**: Failing - Mostly incorrect

## View Results

### In Langfuse Dashboard

1. **Dataset View:**
   ```
   https://us.cloud.langfuse.com/datasets/correctness-eval-golden
   ```

2. **Traces:**
   Filter by `name:eval-*` to see evaluation traces

3. **Scores:**
   View detailed scores with reasoning

### Local Files

Results saved to: `langfuse/llm-as-judge/results/`

```json
{
  "run_name": "gemini-1.5-flash-eval-20251110-120000",
  "summary": {
    "average_score": 8.2,
    "category_scores": {...}
  },
  "results": [...]
}
```

## Cost Estimates

### Offline Evaluation
- **25 test cases**: ~$0.10-0.15 per run
- Model responses: 25 × 500 tokens
- Judge evaluations: 25 × 1000 tokens

### Online Evaluation  
- **10% sampling, 1000 traces/day**: ~$1.00/day
- 100 evaluations × 1000 tokens

### Cost Optimization
```bash
# Sample during development
python offline_evaluation.py --sample 5  # ~$0.03

# Use cheaper judge
python online_evaluation.py --judge gemini-1.5-flash

# Lower sampling rate
python online_evaluation.py --sampling 0.05  # 5%
```

## Evaluator Templates

### 1. Comprehensive (Default)
Multi-dimensional with detailed rubric
```python
from evaluators.correctness_template import get_evaluator_prompt
prompt = get_evaluator_prompt("comprehensive")
```

### 2. Simple
Quick binary correctness check
```python
prompt = get_evaluator_prompt("simple")
```

### 3. Without Reference
For production (no expected answer)
```python
prompt = get_evaluator_prompt("without_reference")
```

### 4. G-Eval
Research-backed methodology
```python
prompt = get_evaluator_prompt("geval")
```

## Common Use Cases

### 1. Baseline Evaluation
```bash
# Establish baseline score
python offline_evaluation.py --run-name baseline-v1
```

### 2. Model Comparison
```bash
# Compare models
python offline_evaluation.py --model gemini-1.5-flash --run-name flash-v1
python offline_evaluation.py --model gemini-1.5-pro --run-name pro-v1
```

### 3. Production Monitoring
```bash
# Daily cron job
python online_evaluation.py --hours 24 --sampling 0.1
```

### 4. Category Analysis
Check results JSON for category breakdown:
```python
import json
with open('results/latest.json') as f:
    data = json.load(f)
    print(data['summary']['category_scores'])
```

## Troubleshooting

### Authentication Error
**Problem:** `Langfuse client initialized without public_key`

**Solution:**
- Ensure `USE_SECRET_MANAGER=true` in `.env`
- Verify Secret Manager has credentials
- Check IAM permissions

### No Traces Found
**Problem:** Online evaluation finds 0 traces

**Solution:**
```bash
# Increase time window
python online_evaluation.py --hours 168  # 7 days

# Check trace name
python online_evaluation.py --trace-name "rag"

# Verify traces exist in Langfuse dashboard
```

### Low Scores
**Problem:** Unexpectedly low scores

**Debug:**
1. Check Langfuse dashboard for judge reasoning
2. Review specific failing test cases
3. Test with known-good examples:
   ```bash
   python offline_evaluation.py --sample 3
   ```

## Integration Examples

### CI/CD Pipeline
```yaml
# .github/workflows/eval.yml
- name: Run Evaluation
  run: |
    python offline_evaluation.py --sample 10
    # Fail if score < 7.0
    python -c "
    import json, glob
    files = glob.glob('results/*.json')
    with open(max(files)) as f:
        if json.load(f)['summary']['average_score'] < 7.0:
            exit(1)
    "
```

### Scheduled Monitoring
```bash
# Daily at midnight
0 0 * * * cd /path/to/scripts && python online_evaluation.py --hours 24 --sampling 0.1
```

### Custom Dataset
```json
// my_dataset.json
[
  {
    "id": "test_001",
    "category": "my_category",
    "input": "My question",
    "expected_output": "Expected answer",
    "evaluation_criteria": "Must include X and Y",
    "difficulty": "medium"
  }
]
```

```bash
python upload_dataset.py --dataset-path my_dataset.json --name my-dataset
python offline_evaluation.py --dataset my-dataset
```

## Next Steps

1. ✅ **Run initial evaluation** to establish baseline
2. ✅ **Review results** in Langfuse dashboard
3. ✅ **Set up monitoring** with online evaluation
4. ✅ **Create custom datasets** for your domain
5. ✅ **Integrate** with CI/CD pipeline

## Resources

- **Full Documentation**: `README.md` in this folder
- **Langfuse Docs**: https://langfuse.com/docs/scores/model-based-evals
- **Test Cases**: `datasets/golden_dataset.json`
- **Templates**: `evaluators/correctness_template.py`

---

**Created:** November 10, 2025  
**Status:** ✅ Ready to use  
**Cost:** Free tier compatible
