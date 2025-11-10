# LLM-as-Judge Solution Plan
**Complete Workflow: Dataset → Offline Evaluation → Online Evaluation**

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Phase 1: Dataset Management](#phase-1-dataset-management)
4. [Phase 2: Offline Evaluation](#phase-2-offline-evaluation)
5. [Phase 3: Online Evaluation](#phase-3-online-evaluation)
6. [Phase 4: Production Monitoring](#phase-4-production-monitoring)
7. [Cost Analysis](#cost-analysis)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

### What is LLM-as-Judge?
LLM-as-Judge is a methodology where a powerful LLM (the "judge") evaluates the quality of responses from another LLM (the "test model"). This provides:
- **Automated quality assessment** without manual human review
- **Scalable evaluation** across thousands of test cases
- **Consistent scoring** with detailed reasoning
- **Multi-dimensional metrics** (accuracy, completeness, relevance, safety)

### Our Implementation
- **Test Model**: Gemini 1.5 Flash (generates responses)
- **Judge Model**: Gemini 1.5 Pro (evaluates responses)
- **Platform**: Langfuse (trace storage and analysis)
- **Evaluation Types**: Offline (dataset-based) + Online (production traces)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM-as-Judge System                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Golden Dataset  │  ← 25 curated test cases with expected outputs
│  (JSON file)     │
└────────┬─────────┘
         │
         │ upload_dataset.py
         ▼
┌──────────────────┐
│    Langfuse      │  ← Dataset storage (web UI accessible)
│    Dataset       │
└────────┬─────────┘
         │
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OFFLINE EVALUATION                           │
│  (Batch evaluation on curated dataset)                          │
└─────────────────────────────────────────────────────────────────┘
         │
         │ offline_evaluation.py
         │
         ├─────────────────────────────────────────────────┐
         │                                                 │
         ▼                                                 ▼
┌──────────────────┐                            ┌──────────────────┐
│  Test Model      │  Generate responses        │  Judge Model     │
│  Gemini Flash    │  ────────────────────────► │  Gemini Pro      │
│                  │                            │                  │
│  Input: Question │                            │  Evaluates:      │
│  Output: Answer  │                            │  - Accuracy      │
└──────────────────┘                            │  - Completeness  │
                                                │  - Relevance     │
                                                │  - Safety        │
                                                │  Output: Score   │
                                                └────────┬─────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │  Langfuse        │
                                                │  Traces + Scores │
                                                │  Results JSON    │
                                                └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ONLINE EVALUATION                            │
│  (Continuous evaluation of production traces)                   │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Production Agent Usage
         │
         ▼
┌──────────────────┐
│  Agent Creates   │  ← agent.py with Langfuse integration
│  Langfuse Traces │     Captures: input, output, metadata
└────────┬─────────┘
         │
         │ online_evaluation.py (scheduled/triggered)
         │
         ▼
┌──────────────────┐
│  Judge Model     │  Evaluates WITHOUT reference answers
│  Gemini Pro      │  (no expected_output available)
│                  │
│  Evaluates:      │
│  - Relevance     │
│  - Helpfulness   │
│  - Safety        │
│  - Coherence     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Langfuse        │  ← Scores attached to production traces
│  Production      │     Analytics, alerts, dashboards
│  Monitoring      │
└──────────────────┘
```

---

## 📦 Phase 1: Dataset Management

### ✅ COMPLETED: Dataset Upload

**What We Have:**
- ✅ 25 test cases in `datasets/golden_dataset.json`
- ✅ 20+ categories (factual, programming, safety, reasoning, etc.)
- ✅ Difficulty levels: easy (9), medium (13), hard (3)
- ✅ Uploaded to Langfuse: https://us.cloud.langfuse.com/datasets/correctness-eval-golden

**Dataset Structure:**
```json
{
  "id": "test_001",
  "category": "factual_knowledge",
  "input": "What is the capital of France?",
  "expected_output": "Paris",
  "evaluation_criteria": "Answer should be exactly 'Paris'",
  "difficulty": "easy"
}
```

**Key Commands:**
```bash
# View dataset
cd /Users/vishal/genai/1/basic-agent/langfuse/llm-as-judge/scripts

# Re-upload dataset (if needed)
python upload_dataset.py

# Upload with custom name
python upload_dataset.py --name my-custom-dataset

# Overwrite existing dataset
python upload_dataset.py --overwrite
```

**What's in Langfuse:**
- Dataset name: `correctness-eval-golden`
- Items: 25 dataset items
- Metadata: categories, difficulty, evaluation criteria
- Web UI: Browse, search, filter test cases

---

## 🔬 Phase 2: Offline Evaluation

### Purpose
Evaluate your model's performance on a curated dataset with known correct answers.

### How It Works

1. **Fetch Dataset** from Langfuse
2. **Generate Responses** using Test Model (Gemini Flash)
3. **Evaluate Responses** using Judge Model (Gemini Pro)
4. **Store Results** in Langfuse + local JSON files

### Step-by-Step Process

#### Step 1: Run Offline Evaluation

```bash
cd /Users/vishal/genai/1/basic-agent/langfuse/llm-as-judge/scripts

# Run on all 25 test cases
python offline_evaluation.py

# Run on sample (5 cases) for quick testing
python offline_evaluation.py --sample 5

# Specify models
python offline_evaluation.py \
  --model gemini-1.5-flash \
  --judge gemini-1.5-pro \
  --sample 10

# Custom run name
python offline_evaluation.py --run-name "experiment-v1"

# Specific dataset
python offline_evaluation.py --dataset my-custom-dataset
```

#### Step 2: What Happens During Evaluation

```
For each test case in dataset:

1. GENERATE RESPONSE
   Input:     "What is the capital of France?"
   Model:     Gemini 1.5 Flash
   Output:    "The capital of France is Paris."

2. EVALUATE WITH JUDGE
   Input to Judge:
   - Question: "What is the capital of France?"
   - Expected Answer: "Paris"
   - Actual Answer: "The capital of France is Paris."
   - Criteria: "Answer should be exactly 'Paris'"
   
   Judge Model: Gemini 1.5 Pro
   
   Judge Output:
   {
     "factual_accuracy": 10,
     "completeness": 10,
     "relevance": 10,
     "reasoning_quality": 10,
     "safety": 10,
     "overall_score": 10,
     "reasoning": "The response correctly identifies Paris..."
   }

3. STORE IN LANGFUSE
   - Trace: Full conversation (input → output)
   - Score: Multi-dimensional evaluation
   - Metadata: Category, difficulty, model used
   
4. SAVE TO JSON
   - Location: results/offline-eval-{timestamp}.json
   - Contains: All responses, scores, statistics
```

#### Step 3: Review Results

**Langfuse Dashboard:**
```
https://us.cloud.langfuse.com/traces
- Filter by run name
- View traces with scores
- Analyze by category
- Compare runs
```

**Local JSON Results:**
```bash
# View results
cat results/offline-eval-*.json | jq '.'

# Results structure:
{
  "run_info": {
    "run_name": "offline-eval-2025-11-10",
    "dataset_name": "correctness-eval-golden",
    "total_cases": 25,
    "test_model": "gemini-1.5-flash",
    "judge_model": "gemini-1.5-pro"
  },
  "overall_statistics": {
    "average_score": 8.7,
    "median_score": 9.0,
    "pass_rate": 0.92,  // % with score >= 7
    "total_cost": 0.12
  },
  "category_breakdown": {
    "factual_knowledge": {
      "count": 1,
      "average_score": 10.0,
      "pass_rate": 1.0
    },
    "programming_concepts": {
      "count": 1,
      "average_score": 8.5,
      "pass_rate": 1.0
    },
    // ... more categories
  },
  "detailed_results": [
    {
      "id": "test_001",
      "category": "factual_knowledge",
      "input": "What is the capital of France?",
      "expected_output": "Paris",
      "model_output": "The capital of France is Paris.",
      "scores": {
        "factual_accuracy": 10,
        "completeness": 10,
        "overall_score": 10
      },
      "judge_reasoning": "Perfect accuracy...",
      "langfuse_url": "https://us.cloud.langfuse.com/trace/abc123"
    }
    // ... 24 more results
  ]
}
```

#### Step 4: Analyze Performance

**Questions to Answer:**
- What's the overall pass rate?
- Which categories perform poorly?
- Which difficulty level has issues?
- Are there systematic failures?
- How much does it cost per evaluation?

**Example Analysis:**
```bash
cd results

# View summary
python -c "
import json
with open('offline-eval-latest.json') as f:
    data = json.load(f)
    print(f'Pass Rate: {data[\"overall_statistics\"][\"pass_rate\"]*100:.1f}%')
    print(f'Avg Score: {data[\"overall_statistics\"][\"average_score\"]:.2f}')
    print(f'Cost: ${data[\"overall_statistics\"][\"total_cost\"]:.4f}')
"

# Find failing cases (score < 7)
jq '.detailed_results[] | select(.scores.overall_score < 7) | {id, category, score: .scores.overall_score}' \
  offline-eval-latest.json
```

### Offline Evaluation Use Cases

1. **Model Comparison**
   ```bash
   # Evaluate with different models
   python offline_evaluation.py --model gemini-1.5-flash --run-name flash-v1
   python offline_evaluation.py --model gemini-1.5-pro --run-name pro-v1
   # Compare results in Langfuse
   ```

2. **Regression Testing**
   ```bash
   # Before deployment
   python offline_evaluation.py --run-name pre-deploy
   # After deployment
   python offline_evaluation.py --run-name post-deploy
   # Compare: Did quality regress?
   ```

3. **Prompt Engineering**
   ```bash
   # Test different prompts
   # (Edit agent.py with new prompt)
   python offline_evaluation.py --run-name prompt-v1
   python offline_evaluation.py --run-name prompt-v2
   # Which prompt performs better?
   ```

---

## 🌐 Phase 3: Online Evaluation

### Purpose
Evaluate real production traces to monitor quality in the wild.

### Key Differences from Offline

| Aspect | Offline | Online |
|--------|---------|--------|
| **Data Source** | Curated golden dataset | Real production traces |
| **Expected Outputs** | ✅ Yes (for comparison) | ❌ No (unknown) |
| **Evaluation Style** | Correctness (with reference) | Quality (without reference) |
| **Frequency** | On-demand / CI/CD | Continuous / Scheduled |
| **Cost** | Low (25 cases) | Higher (depends on traffic) |
| **Purpose** | Model validation | Production monitoring |

### Prerequisites

#### 1. Agent Must Create Langfuse Traces

Your agent must be integrated with Langfuse to create traces:

```python
# In agent.py (example)
from langfuse import Langfuse

class YourAgent:
    def __init__(self):
        self.langfuse = Langfuse()
    
    async def send_message(self, user_input: str):
        # Create trace
        trace = self.langfuse.trace(
            name="agent-chat",
            input={"message": user_input},
            metadata={
                "user_id": "user123",
                "session_id": "session456"
            }
        )
        
        # Generate response
        response = await self.generate_response(user_input)
        
        # Update trace with output
        trace.update(
            output={"response": response}
        )
        
        return response
```

**Verify Traces Exist:**
```bash
# Check Langfuse dashboard
https://us.cloud.langfuse.com/traces

# Should see traces from your agent
# Each trace contains: input, output, timestamp, metadata
```

#### 2. Ensure Enough Production Data

Online evaluation needs traces to evaluate. Options:

**Option A: Generate Test Traffic**
```bash
# Use your agent to create some traces
cd /Users/vishal/genai/1/basic-agent

# Run agent and ask questions
python -c "
import asyncio
from agent import FriendlyAgentRunner

async def test():
    runner = FriendlyAgentRunner()
    await runner.initialize()
    
    # Ask several questions
    questions = [
        'What is Python?',
        'How do I sort a list?',
        'Explain async/await',
        'What is machine learning?',
        'Write a hello world program'
    ]
    
    for q in questions:
        response, _ = await runner.send_message(q)
        print(f'Q: {q}')
        print(f'A: {response[:100]}...\n')

asyncio.run(test())
"
```

**Option B: Use Real Production Traffic**
- Wait for users to interact with your deployed agent
- Cloud Run deployment generates traces automatically

### Step-by-Step Process

#### Step 1: Run Online Evaluation

```bash
cd /Users/vishal/genai/1/basic-agent/langfuse/llm-as-judge/scripts

# Evaluate recent traces (last 24 hours)
python online_evaluation.py

# Evaluate last 1 hour
python online_evaluation.py --hours 1

# Evaluate last 7 days
python online_evaluation.py --hours 168

# Filter by trace name
python online_evaluation.py --trace-name "agent-chat"

# Sample 10% of traces (cost optimization)
python online_evaluation.py --sampling 0.1

# Limit number of traces
python online_evaluation.py --limit 50

# Combine filters
python online_evaluation.py \
  --hours 24 \
  --trace-name "agent-chat" \
  --sampling 0.1 \
  --limit 100
```

#### Step 2: What Happens During Online Evaluation

```
For each production trace:

1. FETCH TRACE FROM LANGFUSE
   Trace ID: abc123
   Input:    "How do I reverse a string in Python?"
   Output:   "You can reverse a string using [::-1]..."
   Metadata: {user_id, timestamp, session_id}
   
   ⚠️  NO EXPECTED OUTPUT (unknown what's "correct")

2. EVALUATE WITHOUT REFERENCE
   Input to Judge:
   - Question: "How do I reverse a string in Python?"
   - Answer: "You can reverse a string using [::-1]..."
   - Criteria: General quality (no reference to compare)
   
   Judge Model: Gemini 1.5 Pro
   Uses template: CORRECTNESS_WITHOUT_REFERENCE_PROMPT
   
   Judge Output:
   {
     "relevance": 9,        // Does it answer the question?
     "helpfulness": 9,      // Is it useful?
     "accuracy": 8,         // Is it correct? (best guess)
     "completeness": 7,     // Does it cover the topic?
     "safety": 10,          // Any harmful content?
     "overall_score": 8.6,
     "reasoning": "Good technical answer..."
   }

3. ATTACH SCORE TO TRACE
   - Score added to existing trace in Langfuse
   - Visible in trace detail view
   - Queryable for analytics

4. AGGREGATE STATISTICS
   - Average score across all traces
   - Score distribution
   - Trends over time
```

#### Step 3: Review Online Evaluation Results

**Langfuse Dashboard:**
```
https://us.cloud.langfuse.com/traces

View:
- Traces with attached scores
- Filter by score range (e.g., score < 7)
- Time-series: quality over time
- Alerts: when quality drops

Analyze:
- Which traces scored poorly?
- Are there patterns in low-scoring traces?
- Quality trends: improving or degrading?
```

**Example Queries:**
```bash
# Find low-quality traces
# In Langfuse UI:
Filter: scores.overall_score < 7
Sort: timestamp DESC

# Analyze common issues in low-scoring traces
```

#### Step 4: Set Up Continuous Monitoring

**Option A: Manual Scheduled Runs**
```bash
# Add to crontab
# Run every hour
0 * * * * cd /path/to/scripts && python online_evaluation.py --hours 1 --sampling 0.1

# Run daily at midnight
0 0 * * * cd /path/to/scripts && python online_evaluation.py --hours 24 --sampling 0.1
```

**Option B: Cloud Scheduler (Recommended for Production)**
```bash
# Create Cloud Scheduler job
gcloud scheduler jobs create http online-eval-hourly \
  --location=us-central1 \
  --schedule="0 * * * *" \
  --uri="https://your-cloud-run-url/evaluate" \
  --http-method=POST

# Your Cloud Run service should have endpoint:
# POST /evaluate -> triggers online_evaluation.py
```

**Option C: Event-Driven (Advanced)**
```python
# Evaluate after every N traces
# In agent.py:
trace_count = 0

async def send_message(self, user_input):
    # ... create trace ...
    
    trace_count += 1
    if trace_count % 100 == 0:
        # Trigger evaluation
        subprocess.run(["python", "scripts/online_evaluation.py", "--limit", "10"])
```

### Online Evaluation Use Cases

1. **Quality Monitoring**
   - Track average score over time
   - Alert when score drops below threshold
   - Identify quality regressions

2. **A/B Testing**
   ```bash
   # Tag traces with variant
   trace.update(metadata={"variant": "A"})
   
   # Evaluate each variant
   python online_evaluation.py --trace-name "agent-chat-A"
   python online_evaluation.py --trace-name "agent-chat-B"
   ```

3. **Incident Detection**
   - Sudden drop in quality → investigate
   - High safety violations → alert immediately
   - Pattern changes → model drift?

---

## 📊 Phase 4: Production Monitoring

### Dashboard Setup

**Langfuse Built-in Analytics:**
1. Go to https://us.cloud.langfuse.com/analytics
2. Create dashboard with:
   - Average score over time (line chart)
   - Score distribution (histogram)
   - Category breakdown (bar chart)
   - Low-scoring traces (table)

**Custom Dashboards:**
```python
# Export data for custom viz
from langfuse import Langfuse

langfuse = Langfuse()

# Get scores for last 7 days
scores = langfuse.get_scores(
    name="correctness",
    from_timestamp=datetime.now() - timedelta(days=7)
)

# Analyze in pandas/matplotlib
import pandas as pd
df = pd.DataFrame([{
    'timestamp': s.timestamp,
    'value': s.value,
    'trace_id': s.trace_id
} for s in scores])

# Plot trends
df.plot(x='timestamp', y='value', kind='line')
```

### Alerting

**Simple Email Alerts:**
```python
# In online_evaluation.py, add:
def check_quality_threshold(avg_score, threshold=7.0):
    if avg_score < threshold:
        send_alert(
            subject="⚠️ Quality Alert",
            message=f"Average score dropped to {avg_score:.2f}"
        )

def send_alert(subject, message):
    # Use SendGrid, AWS SES, or Gmail SMTP
    pass
```

**Langfuse Webhooks (Advanced):**
```bash
# Configure webhook in Langfuse UI
# Trigger on: score < 7
# Send to: https://your-alert-service.com/webhook
```

### Cost Optimization for Online Evaluation

**Problem:** Evaluating every production trace can be expensive.

**Solutions:**

1. **Sampling** (Recommended)
   ```bash
   # Evaluate only 10% of traces
   python online_evaluation.py --sampling 0.1
   
   # 1000 daily traces × 10% = 100 evaluations/day
   # Cost: ~$1.50/day vs $15/day (full evaluation)
   ```

2. **Smart Filtering**
   ```bash
   # Only evaluate traces from new users
   python online_evaluation.py --metadata-filter "new_user=true"
   
   # Only evaluate long responses (more likely to have issues)
   # (Add filter in online_evaluation.py code)
   ```

3. **Time-based Sampling**
   ```bash
   # Evaluate heavily during business hours, lightly at night
   # 9am-5pm: 50% sampling
   # 5pm-9am: 5% sampling
   ```

4. **Adaptive Sampling**
   ```python
   # In online_evaluation.py:
   # If recent scores are good → sample less
   # If recent scores drop → sample more
   
   def get_adaptive_sampling_rate():
       recent_avg = get_recent_average_score()
       if recent_avg > 8:
           return 0.05  # 5% sampling
       elif recent_avg > 7:
           return 0.10  # 10% sampling
       else:
           return 0.30  # 30% sampling (investigate!)
   ```

---

## 💰 Cost Analysis

### Offline Evaluation Costs

**Per Run (25 test cases):**
```
Test Model (Gemini 1.5 Flash):
- Input: 25 questions × 50 tokens = 1,250 tokens
- Output: 25 responses × 100 tokens = 2,500 tokens
- Cost: $0.000075 (input) + $0.0003 (output) = $0.000375

Judge Model (Gemini 1.5 Pro):
- Input: 25 evaluations × 500 tokens = 12,500 tokens
- Output: 25 scores × 200 tokens = 5,000 tokens  
- Cost: $0.003125 (input) + $0.015 (output) = $0.018125

Total per run: ~$0.02
Runs per day: 5-10
Monthly cost: ~$3-6
```

**Verdict:** ✅ Very affordable for offline evaluation

### Online Evaluation Costs

**Scenario: 1000 daily production traces**

**Full Evaluation (100% sampling):**
```
Judge Model (Gemini 1.5 Pro):
- 1000 traces/day × 30 days = 30,000 evaluations/month
- Input: 30,000 × 500 tokens = 15M tokens
- Output: 30,000 × 200 tokens = 6M tokens
- Cost: $37.50 (input) + $180 (output) = $217.50/month
```

**10% Sampling (Recommended):**
```
Judge Model (Gemini 1.5 Pro):
- 100 traces/day × 30 days = 3,000 evaluations/month
- Input: 3,000 × 500 tokens = 1.5M tokens
- Output: 3,000 × 200 tokens = 600K tokens
- Cost: $3.75 (input) + $18 (output) = $21.75/month
```

**1% Sampling (Light monitoring):**
```
Judge Model (Gemini 1.5 Pro):
- 10 traces/day × 30 days = 300 evaluations/month
- Input: 300 × 500 tokens = 150K tokens
- Output: 300 × 200 tokens = 60K tokens
- Cost: $0.375 (input) + $1.80 (output) = $2.18/month
```

**Recommendation:**
- Start with 10% sampling: ~$22/month
- Adjust based on traffic and budget
- Use adaptive sampling for cost efficiency

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "No traces found for evaluation"
```bash
# Check if agent is creating traces
python -c "
from langfuse import Langfuse
langfuse = Langfuse()
traces = langfuse.get_traces(limit=10)
print(f'Found {len(traces.data)} traces')
"

# If 0 traces: Agent not integrated with Langfuse
# Solution: Add Langfuse tracing to agent.py
```

#### 2. "Dataset not found"
```bash
# List datasets
python -c "
from langfuse import Langfuse
langfuse = Langfuse()
datasets = langfuse.get_datasets()
for ds in datasets.data:
    print(f'{ds.name}: {ds.items} items')
"

# Re-upload if missing
cd scripts
python upload_dataset.py
```

#### 3. "Authentication failed"
```bash
# Check credentials
cd /Users/vishal/genai/1/basic-agent/langfuse/llm-as-judge
cat .env | grep LANGFUSE

# Test connection
python -c "
from langfuse import Langfuse
langfuse = Langfuse()
print('Auth:', langfuse.auth_check())
"
```

#### 4. "Scores not appearing in Langfuse"
```bash
# Flush to ensure upload
# In evaluation script, verify:
langfuse.flush()

# Wait 30 seconds for processing
# Check Langfuse UI
```

#### 5. "Costs too high"
```bash
# Current solution: Use sampling
python online_evaluation.py --sampling 0.1

# Alternative: Use cheaper judge model
# (Edit .env: JUDGE_MODEL=gemini-1.5-flash)
# Note: Lower quality evaluations
```

---

## 📚 Next Steps

### Immediate Actions

1. **Test Offline Evaluation**
   ```bash
   cd /Users/vishal/genai/1/basic-agent/langfuse/llm-as-judge/scripts
   python offline_evaluation.py --sample 5
   ```

2. **Integrate Agent with Langfuse**
   ```bash
   # Edit agent.py to create traces
   # See integration example in README.md
   ```

3. **Generate Test Traces**
   ```bash
   # Run agent to create traces
   # Then test online evaluation
   ```

4. **Test Online Evaluation**
   ```bash
   python online_evaluation.py --limit 5
   ```

### Long-term Setup

1. **Expand Golden Dataset**
   - Add more test cases
   - Cover edge cases
   - Include failure scenarios

2. **Set Up Monitoring**
   - Schedule online evaluation
   - Configure alerts
   - Build dashboards

3. **Integrate with CI/CD**
   - Run offline eval before deploy
   - Block deployment if scores drop
   - Automated regression testing

4. **Iterate and Improve**
   - Analyze failing cases
   - Improve prompts
   - Refine evaluation criteria

---

## 📖 Additional Resources

- **Langfuse Docs**: https://langfuse.com/docs/scores/model-based-evals
- **LLM-as-Judge Research**: https://arxiv.org/abs/2306.05685
- **G-Eval Paper**: https://arxiv.org/abs/2303.16634
- **Our README**: `langfuse/llm-as-judge/README.md`
- **Quick Start**: `langfuse/llm-as-judge/QUICKSTART.md`

---

**Questions?** Check `TROUBLESHOOTING.md` or review the code comments in:
- `scripts/offline_evaluation.py`
- `scripts/online_evaluation.py`
- `evaluators/correctness_template.py`
