"""
Test the discovery package end-to-end.
"""
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Verify API key is loaded
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError("OPENAI_API_KEY not found in environment")

from discovery import InterviewAnalyzer


async def main():
    # Initialize analyzer
    print("Initializing analyzer...")
    analyzer = InterviewAnalyzer()
    
    # Analyze a file
    print("\nAnalyzing interview file...")
    insights = await analyzer.analyze_file(
        'data/interviews/mock_interview_sensitive.txt',
        audit=True,
        validate=True
    )
    
    # Display results
    print(f"\n{'='*60}")
    print("ANALYSIS RESULTS")
    print(f"{'='*60}")
    
    print(f"\nPain Points: {len(insights.pain_points)}")
    for i, pp in enumerate(insights.pain_points, 1):
        print(f"\n{i}. {pp.description}")
        print(f"   Impact: {pp.impact}")
    
    print(f"\nJobs-to-be-Done: {len(insights.jobs_to_be_done)}")
    for i, job in enumerate(insights.jobs_to_be_done, 1):
        print(f"\n{i}. {job.functional_job}")
    
    print(f"\nWorkarounds: {len(insights.workarounds)}")
    print(f"Desired Outcomes: {len(insights.desired_outcomes)}")
    print(f"Behavioral Signals: {len(insights.behavioral_signals)}")
    print(f"Mental Models: {len(insights.mental_models)}")


if __name__ == "__main__":
    asyncio.run(main())