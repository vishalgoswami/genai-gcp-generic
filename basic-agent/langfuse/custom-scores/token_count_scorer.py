"""
Token Count Scorer - Categorical Score (HIGH/MEDIUM/LOW)

This scorer evaluates responses based on their token count without using any LLM.
It categorizes responses into HIGH, MEDIUM, or LOW token usage.

Score Type: CATEGORICAL
Values: LOW, MEDIUM, HIGH
Data Type: String-based categorical score

Thresholds:
- LOW: < 100 tokens (concise responses)
- MEDIUM: 100-500 tokens (balanced responses)
- HIGH: > 500 tokens (detailed/verbose responses)
"""

import tiktoken
from typing import Tuple, Optional


class TokenCountScorer:
    """
    Scores responses based on token count using categorical labels.
    
    This is a programmatic scorer that doesn't require LLM evaluation.
    Useful for monitoring verbosity and response length patterns.
    """
    
    def __init__(self, model_name: str = "gpt-4"):
        """
        Initialize the token counter.
        
        Args:
            model_name: Model encoding to use (default: gpt-4)
                       Supports: gpt-4, gpt-3.5-turbo, text-embedding-ada-002
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Define thresholds
        self.LOW_THRESHOLD = 100
        self.MEDIUM_THRESHOLD = 500
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            print(f"Warning: Error counting tokens: {e}")
            # Fallback to rough estimation: ~4 chars per token
            return len(text) // 4
    
    def categorize_token_count(self, token_count: int) -> str:
        """
        Categorize token count into LOW, MEDIUM, or HIGH.
        
        Args:
            token_count: Number of tokens
            
        Returns:
            Category string: "LOW", "MEDIUM", or "HIGH"
        """
        if token_count < self.LOW_THRESHOLD:
            return "LOW"
        elif token_count < self.MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def score_response(self, response_text: str) -> Tuple[str, int, str]:
        """
        Score a response based on its token count.
        
        Args:
            response_text: The response text to score
            
        Returns:
            Tuple of (category, token_count, comment)
        """
        token_count = self.count_tokens(response_text)
        category = self.categorize_token_count(token_count)
        
        # Generate explanatory comment
        if category == "LOW":
            comment = f"Concise response: {token_count} tokens (< {self.LOW_THRESHOLD})"
        elif category == "MEDIUM":
            comment = f"Balanced response: {token_count} tokens ({self.LOW_THRESHOLD}-{self.MEDIUM_THRESHOLD})"
        else:
            comment = f"Detailed response: {token_count} tokens (> {self.MEDIUM_THRESHOLD})"
        
        return category, token_count, comment
    
    def score_input_and_response(
        self, 
        input_text: str, 
        response_text: str
    ) -> Tuple[str, dict, str]:
        """
        Score both input and response, providing a combined category.
        
        Args:
            input_text: The input/question text
            response_text: The response text
            
        Returns:
            Tuple of (category, data_dict, comment)
            - category: Overall response category
            - data_dict: Dictionary with input_tokens, response_tokens, total_tokens
            - comment: Explanation of the score
        """
        input_tokens = self.count_tokens(input_text)
        response_tokens = self.count_tokens(response_text)
        total_tokens = input_tokens + response_tokens
        
        # Score based on response only (most important)
        category = self.categorize_token_count(response_tokens)
        
        data = {
            "input_tokens": input_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "category": category
        }
        
        comment = (
            f"Response: {response_tokens} tokens ({category}), "
            f"Input: {input_tokens} tokens, "
            f"Total: {total_tokens} tokens"
        )
        
        return category, data, comment


def get_token_category_mapping() -> dict:
    """
    Get the categorical mapping for Langfuse score config.
    
    Returns:
        Dictionary mapping categories to their descriptions
    """
    return {
        "LOW": "Concise response (< 100 tokens)",
        "MEDIUM": "Balanced response (100-500 tokens)",
        "HIGH": "Detailed response (> 500 tokens)"
    }


# Example usage
if __name__ == "__main__":
    scorer = TokenCountScorer()
    
    # Test examples
    test_cases = [
        ("What is Python?", "Python is a programming language."),
        ("What is Python?", "Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991. Python supports multiple programming paradigms including procedural, object-oriented, and functional programming."),
        ("Explain machine learning", "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It involves algorithms that can identify patterns in data, make predictions, and adapt to new information. The field encompasses supervised learning (with labeled data), unsupervised learning (finding patterns in unlabeled data), and reinforcement learning (learning through trial and error). Applications range from recommendation systems and image recognition to natural language processing and autonomous vehicles. Modern machine learning leverages neural networks and deep learning architectures to solve increasingly complex problems across various domains.")
    ]
    
    print("Token Count Scorer - Test Results\n")
    print("=" * 80)
    
    for i, (input_text, response_text) in enumerate(test_cases, 1):
        category, data, comment = scorer.score_input_and_response(input_text, response_text)
        
        print(f"\nTest Case {i}:")
        print(f"Input: {input_text[:60]}...")
        print(f"Response: {response_text[:60]}...")
        print(f"Category: {category}")
        print(f"Data: {data}")
        print(f"Comment: {comment}")
        print("-" * 80)
