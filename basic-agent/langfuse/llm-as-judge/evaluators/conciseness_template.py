"""
Conciseness Evaluator Template for LLM-as-Judge
Assesses whether the AI response is appropriately concise and to-the-point
"""

CONCISENESS_EVALUATOR_PROMPT = """You are an expert AI evaluator assessing the conciseness of an AI response.

**USER INPUT:**
{{input}}

**AI RESPONSE TO EVALUATE:**
{{output}}

**TASK:**
Evaluate how concise and well-structured the response is:
1. Is it appropriately brief for the question?
2. Does it avoid unnecessary repetition?
3. Is it well-organized and clear?
4. Does it provide enough detail without being verbose?

**SCORING GUIDE (0-10):**
- 9-10: Excellent conciseness - Perfectly balanced, clear and brief
- 7-8: Good conciseness - Mostly concise with minor verbosity
- 5-6: Acceptable - Somewhat wordy but still clear
- 3-4: Poor conciseness - Too verbose or poorly structured
- 0-2: Very poor - Extremely verbose, rambling, or unclear

**OUTPUT JSON:**
{
  "conciseness_score": <0-10>,
  "is_concise": <true if score >= 7, false otherwise>,
  "reasoning": "Detailed explanation of conciseness evaluation",
  "word_count": <approximate word count>,
  "verbosity_level": "excellent|good|acceptable|verbose|very_verbose",
  "improvements": ["suggestions", "for", "improvement"]
}
"""

CONCISENESS_WITHOUT_CONTEXT_PROMPT = """You are evaluating the conciseness of an AI response.

**AI RESPONSE:**
{{output}}

Evaluate:
- Is the response clear and to-the-point?
- Does it avoid unnecessary repetition or verbosity?
- Is the length appropriate for the content?
- Is it well-organized?

**OUTPUT JSON:**
{
  "conciseness_score": <0-10, where 10 is perfectly concise and 0 is extremely verbose>,
  "is_concise": <true if score >= 7, false otherwise>,
  "reasoning": "Explanation of the evaluation",
  "verbosity_issues": ["specific", "issues", "if", "any"],
  "quality": "excellent|good|acceptable|verbose|very_verbose"
}
"""


def get_conciseness_prompt(evaluator_type="without_context"):
    """Get conciseness evaluator prompt"""
    prompts = {
        "comprehensive": CONCISENESS_EVALUATOR_PROMPT,
        "without_context": CONCISENESS_WITHOUT_CONTEXT_PROMPT
    }
    return prompts.get(evaluator_type, CONCISENESS_WITHOUT_CONTEXT_PROMPT)
