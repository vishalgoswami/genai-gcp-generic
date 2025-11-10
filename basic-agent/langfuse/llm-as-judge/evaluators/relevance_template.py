"""
Relevance Evaluator Template for LLM-as-Judge
Assesses how well the AI response addresses the user's question
"""

RELEVANCE_EVALUATOR_PROMPT = """You are an expert AI evaluator assessing the relevance of an AI response to the user's question.

**USER INPUT:**
{{input}}

**AI RESPONSE TO EVALUATE:**
{{output}}

**TASK:**
Evaluate how relevant and on-topic the response is:
1. Does it directly address the user's question?
2. Does it stay focused on the topic?
3. Does it provide what the user asked for?
4. Does it avoid unnecessary tangents?

**SCORING GUIDE (0-10):**
- 9-10: Highly relevant - Perfectly addresses the question
- 7-8: Relevant - Addresses most aspects with minor tangents
- 5-6: Somewhat relevant - Partially addresses the question
- 3-4: Low relevance - Misses key points or goes off-topic
- 0-2: Irrelevant - Doesn't address the question

**OUTPUT JSON:**
{
  "relevance_score": <0-10>,
  "is_relevant": <true if score >= 7, false otherwise>,
  "reasoning": "Detailed explanation of relevance evaluation",
  "addressed_aspects": ["what", "was", "addressed"],
  "missed_aspects": ["what", "was", "missed"],
  "off_topic_content": ["any", "irrelevant", "content"]
}
"""

RELEVANCE_WITHOUT_CONTEXT_PROMPT = """You are evaluating if an AI response appears relevant and focused.

**AI RESPONSE:**
{{output}}

Evaluate:
- Does the response seem focused and coherent?
- Does it provide useful information?
- Does it avoid rambling or going off-topic?

**OUTPUT JSON:**
{
  "relevance_score": <0-10, where 10 is highly relevant and focused>,
  "is_relevant": <true if score >= 7, false otherwise>,
  "reasoning": "Explanation of the evaluation",
  "quality": "excellent|good|fair|poor"
}
"""


def get_relevance_prompt(evaluator_type="without_context"):
    """Get relevance evaluator prompt"""
    prompts = {
        "comprehensive": RELEVANCE_EVALUATOR_PROMPT,
        "without_context": RELEVANCE_WITHOUT_CONTEXT_PROMPT
    }
    return prompts.get(evaluator_type, RELEVANCE_WITHOUT_CONTEXT_PROMPT)
