#!/usr/bin/env python3
"""
View Offline Evaluation Results
Quick viewer for evaluation JSON files
"""

import json
from pathlib import Path
from datetime import datetime
import sys

def view_latest_results(results_dir: str = "."):
    """View the most recent evaluation results"""
    
    results_path = Path(results_dir)
    
    # Find latest JSON file
    json_files = list(results_path.glob("*.json"))
    if not json_files:
        print("❌ No evaluation results found!")
        print(f"   Looking in: {results_path.absolute()}")
        return
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    
    # Load results
    with open(latest_file) as f:
        data = json.load(f)
    
    # Display summary
    print("=" * 70)
    print(f"Evaluation Results: {data['run_name']}")
    print("=" * 70)
    print()
    
    print("📅 Run Information:")
    print(f"   Dataset: {data['dataset']}")
    print(f"   Model Tested: {data['model_tested']}")
    print(f"   Judge Model: {data['judge_model']}")
    print(f"   Timestamp: {data['timestamp']}")
    print(f"   Result File: {latest_file.name}")
    print()
    
    summary = data['summary']
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"   Total Items Evaluated: {summary['total_items']}")
    print(f"   Average Score: {summary['average_score']:.2f}/10")
    
    # Pass/fail rate (assuming 7+ is pass)
    pass_count = sum(1 for r in data['results'] if r['score'] >= 7)
    pass_rate = (pass_count / summary['total_items'] * 100) if summary['total_items'] > 0 else 0
    print(f"   Pass Rate (≥7): {pass_rate:.1f}% ({pass_count}/{summary['total_items']})")
    print()
    
    print("📈 Scores by Category:")
    for cat, score in sorted(summary['category_scores'].items()):
        status = "✅" if score >= 7 else "⚠️" if score >= 5 else "❌"
        print(f"   {status} {cat:30s}: {score:.1f}/10")
    print()
    
    print("=" * 70)
    print("📝 DETAILED RESULTS")
    print("=" * 70)
    print()
    
    for i, result in enumerate(data['results'], 1):
        eval_result = result['eval_result']
        score = result['score']
        
        # Status indicator
        if score >= 9:
            status = "🌟 EXCELLENT"
        elif score >= 7:
            status = "✅ PASS"
        elif score >= 5:
            status = "⚠️  NEEDS IMPROVEMENT"
        else:
            status = "❌ FAIL"
        
        print(f"[{i}/{summary['total_items']}] {result['id']} - {result['category']}")
        print(f"      {status}: {score:.1f}/10")
        print()
        
        # Detailed scores
        print("      Detailed Scores:")
        for metric in ['factual_accuracy', 'completeness', 'relevance', 'reasoning_quality', 'safety']:
            if metric in eval_result:
                print(f"        • {metric.replace('_', ' ').title():20s}: {eval_result[metric]:.1f}/10")
        print()
        
        # Verdict and reasoning
        if 'verdict' in eval_result:
            print(f"      Verdict: {eval_result['verdict'].upper()}")
        
        reasoning = eval_result.get('reasoning', 'No reasoning provided')
        print(f"      Reasoning:")
        # Wrap text at 60 chars
        words = reasoning.split()
        line = "        "
        for word in words:
            if len(line) + len(word) + 1 > 66:
                print(line)
                line = "        " + word
            else:
                line += " " + word if line != "        " else word
        if line.strip():
            print(line)
        print()
        
        # Strengths
        if eval_result.get('strengths'):
            print("      ✨ Strengths:")
            for strength in eval_result['strengths']:
                print(f"        • {strength}")
            print()
        
        # Issues
        if eval_result.get('key_issues'):
            print("      ⚠️  Issues:")
            for issue in eval_result['key_issues']:
                print(f"        • {issue}")
            print()
        
        print("-" * 70)
        print()
    
    # Summary footer
    print("=" * 70)
    print("💡 INSIGHTS")
    print("=" * 70)
    print()
    
    # Find best and worst performing categories
    cat_scores = summary['category_scores']
    if cat_scores:
        best_cat = max(cat_scores.items(), key=lambda x: x[1])
        worst_cat = min(cat_scores.items(), key=lambda x: x[1])
        
        print(f"🏆 Best Category: {best_cat[0]} ({best_cat[1]:.1f}/10)")
        print(f"📉 Worst Category: {worst_cat[0]} ({worst_cat[1]:.1f}/10)")
        print()
    
    # Count issues
    all_issues = []
    for result in data['results']:
        all_issues.extend(result['eval_result'].get('key_issues', []))
    
    if all_issues:
        from collections import Counter
        issue_counts = Counter(all_issues)
        print("🔍 Common Issues:")
        for issue, count in issue_counts.most_common(5):
            print(f"   • {issue} ({count}x)")
        print()
    
    # File location
    print("=" * 70)
    print(f"📁 Full results: {latest_file.absolute()}")
    print("=" * 70)


def list_all_results(results_dir: str = "."):
    """List all evaluation results"""
    
    results_path = Path(results_dir)
    json_files = sorted(results_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not json_files:
        print("❌ No evaluation results found!")
        return
    
    print("=" * 70)
    print(f"Evaluation Results History ({len(json_files)} runs)")
    print("=" * 70)
    print()
    
    for i, file_path in enumerate(json_files, 1):
        with open(file_path) as f:
            data = json.load(f)
        
        summary = data['summary']
        timestamp = data.get('timestamp', 'Unknown')
        
        print(f"{i}. {data['run_name']}")
        print(f"   Time: {timestamp}")
        print(f"   Score: {summary['average_score']:.2f}/10 ({summary['total_items']} items)")
        print(f"   File: {file_path.name}")
        print()


def compare_results(file1: str, file2: str):
    """Compare two evaluation results"""
    
    with open(file1) as f:
        data1 = json.load(f)
    with open(file2) as f:
        data2 = json.load(f)
    
    print("=" * 70)
    print("Comparison: Evaluation Results")
    print("=" * 70)
    print()
    
    print(f"Run 1: {data1['run_name']}")
    print(f"   Model: {data1['model_tested']}")
    print(f"   Score: {data1['summary']['average_score']:.2f}/10")
    print()
    
    print(f"Run 2: {data2['run_name']}")
    print(f"   Model: {data2['model_tested']}")
    print(f"   Score: {data2['summary']['average_score']:.2f}/10")
    print()
    
    # Score difference
    diff = data2['summary']['average_score'] - data1['summary']['average_score']
    if diff > 0:
        print(f"📈 Improvement: +{diff:.2f} points")
    elif diff < 0:
        print(f"📉 Regression: {diff:.2f} points")
    else:
        print("➡️  No change")
    print()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="View offline evaluation results")
    parser.add_argument(
        "--dir",
        default="../results",
        help="Results directory (default: ../results)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all evaluation runs"
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("FILE1", "FILE2"),
        help="Compare two result files"
    )
    
    args = parser.parse_args()
    
    if args.compare:
        compare_results(args.compare[0], args.compare[1])
    elif args.list:
        list_all_results(args.dir)
    else:
        view_latest_results(args.dir)


if __name__ == "__main__":
    main()
