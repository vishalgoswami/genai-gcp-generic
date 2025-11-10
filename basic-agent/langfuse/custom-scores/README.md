# Custom Scores - Programmatic Evaluation

This folder contains custom programmatic scoring tools for Langfuse traces that **do not require LLM-as-judge**. These scores are fast, cost-effective, and deterministic.

## 📊 Available Scores

### 1. Token Count Score (Categorical)
**File**: `token_count_scorer.py`

Categorizes responses based on token usage without any LLM calls.

- **Type**: CATEGORICAL
- **Values**: `LOW`, `MEDIUM`, `HIGH`
- **Thresholds**:
  - `LOW`: < 100 tokens (concise responses)
  - `MEDIUM`: 100-500 tokens (balanced responses)
  - `HIGH`: > 500 tokens (detailed/verbose responses)

**Use Cases**:
- Monitor response verbosity patterns
- Identify over-explanation or under-explanation
- Track token usage for cost optimization
- Ensure responses match expected length guidelines

**Example Output**:
```
Category: MEDIUM
Tokens: 247
Comment: "Balanced response: 247 tokens (100-500)"
```

### 2. Response Latency Score (Numeric)
**File**: `response_latency_scorer.py`

Scores response time performance on a 0-10 scale.

- **Type**: NUMERIC
- **Range**: 0-10
- **Score Interpretation**:
  - `10`: Excellent (< 1 second)
  - `8-9`: Good (1-3 seconds)
  - `6-7`: Acceptable (3-5 seconds)
  - `4-5`: Slow (5-10 seconds)
  - `0-3`: Very Slow (> 10 seconds)

**Use Cases**:
- Monitor response time SLAs
- Identify performance degradation
- Compare latency across different prompts/models
- Track user experience quality

**Example Output**:
```
Score: 9.2/10
Latency: 1.5s
Category: Good
Comment: "Good: 1.50s latency (score: 9.2/10)"
```

## 🚀 Quick Start

### 1. Setup Environment

First, configure your Langfuse credentials:

```bash
# Navigate to the custom-scores folder
cd basic-agent/langfuse/custom-scores

# Copy the example environment file
cp .env.example .env

# Edit .env and add your Langfuse credentials
# Get your keys from: https://us.cloud.langfuse.com/settings
nano .env  # or use your preferred editor
```

Update these values in `.env`:
```bash
LANGFUSE_SECRET_KEY=sk-lf-your-actual-secret-key
LANGFUSE_PUBLIC_KEY=pk-lf-your-actual-public-key
```

### 2. Install Dependencies

```bash
# Install required package for token counting
pip install tiktoken
```

### 3. Run Custom Scoring

```bash
# Navigate to the custom-scores folder
cd basic-agent/langfuse/custom-scores

# Score the 10 most recent traces
python custom_scoring.py --limit 10

# Score a specific trace
python custom_scoring.py --trace-id abc123def456

# Score with pagination
python custom_scoring.py --limit 20 --page 2
```

### Test Individual Scorers

```bash
# Test token count scorer
python token_count_scorer.py

# Test latency scorer
python response_latency_scorer.py
```

## 📖 How It Works

### Architecture

```
Langfuse Traces
      ↓
fetch_traces() ← HTTP API
      ↓
extract_input_output()
      ↓
┌─────────────────────┬─────────────────────┐
│   Token Counter     │   Latency Scorer    │
│  (no LLM needed)    │  (no LLM needed)    │
└─────────────────────┴─────────────────────┘
      ↓                        ↓
create_score()          create_score()
      ↓                        ↓
    Langfuse Dashboard
```

### Key Features

✅ **No LLM Required**: Pure programmatic evaluation (fast & free)  
✅ **Real-time**: Instant scoring without model inference  
✅ **Deterministic**: Same input = same output every time  
✅ **Cost-effective**: No additional API costs  
✅ **Automatic**: Works with existing trace data  

## 📝 Usage Examples

### Basic Usage

```python
from token_count_scorer import TokenCountScorer
from response_latency_scorer import ResponseLatencyScorer

# Initialize scorers
token_scorer = TokenCountScorer()
latency_scorer = ResponseLatencyScorer()

# Score token count
category, data, comment = token_scorer.score_input_and_response(
    input_text="What is Python?",
    response_text="Python is a high-level programming language..."
)
print(f"Token Category: {category}")  # OUTPUT: MEDIUM
print(f"Response Tokens: {data['response_tokens']}")  # OUTPUT: 247

# Score latency
score, latency_seconds, comment = latency_scorer.score_from_latency_ms(1500)
print(f"Latency Score: {score}/10")  # OUTPUT: 8.5/10
print(f"Performance: {comment}")  # OUTPUT: "Good: 1500ms (1.50s) latency..."
```

### Integration with Langfuse

```python
from custom_scoring import CustomScoreManager

# Initialize manager
manager = CustomScoreManager()

# Score all recent traces
manager.run(limit=50)

# Score a specific trace
manager.run(trace_id="your-trace-id-here")
```

### Programmatic Score Creation

```python
# Create token count score
manager.create_score(
    trace_id="abc123",
    name="token_count",
    value="MEDIUM",  # Categorical value
    data_type="CATEGORICAL",
    comment="Balanced response: 247 tokens",
    data={"input_tokens": 12, "response_tokens": 247, "total_tokens": 259}
)

# Create latency score
manager.create_score(
    trace_id="abc123",
    name="response_latency",
    value=8.5,  # Numeric value
    data_type="NUMERIC",
    comment="Good: 1.50s latency (score: 8.5/10)",
    data={"latency_seconds": 1.5}
)
```

## 🎯 Score Interpretation

### Token Count Categories

| Category | Token Range | Interpretation | Action |
|----------|-------------|----------------|--------|
| **LOW** | < 100 | Concise, possibly too brief | ✅ Good for simple questions<br>⚠️ May lack detail |
| **MEDIUM** | 100-500 | Balanced, appropriate length | ✅ Ideal for most use cases |
| **HIGH** | > 500 | Detailed, possibly verbose | ✅ Good for complex topics<br>⚠️ May be over-explaining |

### Latency Performance Bands

| Score | Latency | Performance | User Experience | Action |
|-------|---------|-------------|-----------------|--------|
| **10** | < 1s | Excellent | Feels instant | ✅ Maintain |
| **8-9** | 1-3s | Good | Smooth | ✅ Acceptable |
| **6-7** | 3-5s | Acceptable | Noticeable wait | ⚠️ Monitor |
| **4-5** | 5-10s | Slow | Frustrating | 🔴 Investigate |
| **0-3** | > 10s | Very Slow | Unacceptable | 🔴 Fix urgently |

## 🎛️ Configuration

### Customize Token Thresholds

Edit `token_count_scorer.py`:

```python
class TokenCountScorer:
    def __init__(self, model_name: str = "gpt-4"):
        # Modify these thresholds
        self.LOW_THRESHOLD = 100     # Change to 50 for stricter "LOW"
        self.MEDIUM_THRESHOLD = 500  # Change to 300 for stricter "MEDIUM"
```

### Customize Latency Thresholds

Edit `response_latency_scorer.py`:

```python
class ResponseLatencyScorer:
    def __init__(self):
        # Modify these thresholds (in seconds)
        self.EXCELLENT_THRESHOLD = 1.0   # Change to 0.5 for stricter SLA
        self.GOOD_THRESHOLD = 3.0        # Change to 2.0 for stricter SLA
        self.ACCEPTABLE_THRESHOLD = 5.0
        self.SLOW_THRESHOLD = 10.0
```

## 📊 Dashboard Filtering

Once scores are created, filter them in Langfuse:

1. **Navigate to Scores**: https://us.cloud.langfuse.com/scores

2. **Filter by Token Count**:
   - Filter: `score.name = "token_count"`
   - View: Group by `value` to see LOW/MEDIUM/HIGH distribution
   - Alert: Flag traces with `HIGH` token usage

3. **Filter by Latency**:
   - Filter: `score.name = "response_latency"`
   - View: Sort by `value` ascending to find slowest responses
   - Alert: Flag scores < 6.0 (slow responses)

4. **Combined Analysis**:
   - Filter: `token_count = "HIGH" AND response_latency < 7`
   - Insight: Verbose responses that are also slow
   - Action: Optimize prompts for both brevity and speed

## 🔄 Continuous Monitoring

### Set Up Automated Scoring

```bash
# Create a cron job to score new traces hourly
0 * * * * cd /path/to/custom-scores && python custom_scoring.py --limit 50
```

### Use with Cloud Scheduler (GCP)

```bash
# Create a scheduled job
gcloud scheduler jobs create http custom-scoring \
  --schedule="0 * * * *" \
  --uri="https://your-cloud-function-url" \
  --http-method=POST \
  --message-body='{"limit": 50}'
```

### Real-time Scoring

Integrate directly into your application:

```python
from langfuse import Langfuse
from token_count_scorer import TokenCountScorer
from response_latency_scorer import ResponseLatencyScorer

langfuse = Langfuse()
token_scorer = TokenCountScorer()
latency_scorer = ResponseLatencyScorer()

# After creating a trace
trace = langfuse.trace(name="user-query")
span = trace.span(name="llm-call")
# ... your LLM call here ...

# Score immediately
category, data, comment = token_scorer.score_response(response_text)
trace.score(
    name="token_count",
    value=category,
    data_type="CATEGORICAL",
    comment=comment
)

# Latency from trace timing
score, latency, comment = latency_scorer.score_from_timestamps(
    span.start_time, 
    span.end_time
)
trace.score(
    name="response_latency",
    value=score,
    data_type="NUMERIC",
    comment=comment
)
```

## 🚨 Alert Thresholds

Recommended thresholds for production monitoring:

### Token Count Alerts
- **Warning**: > 80% of responses are `HIGH`
  - *Indicates*: Over-explanation, higher costs
  - *Action*: Review prompts, add length constraints

- **Error**: > 90% of responses are `LOW`
  - *Indicates*: Insufficient detail, poor quality
  - *Action*: Review prompts, improve instructions

### Latency Alerts
- **Warning**: Average score < 7.0
  - *Indicates*: Performance degradation
  - *Action*: Review model choice, optimize prompts

- **Error**: Average score < 5.0
  - *Indicates*: Unacceptable performance
  - *Action*: Urgent investigation needed

- **Critical**: Any score < 3.0
  - *Indicates*: Individual response taking > 15s
  - *Action*: Immediate debugging required

## 🆚 Comparison: Custom Scores vs LLM-as-Judge

| Aspect | Custom Scores | LLM-as-Judge |
|--------|---------------|--------------|
| **Speed** | Instant (< 100ms) | 1-5 seconds per score |
| **Cost** | Free | ~$0.001-0.01 per evaluation |
| **Determinism** | 100% reproducible | May vary slightly |
| **Use Cases** | Quantitative metrics | Qualitative assessment |
| **Best For** | - Token usage<br>- Latency<br>- Format validation<br>- Length checks | - Correctness<br>- Relevance<br>- Toxicity<br>- Hallucination |

**Recommendation**: Use both together for comprehensive evaluation!

## 📚 Additional Scorer Ideas

You can easily add more custom scorers:

### 3. Structured Output Validator
```python
def score_json_validity(response: str) -> bool:
    try:
        json.loads(response)
        return True  # Valid JSON
    except:
        return False  # Invalid JSON
```

### 4. Keyword Coverage Score
```python
def score_keyword_coverage(response: str, required_keywords: list) -> float:
    found = sum(1 for kw in required_keywords if kw.lower() in response.lower())
    return (found / len(required_keywords)) * 10.0
```

### 5. Language Detection
```python
from langdetect import detect

def score_language(response: str, expected: str = "en") -> bool:
    detected = detect(response)
    return detected == expected
```

### 6. Sentiment Score
```python
from textblob import TextBlob

def score_sentiment(response: str) -> float:
    sentiment = TextBlob(response).sentiment.polarity
    return (sentiment + 1) * 5  # Convert -1 to 1 → 0 to 10
```

## 🔧 Troubleshooting

### Issue: "No input/output found in trace"
**Solution**: Ensure your traces have observations with `type="GENERATION"` and proper input/output fields.

### Issue: "No latency data available"
**Solution**: Traces must have `timestamp` and `endTime` fields, or observations with `startTime` and `endTime`.

### Issue: Token count seems inaccurate
**Solution**: The scorer uses tiktoken for GPT models. For other models, it estimates ~4 chars per token. Adjust the model parameter in TokenCountScorer initialization.

### Issue: Scores not appearing in dashboard
**Solution**: 
1. Check API credentials are correct
2. Verify trace IDs exist
3. Allow a few seconds for scores to sync
4. Refresh the dashboard page

## 📖 References

- [Langfuse Custom Scores Documentation](https://langfuse.com/docs/evaluation/evaluation-methods/custom-scores)
- [Langfuse Score Analytics](https://langfuse.com/docs/evaluation/evaluation-methods/score-analytics)
- [tiktoken Documentation](https://github.com/openai/tiktoken)

## 🤝 Contributing

To add a new custom scorer:

1. Create a new file: `your_scorer_name.py`
2. Implement a scorer class with a `score()` method
3. Add integration to `custom_scoring.py`
4. Update this README with documentation
5. Add tests and examples

## 📄 License

Same as the parent project.

---

**Need help?** Check the [main evaluation documentation](../llm-as-judge/SOLUTION_PLAN.md) or create an issue.
