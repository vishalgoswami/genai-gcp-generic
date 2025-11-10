# Custom Scores - Setup Complete! 🎉

## What Was Created

I've created a complete **programmatic scoring system** for Langfuse that doesn't require any LLM calls. Here's what you have:

### 📁 Files Created

```
langfuse/custom-scores/
├── README.md                      # Comprehensive documentation
├── .env.example                   # Environment template
├── .env                          # Your environment config (gitignored)
├── .gitignore                    # Protects sensitive files
├── setup_check.sh                # Validates configuration
├── custom_scoring.py             # Main scoring script
├── token_count_scorer.py         # Token count evaluator
└── response_latency_scorer.py    # Latency evaluator
```

### 🎯 Two Custom Scores Implemented

#### 1. **Token Count Score** (Categorical)
- **Type**: CATEGORICAL
- **Values**: LOW, MEDIUM, HIGH
- **Method**: Uses `tiktoken` to count tokens
- **No LLM needed**: Pure programmatic counting
- **Thresholds**:
  - LOW: < 100 tokens
  - MEDIUM: 100-500 tokens  
  - HIGH: > 500 tokens

#### 2. **Response Latency Score** (Numeric)
- **Type**: NUMERIC
- **Range**: 0-10
- **Method**: Calculates from trace timestamps
- **No LLM needed**: Pure math on timing data
- **Scoring**:
  - 10: < 1 second (Excellent)
  - 8-9: 1-3 seconds (Good)
  - 6-7: 3-5 seconds (Acceptable)
  - 4-5: 5-10 seconds (Slow)
  - 0-3: > 10 seconds (Very Slow)

## 🚀 Next Steps - Setup Instructions

### Step 1: Configure Credentials

You need to add your Langfuse API credentials to the `.env` file:

```bash
cd /Users/vishal/genai/1/basic-agent/langfuse/custom-scores

# Edit the .env file
nano .env  # or use your preferred editor
```

**Update these two lines:**
```bash
LANGFUSE_SECRET_KEY=sk-lf-your-actual-secret-key-here
LANGFUSE_PUBLIC_KEY=pk-lf-your-actual-public-key-here
```

**Where to get your keys:**
1. Visit: https://us.cloud.langfuse.com/settings
2. Navigate to "API Keys" section
3. Copy your Public Key and Secret Key
4. Paste them into the `.env` file

### Step 2: Verify Setup

Run the setup check script:

```bash
./setup_check.sh
```

This will verify your credentials are configured correctly.

### Step 3: Test the Scorers

Test individual scorers to make sure they work:

```bash
# Test token counting
python token_count_scorer.py

# Test latency scoring
python response_latency_scorer.py
```

### Step 4: Run Custom Scoring

Score your Langfuse traces:

```bash
# Score 10 recent traces
python custom_scoring.py --limit 10

# Score a specific trace
python custom_scoring.py --trace-id YOUR_TRACE_ID

# Score with pagination
python custom_scoring.py --limit 20 --page 2
```

## 📊 What You'll See

When you run `custom_scoring.py`, you'll get output like:

```
================================================================================
Custom Scoring - Programmatic Evaluations (No LLM)
================================================================================

Scores to apply:
  1. token_count (CATEGORICAL: LOW/MEDIUM/HIGH)
  2. response_latency (NUMERIC: 0-10)

================================================================================

Fetching traces (limit: 10, page: 1)

Found 10 trace(s)

[1/10] agent-query (abc123...)
  ✅ Token Count: MEDIUM (247 tokens)
  ✅ Response Latency: 8.5/10 (1.50s)

[2/10] agent-query (def456...)
  ✅ Token Count: LOW (89 tokens)
  ✅ Response Latency: 10.0/10 (0.75s)

...

================================================================================
SUMMARY
================================================================================

Total traces processed: 10

Scores created:
  - token_count: 10/10
  - response_latency: 10/10

✅ Custom scoring complete!

View scores in Langfuse dashboard:
  https://us.cloud.langfuse.com/scores
```

## 🎨 View in Langfuse Dashboard

Once scores are created, you can:

1. **View All Scores**: https://us.cloud.langfuse.com/scores
2. **Filter by Token Count**: `score.name = "token_count"`
3. **Filter by Latency**: `score.name = "response_latency"`
4. **Find Slow Responses**: `score.name = "response_latency" AND value < 7`
5. **Find Verbose Responses**: `score.name = "token_count" AND value = "HIGH"`

## 💡 Key Benefits

✅ **Zero LLM Costs**: No API calls to judge models  
✅ **Instant Results**: Scores computed in milliseconds  
✅ **100% Deterministic**: Same input = same output every time  
✅ **Real-time Ready**: Can run immediately after trace creation  
✅ **Cost Effective**: Free to run at any scale  

## 🆚 Comparison with LLM-as-Judge

| Aspect | Custom Scores | LLM-as-Judge |
|--------|---------------|--------------|
| **Speed** | < 100ms | 1-5 seconds |
| **Cost** | $0 | ~$0.001-0.01 per eval |
| **Use Case** | Quantitative metrics | Qualitative assessment |
| **Best For** | Token count, latency, format validation | Correctness, relevance, toxicity |

**Recommendation**: Use both together! 
- Custom scores for quantitative metrics
- LLM-as-judge for qualitative evaluation

## 📚 Documentation

Full documentation is in `README.md` including:
- Detailed usage examples
- Score interpretation guides
- Dashboard filtering tips
- Continuous monitoring setup
- Alert threshold recommendations
- How to add more custom scorers

## 🔧 Troubleshooting

**Issue**: "Langfuse credentials not found"  
**Solution**: Make sure you've updated the `.env` file with your actual API keys

**Issue**: "ModuleNotFoundError: No module named 'tiktoken'"  
**Solution**: Install dependencies: `pip install tiktoken python-dotenv`

**Issue**: "No input/output found in trace"  
**Solution**: Your traces need observations with type="GENERATION" and proper input/output fields

## 🎯 What's Different from LLM-as-Judge?

The `/langfuse/llm-as-judge` folder contains:
- **5 LLM-based evaluators**: correctness, toxicity, hallucination, relevance, conciseness
- **Uses Gemini model**: Each evaluation costs ~$0.001-0.01
- **Takes 1-5 seconds**: Per evaluation (LLM inference time)
- **Qualitative**: Subjective quality assessment

The `/langfuse/custom-scores` folder contains:
- **2 programmatic scorers**: token_count, response_latency
- **No LLM needed**: Pure computation
- **Takes < 100ms**: Per evaluation (instant)
- **Quantitative**: Objective metrics

**Use both together for comprehensive monitoring!**

---

## 📖 Reference Documentation

- [Langfuse Custom Scores Docs](https://langfuse.com/docs/evaluation/evaluation-methods/custom-scores)
- [Token Counting with tiktoken](https://github.com/openai/tiktoken)
- [LLM-as-Judge Documentation](../llm-as-judge/SOLUTION_PLAN.md)

---

**Ready to start?** Just update your `.env` file with Langfuse credentials and run `python custom_scoring.py --limit 10`! 🚀
