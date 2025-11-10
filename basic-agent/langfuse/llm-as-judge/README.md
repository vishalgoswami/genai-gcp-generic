# LLM-as-Judge Evaluation with Langfuse

Comprehensive implementation of LLM-as-Judge evaluation for correctness, following Langfuse best practices.

## Overview

This implementation provides:
- ✅ **Offline Evaluation**: Evaluate models on curated datasets
- ✅ **Online Evaluation**: Evaluate production traces in real-time
- ✅ **Golden Dataset**: 25 test cases across multiple categories
- ✅ **Correctness Evaluators**: Multiple prompt templates for different use cases
- ✅ **Result Analytics**: Detailed reporting and visualization

## Directory Structure

```
langfuse/llm-as-judge/
├── datasets/
│   └── golden_dataset.json          # 25 golden test cases
├── evaluators/
│   └── correctness_template.py      # Evaluator prompt templates
├── scripts/
│   ├── upload_dataset.py            # Upload dataset to Langfuse
│   ├── offline_evaluation.py        # Evaluate on datasets
│   └── online_evaluation.py         # Evaluate production traces
├── results/                          # Evaluation results (auto-generated)
└── README.md                         # This file
```

## Golden Dataset

The dataset includes 25 carefully crafted test cases across:

### Categories
- **Factual Knowledge** - Basic facts and general knowledge
- **Mathematical Reasoning** - Math problems and calculations
- **Programming Concepts** - Code generation and explanation
- **Logical Reasoning** - Logic puzzles and deduction
- **Safety (Harmful/PII)** - Testing safety guardrails
- **Multi-step Reasoning** - Complex problem solving
- **Context Understanding** - Contextual awareness
- **Ambiguity Handling** - Dealing with unclear inputs
- **Instruction Following** - Following specific instructions
- **Creative Generation** - Creative tasks (haiku, etc.)
- **Data Analysis** - Analyzing trends and patterns
- **Edge Case Handling** - Undefined operations, etc.
- **Comparison Analysis** - Comparing technologies/concepts
- **And more...**

### Difficulty Levels
- **Easy** - Basic questions with clear answers
- **Medium** - Moderate complexity requiring reasoning
- **Hard** - Complex multi-step problems

## Quick Start

### 1. Upload Golden Dataset to Langfuse

```bash
cd basic-agent/langfuse/llm-as-judge/scripts
python upload_dataset.py
```

This creates a dataset named `correctness-eval-golden` in your Langfuse project.

### 2. Run Offline Evaluation

Evaluate a model on the golden dataset:

```bash
python offline_evaluation.py \
  --dataset correctness-eval-golden \
  --model gemini-1.5-flash \
  --judge gemini-1.5-pro
```

**Options:**
- `--dataset`: Dataset name in Langfuse
- `--model`: Model to test (e.g., `gemini-1.5-flash`, `gemini-1.5-pro`)
- `--judge`: Judge model for evaluation
- `--run-name`: Custom name for this evaluation run
- `--sample N`: Evaluate only N random samples

### 3. Run Online Evaluation

Evaluate recent production traces:

```bash
python online_evaluation.py \
  --trace-name rag \
  --hours 24 \
  --limit 10 \
  --sampling 1.0 \
  --judge gemini-1.5-flash
```

**Options:**
- `--trace-name`: Filter traces by name
- `--hours N`: Look back N hours
- `--limit N`: Evaluate max N traces
- `--sampling 0.X`: Sample X% of traces (e.g., 0.1 = 10%)
- `--judge`: Judge model

## Evaluator Templates

### 1. Comprehensive Correctness Evaluator

Multi-dimensional evaluation with detailed rubric:

**Dimensions:**
- Factual Accuracy (0-10)
- Completeness (0-10)
- Relevance (0-10)
- Reasoning Quality (0-10)
- Safety (0-10)

**Usage:**
```python
from evaluators.correctness_template import get_evaluator_prompt

prompt = get_evaluator_prompt("comprehensive")
```

### 2. Simple Correctness Evaluator

Quick binary correctness check:

```python
prompt = get_evaluator_prompt("simple")
```

### 3. Without Reference Evaluator

For production traces without expected answers:

```python
prompt = get_evaluator_prompt("without_reference")
```

### 4. G-Eval Style Evaluator

Research-backed evaluation methodology:

```python
prompt = get_evaluator_prompt("geval")
```

## Usage Examples

### Offline Evaluation (Dataset-Based)

```bash
# Evaluate all test cases
python offline_evaluation.py

# Evaluate sample of 10 cases
python offline_evaluation.py --sample 10

# Use different models
python offline_evaluation.py --model gemini-1.5-pro --judge gemini-1.5-flash

# Custom run name
python offline_evaluation.py --run-name "gemini-flash-v1-baseline"
```

### Online Evaluation (Production Traces)

```bash
# Evaluate last 24 hours, all traces
python online_evaluation.py

# Evaluate specific trace type
python online_evaluation.py --trace-name "friendly_agent"

# Evaluate with sampling (10% of traces)
python online_evaluation.py --sampling 0.1 --limit 100

# Last 7 days
python online_evaluation.py --hours 168
```

### Programmatic Usage

```python
import asyncio
from scripts.offline_evaluation import CorrectnessEvaluator

# Initialize evaluator
evaluator = CorrectnessEvaluator(
    judge_model="gemini-1.5-pro",
    evaluator_type="comprehensive"
)

# Evaluate a response
result = await evaluator.evaluate(
    input_text="What is the capital of France?",
    output_text="Paris",
    expected_output="Paris",
    evaluation_criteria="Must correctly identify Paris"
)

print(f"Score: {result['overall_score']}/10")
print(f"Reasoning: {result['reasoning']}")
```

## Evaluation Metrics

### Overall Correctness Score (0-10)
- **9-10**: Excellent - Completely correct and comprehensive
- **7-8**: Good - Mostly correct with minor issues
- **5-6**: Fair - Partially correct with notable gaps
- **3-4**: Poor - Significant errors or omissions
- **0-2**: Failing - Mostly incorrect

### Category-Specific Metrics
- **Factual Accuracy**: Correctness of factual claims
- **Completeness**: Coverage of all aspects
- **Relevance**: On-topic and appropriate
- **Reasoning Quality**: Logical soundness
- **Safety**: Absence of harmful content

## Results and Analytics

### Viewing Results

**Langfuse Dashboard:**
1. Navigate to: `https://us.cloud.langfuse.com/datasets/correctness-eval-golden`
2. View traces, scores, and dataset runs
3. Filter by category, score, or time period
4. Drill down into individual evaluations

**Local Results:**
- Results saved to: `results/`
- JSON format with full details
- Includes summary statistics

### Result Structure

```json
{
  "run_name": "gemini-1.5-flash-eval-20251110-120000",
  "dataset": "correctness-eval-golden",
  "model_tested": "gemini-1.5-flash",
  "judge_model": "gemini-1.5-pro",
  "timestamp": "2025-11-10T12:00:00",
  "summary": {
    "total_items": 25,
    "average_score": 8.2,
    "category_scores": {
      "factual_knowledge": 9.5,
      "mathematical_reasoning": 8.0,
      ...
    }
  },
  "results": [...]
}
```

## Best Practices

### 1. Choose the Right Judge Model

**For Production (Online Eval):**
- Use faster, cheaper models: `gemini-1.5-flash`
- Sample traces (e.g., 10-20%)
- Balance cost vs coverage

**For Development (Offline Eval):**
- Use higher-quality models: `gemini-1.5-pro`
- Evaluate full dataset
- Prioritize accuracy over cost

### 2. Evaluation Frequency

**Offline:**
- Run after model changes
- Weekly benchmark runs
- Before production deployments

**Online:**
- Continuous monitoring (sampled)
- Alert on score drops
- Daily summary reports

### 3. Cost Optimization

```python
# Offline: Sample during development
python offline_evaluation.py --sample 10

# Online: Use sampling and faster judge
python online_evaluation.py --sampling 0.1 --judge gemini-1.5-flash
```

**Estimated Costs:**
- Offline (25 items): ~$0.05-0.10 per run
- Online (10% of 1000 traces/day): ~$0.50-1.00/day

### 4. Interpreting Scores

**High scores (8-10):**
- Model performing well
- Consider edge cases
- Test harder examples

**Medium scores (5-7):**
- Identify weak categories
- Improve prompts/context
- Add training examples

**Low scores (0-4):**
- Critical issues detected
- Review safety filters
- Check model configuration

## Advanced Usage

### Custom Datasets

Create your own dataset JSON:

```json
[
  {
    "id": "custom_001",
    "category": "domain_specific",
    "input": "Your question",
    "expected_output": "Expected answer",
    "evaluation_criteria": "Evaluation rubric",
    "difficulty": "medium"
  }
]
```

Upload:
```bash
python upload_dataset.py --dataset-path my_dataset.json --name my-dataset
```

### Custom Evaluator Prompts

Edit `evaluators/correctness_template.py`:

```python
CUSTOM_EVALUATOR_PROMPT = """
Your custom evaluation prompt here...

**INPUT:** {{input}}
**OUTPUT:** {{output}}
**EXPECTED:** {{expected_output}}

[Your rubric and instructions]
"""
```

### Integration with CI/CD

```yaml
# GitHub Actions example
- name: Run Evaluation
  run: |
    cd basic-agent/langfuse/llm-as-judge/scripts
    python offline_evaluation.py --sample 10
    
    # Fail if average score < 7.0
    python -c "
    import json
    with open('../results/*.json') as f:
        result = json.load(f)
        if result['summary']['average_score'] < 7.0:
            exit(1)
    "
```

### Scheduled Online Evaluation

```bash
# Cron job for daily evaluation
0 0 * * * cd /path/to/scripts && python online_evaluation.py --hours 24 --sampling 0.1
```

## Troubleshooting

### Dataset Upload Fails

**Error:** "Dataset already exists"

**Solution:**
```bash
# Delete from Langfuse UI or use different name
python upload_dataset.py --name correctness-eval-v2
```

### Evaluation Timeout

**Error:** "Request timeout"

**Solution:**
- Reduce sample size: `--sample 5`
- Use faster judge: `--judge gemini-1.5-flash`
- Check GCP quotas

### Low Scores Unexpectedly

**Debugging:**
1. Check individual trace details in Langfuse
2. Review judge's reasoning in score comments
3. Verify model configuration
4. Test with known-good examples

### Missing Traces

**Online eval finds no traces:**
- Check time window: `--hours 168` (7 days)
- Verify trace name: `--trace-name rag`
- Confirm traces exist in Langfuse

## Cost Estimation

### Offline Evaluation

**Per run (25 items):**
- Model responses: 25 × ~500 tokens = ~$0.05
- Judge evaluations: 25 × ~1000 tokens = ~$0.10
- **Total: ~$0.15 per run**

### Online Evaluation

**Per day (1000 traces, 10% sampling):**
- 100 evaluations × ~1000 tokens = ~$1.00
- **Total: ~$30/month**

**Cost optimization:**
- Use sampling: `--sampling 0.05` (5%)
- Use cheaper judge: `gemini-1.5-flash` vs `gemini-1.5-pro`
- Focus on critical traces only

## Langfuse Dashboard

View evaluation results:

**Dataset Runs:**
`https://us.cloud.langfuse.com/datasets/correctness-eval-golden`

**Traces:**
`https://us.cloud.langfuse.com/traces?name=eval-*`

**Scores:**
`https://us.cloud.langfuse.com/scores?name=correctness*`

**Custom Dashboards:**
Create custom views filtered by:
- Score ranges
- Categories
- Time periods
- Models

## Next Steps

1. **Run initial baseline:**
   ```bash
   python upload_dataset.py
   python offline_evaluation.py
   ```

2. **Review results in Langfuse dashboard**

3. **Set up online monitoring:**
   ```bash
   python online_evaluation.py --sampling 0.1
   ```

4. **Create custom datasets for your domain**

5. **Integrate with CI/CD pipeline**

## References

- [Langfuse LLM-as-Judge Docs](https://langfuse.com/docs/scores/model-based-evals)
- [Langfuse Evaluation Guide](https://langfuse.com/docs/scores/overview)
- [G-Eval Paper](https://arxiv.org/abs/2303.16634)
- [Ragas Evaluation](https://docs.ragas.io/)

## Support

For issues or questions:
1. Check Langfuse logs in dashboard
2. Review evaluation results JSON
3. Verify GCP and Langfuse credentials
4. Check model quotas and limits

---

**Implementation Date:** November 10, 2025  
**Version:** 1.0.0  
**Langfuse Version:** 2.x  
**Cost:** Free tier compatible (monitoring costs may apply)
