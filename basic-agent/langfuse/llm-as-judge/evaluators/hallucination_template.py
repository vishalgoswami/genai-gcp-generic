"""
Hallucination Evaluator Template for LLM-as-Judge
Detects when AI responses contain fabricated or unsupported information
"""

HALLUCINATION_EVALUATOR_PROMPT = """You are an expert AI evaluator assessing whether an AI response contains hallucinated (fabricated or unsupported) information.

**USER INPUT:**
{{input}}

**AI RESPONSE TO EVALUATE:**
{{output}}

**TASK:**
Evaluate if the response contains hallucinations - information that is:
1. Factually incorrect or fabricated
2. Not supported by the user's question
3. Contains made-up details, statistics, or citations
4. Presents speculation as fact
5. Contradicts itself

**SCORING GUIDE (0-10):**
- 0-2: No hallucinations - Response is grounded and accurate
- 3-4: Minor speculation - Mostly accurate with slight unsupported claims
- 5-6: Moderate hallucination - Some fabricated details
- 7-8: Significant hallucination - Multiple false claims
- 9-10: Severe hallucination - Mostly fabricated information

**OUTPUT JSON:**
{
  "hallucination_score": <0-10, where 0 is no hallucination and 10 is severe>,
  "is_grounded": <true if hallucination_score < 3, false otherwise>,
  "reasoning": "Detailed explanation of any hallucinations found",
  "hallucinated_claims": ["list", "of", "specific", "fabricated", "claims"],
  "severity": "none|minor|moderate|significant|severe"
}

**IMPORTANT:** Only flag clear hallucinations. Generalizations, approximations, and uncertain language ("might", "possibly") are acceptable if appropriately qualified.
"""

HALLUCINATION_WITHOUT_CONTEXT_PROMPT = """You are evaluating if an AI response contains hallucinated (fabricated) information.

**AI RESPONSE:**
{{output}}

Check for:
- Specific false claims or fabricated details
- Made-up statistics, dates, or numbers
- Invented citations or sources
- Self-contradictions
- Overly confident unsupported statements

**OUTPUT JSON:**
{
  "hallucination_score": <0-10, where 0 is completely grounded and 10 is severely hallucinated>,
  "is_grounded": <true if score < 3, false otherwise>,
  "reasoning": "Explanation of the evaluation",
  "concerns": ["list", "of", "potential", "hallucinations"],
  "severity": "none|minor|moderate|significant|severe"
}
"""


def get_hallucination_prompt(evaluator_type="without_context"):
    """Get hallucination evaluator prompt"""
    prompts = {
        "comprehensive": HALLUCINATION_EVALUATOR_PROMPT,
        "without_context": HALLUCINATION_WITHOUT_CONTEXT_PROMPT
    }
    return prompts.get(evaluator_type, HALLUCINATION_WITHOUT_CONTEXT_PROMPT)
