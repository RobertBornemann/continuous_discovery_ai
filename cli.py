"""
Command-line interface for Discovery AI interview analysis.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
import os
from discovery.exporter import print_mural_export
from discovery import InterviewAnalyzer


def display_results(insights):
    """Display analysis results in formatted output."""
    print("\n" + "=" * 70)
    print("INTERVIEW ANALYSIS RESULTS")
    print("=" * 70)
    
    if insights.pain_points:
        print(f"\nPAIN POINTS ({len(insights.pain_points)}):")
        print("-" * 70)
        for i, pp in enumerate(insights.pain_points, 1):
            print(f"\n{i}. {pp.description}")
            print(f"   Impact: {pp.impact}")
            print(f"   Quote: \"{pp.quote[:100]}...\"" if len(pp.quote) > 100 else f"   Quote: \"{pp.quote}\"")
    
    if insights.jobs_to_be_done:
        print(f"\nJOBS-TO-BE-DONE ({len(insights.jobs_to_be_done)}):")
        print("-" * 70)
        for i, job in enumerate(insights.jobs_to_be_done, 1):
            print(f"\n{i}. Functional: {job.functional_job}")
            print(f"   Emotional: {job.emotional_job}")
            print(f"   Context: {job.context}")
    
    if insights.workarounds:
        print(f"\nWORKAROUNDS ({len(insights.workarounds)}):")
        print("-" * 70)
        for i, w in enumerate(insights.workarounds, 1):
            print(f"\n{i}. {w.what_they_do}")
            print(f"   Why: {w.why_needed}")
            print(f"   Cost: {w.cost}")
    
    if insights.desired_outcomes:
        print(f"\nDESIRED OUTCOMES ({len(insights.desired_outcomes)}):")
        print("-" * 70)
        for i, outcome in enumerate(insights.desired_outcomes, 1):
            print(f"\n{i}. {outcome.outcome}")
            print(f"   Gap: {outcome.current_gap}")
    
    if insights.behavioral_signals:
        print(f"\nBEHAVIORAL SIGNALS ({len(insights.behavioral_signals)}):")
        print("-" * 70)
        for i, signal in enumerate(insights.behavioral_signals, 1):
            print(f"\n{i}. {signal.observation}")
            print(f"   Reveals: {signal.what_it_reveals}")
    
    if insights.mental_models:
        print(f"\nMENTAL MODELS ({len(insights.mental_models)}):")
        print("-" * 70)
        for i, model in enumerate(insights.mental_models, 1):
            print(f"\n{i}. {model.description}")
            if model.metaphor_or_analogy:
                print(f"   Metaphor: {model.metaphor_or_analogy}")
    
    print("\n" + "=" * 70)


async def analyze_command(args):
    """Execute the analyze command."""
    if not Path(args.file).exists():
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)
    
    analyzer = InterviewAnalyzer(config_path=args.config)
    
    # Handle audio or text
    if args.audio:
        print(f"Transcribing audio: {args.file}")
        insights = await analyzer.analyze_audio_file(
            args.file,
            language=args.language,
            audit=not args.no_audit,
            validate=not args.no_validate,
            save_transcript=args.save_transcript
        )
    else:
        print(f"Analyzing text: {args.file}")
        insights = await analyzer.analyze_file(
            args.file,
            audit=not args.no_audit,
            validate=not args.no_validate
        )
    
    sif args.mural:
        print_mural_export(insights)
    else:
        display_results(insights)
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            f.write(insights.model_dump_json(indent=2))
        print(f"\nResults saved to: {args.output}")


def main():
    """Main CLI entry point."""
    # Load environment variables
    load_dotenv()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY not found in environment")
        print("Create a .env file with your API key or set the environment variable")
        sys.exit(1)
    
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Discovery AI - Automated qualitative interview analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analyze interview.txt
  %(prog)s analyze interview.txt --output results.json
  %(prog)s analyze interview.txt --no-audit --no-validate
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze an interview transcript')
    analyze_parser.add_argument('file', help='Path to interview transcript file')
    analyze_parser.add_argument(
        '--config',
        default='config/research_guidelines.yaml',
        help='Path to configuration file (default: config/research_guidelines.yaml)'
    )
    analyze_parser.add_argument(
        '--output', '-o',
        help='Save results to JSON file'
    )
    analyze_parser.add_argument(
        '--no-audit',
        action='store_true',
        help='Skip PII audit before processing'
    )
    analyze_parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip PII validation after processing'
    )

    analyze_parser.add_argument(
        '--audio',
        action='store_true',
        help='Input file is audio (will transcribe first)'
    )
    analyze_parser.add_argument(
        '--language',
        help='Language code for transcription (e.g., en, de)'
    )
    analyze_parser.add_argument(
        '--save-transcript',
        help='Save transcript to file'
    )
    analyze_parser.add_argument(
    '--mural',
    action='store_true',
    help='Output in Mural/Miro format (separate text blocks)'
)
	    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'analyze':
        asyncio.run(analyze_command(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()