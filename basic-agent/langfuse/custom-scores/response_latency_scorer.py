"""
Response Latency Scorer - Numeric Score (0-10)

This scorer evaluates responses based on their latency/response time without using any LLM.
It converts response time into a quality score where lower latency = higher score.

Score Type: NUMERIC
Range: 0-10
Data Type: Float

Score Interpretation:
- 10: Excellent (< 1 second)
- 8-9: Good (1-3 seconds)
- 6-7: Acceptable (3-5 seconds)
- 4-5: Slow (5-10 seconds)
- 0-3: Very Slow (> 10 seconds)
"""

from typing import Tuple, Optional
from datetime import datetime


class ResponseLatencyScorer:
    """
    Scores responses based on latency using a numeric scale (0-10).
    
    This is a programmatic scorer that doesn't require LLM evaluation.
    Useful for monitoring response time performance and user experience.
    """
    
    def __init__(self):
        """
        Initialize the latency scorer with threshold definitions.
        """
        # Define latency thresholds in seconds
        self.EXCELLENT_THRESHOLD = 1.0  # < 1s = 10 score
        self.GOOD_THRESHOLD = 3.0       # 1-3s = 8-9 score
        self.ACCEPTABLE_THRESHOLD = 5.0 # 3-5s = 6-7 score
        self.SLOW_THRESHOLD = 10.0      # 5-10s = 4-5 score
        # > 10s = 0-3 score
    
    def calculate_score_from_latency(self, latency_seconds: float) -> float:
        """
        Convert latency to a score (0-10).
        
        Lower latency = higher score (better performance)
        
        Args:
            latency_seconds: Response time in seconds
            
        Returns:
            Score from 0-10
        """
        if latency_seconds < 0:
            return 0.0
        
        # Excellent: < 1s
        if latency_seconds <= self.EXCELLENT_THRESHOLD:
            return 10.0
        
        # Good: 1-3s (linear interpolation from 9 to 8)
        elif latency_seconds <= self.GOOD_THRESHOLD:
            # 1s = 9.0, 3s = 8.0
            progress = (latency_seconds - self.EXCELLENT_THRESHOLD) / (
                self.GOOD_THRESHOLD - self.EXCELLENT_THRESHOLD
            )
            return 9.0 - (progress * 1.0)
        
        # Acceptable: 3-5s (linear interpolation from 7 to 6)
        elif latency_seconds <= self.ACCEPTABLE_THRESHOLD:
            # 3s = 7.0, 5s = 6.0
            progress = (latency_seconds - self.GOOD_THRESHOLD) / (
                self.ACCEPTABLE_THRESHOLD - self.GOOD_THRESHOLD
            )
            return 7.0 - (progress * 1.0)
        
        # Slow: 5-10s (linear interpolation from 5 to 4)
        elif latency_seconds <= self.SLOW_THRESHOLD:
            # 5s = 5.0, 10s = 4.0
            progress = (latency_seconds - self.ACCEPTABLE_THRESHOLD) / (
                self.SLOW_THRESHOLD - self.ACCEPTABLE_THRESHOLD
            )
            return 5.0 - (progress * 1.0)
        
        # Very Slow: > 10s (exponential decay from 3 to 0)
        else:
            # 10s = 3.0, 20s = 1.5, 30s = 0.75, etc.
            # Score = 3.0 * (0.9 ^ ((latency - 10) / 2))
            excess_time = latency_seconds - self.SLOW_THRESHOLD
            score = 3.0 * (0.9 ** (excess_time / 2.0))
            return max(0.0, min(3.0, score))
    
    def get_performance_category(self, score: float) -> str:
        """
        Get performance category based on score.
        
        Args:
            score: Score from 0-10
            
        Returns:
            Performance category string
        """
        if score >= 9.5:
            return "Excellent"
        elif score >= 8.0:
            return "Good"
        elif score >= 6.0:
            return "Acceptable"
        elif score >= 4.0:
            return "Slow"
        else:
            return "Very Slow"
    
    def score_from_timestamps(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Tuple[float, float, str]:
        """
        Calculate score from start and end timestamps.
        
        Args:
            start_time: When the request started
            end_time: When the response completed
            
        Returns:
            Tuple of (score, latency_seconds, comment)
        """
        latency_seconds = (end_time - start_time).total_seconds()
        score = self.calculate_score_from_latency(latency_seconds)
        category = self.get_performance_category(score)
        
        comment = f"{category}: {latency_seconds:.2f}s latency (score: {score:.1f}/10)"
        
        return score, latency_seconds, comment
    
    def score_from_latency_ms(self, latency_ms: float) -> Tuple[float, float, str]:
        """
        Calculate score from latency in milliseconds.
        
        Args:
            latency_ms: Response time in milliseconds
            
        Returns:
            Tuple of (score, latency_seconds, comment)
        """
        latency_seconds = latency_ms / 1000.0
        score = self.calculate_score_from_latency(latency_seconds)
        category = self.get_performance_category(score)
        
        comment = f"{category}: {latency_ms:.0f}ms ({latency_seconds:.2f}s) latency (score: {score:.1f}/10)"
        
        return score, latency_seconds, comment
    
    def score_from_trace_data(self, trace_data: dict) -> Optional[Tuple[float, float, str]]:
        """
        Extract latency from Langfuse trace data and calculate score.
        
        Args:
            trace_data: Langfuse trace dictionary
            
        Returns:
            Tuple of (score, latency_seconds, comment) or None if no timing data
        """
        try:
            # Try to get timestamp from trace
            if "timestamp" in trace_data and "endTime" in trace_data:
                start_time = datetime.fromisoformat(
                    trace_data["timestamp"].replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(
                    trace_data["endTime"].replace("Z", "+00:00")
                )
                return self.score_from_timestamps(start_time, end_time)
            
            # Try to get latency from observations
            elif "observations" in trace_data:
                for obs in trace_data["observations"]:
                    if obs.get("type") == "GENERATION" and "startTime" in obs and "endTime" in obs:
                        start_time = datetime.fromisoformat(
                            obs["startTime"].replace("Z", "+00:00")
                        )
                        end_time = datetime.fromisoformat(
                            obs["endTime"].replace("Z", "+00:00")
                        )
                        return self.score_from_timestamps(start_time, end_time)
            
            # Try to get latency from usage data
            elif "usage" in trace_data and "latency" in trace_data["usage"]:
                latency_ms = trace_data["usage"]["latency"]
                return self.score_from_latency_ms(latency_ms)
            
            return None
            
        except Exception as e:
            print(f"Warning: Error extracting latency from trace: {e}")
            return None


def get_latency_thresholds() -> dict:
    """
    Get latency threshold definitions for documentation.
    
    Returns:
        Dictionary of threshold definitions
    """
    return {
        "excellent": {"threshold": "< 1s", "score_range": "10"},
        "good": {"threshold": "1-3s", "score_range": "8-9"},
        "acceptable": {"threshold": "3-5s", "score_range": "6-7"},
        "slow": {"threshold": "5-10s", "score_range": "4-5"},
        "very_slow": {"threshold": "> 10s", "score_range": "0-3"}
    }


# Example usage
if __name__ == "__main__":
    scorer = ResponseLatencyScorer()
    
    # Test different latencies
    test_latencies = [
        0.5,   # Excellent
        1.5,   # Good
        2.8,   # Good
        4.0,   # Acceptable
        7.5,   # Slow
        12.0,  # Very Slow
        25.0,  # Very Slow
    ]
    
    print("Response Latency Scorer - Test Results\n")
    print("=" * 80)
    
    for latency in test_latencies:
        score = scorer.calculate_score_from_latency(latency)
        category = scorer.get_performance_category(score)
        
        print(f"\nLatency: {latency}s")
        print(f"Score: {score:.2f}/10")
        print(f"Category: {category}")
        print("-" * 80)
    
    # Test with timestamps
    print("\n\nTimestamp-based scoring:")
    print("=" * 80)
    
    from datetime import timedelta
    
    start = datetime.now()
    for delay_seconds in [0.8, 2.5, 8.0]:
        end = start + timedelta(seconds=delay_seconds)
        score, latency, comment = scorer.score_from_timestamps(start, end)
        print(f"\n{comment}")
