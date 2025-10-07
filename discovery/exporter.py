"""
Export formats optimized for tools like Mural and Miro.
"""

from .models import InterviewInsights


def to_mural_text_blocks(insights: InterviewInsights) -> str:
    lines = []

    # Pain Points rows
    for i, pp in enumerate(insights.pain_points, 1):
        details = f"Impact: {pp.impact}"
        lines.append(f"PAIN POINTS\t{i}. {pp.description}\t{details}\tQuote: {pp.quote}")
    
    # Jobs-to-be-Done rows
    for i, job in enumerate(insights.jobs_to_be_done, 1):
        details = f"Emotional: {job.emotional_job}. Context: {job.context}"
        lines.append(f"JOBS-TO-BE-DONE\t{i}. {job.functional_job}\t{details}\tQuote: {job.quote}")
    
    # Workarounds rows
    for i, w in enumerate(insights.workarounds, 1):
        details = f"Why: {w.why_needed}. Cost: {w.cost}"
        lines.append(f"WORKAROUNDS\t{i}. {w.what_they_do}\t{details}\tQuote: {w.quote}")
    
    # Desired Outcomes rows
    for i, outcome in enumerate(insights.desired_outcomes, 1):
        details = f"Gap: {outcome.current_gap}"
        lines.append(f"DESIRED OUTCOMES\t{i}. {outcome.outcome}\t{details}\tQuote: {outcome.quote}")
    
    # Behavioral Signals rows
    for i, signal in enumerate(insights.behavioral_signals, 1):
        details = f"Reveals: {signal.what_it_reveals}"
        lines.append(f"BEHAVIORAL SIGNALS\t{i}. {signal.observation}\t{details}\tQuote: {signal.quote}")
    
    # Mental Models rows
    for i, model in enumerate(insights.mental_models, 1):
        details_parts = []
        if model.metaphor_or_analogy:
            details_parts.append(f"Metaphor: {model.metaphor_or_analogy}")
        if model.mismatch_with_reality:
            details_parts.append(f"Mismatch: {model.mismatch_with_reality}")
        details = ". ".join(details_parts) if details_parts else "---"
        lines.append(f"MENTAL MODELS\t{i}. {model.description}\t{details}\tQuote: {model.quote}")
    
    return "\n".join(lines)


def print_mural_export(insights: InterviewInsights):
    output = to_mural_text_blocks(insights)
    
    print("\n" + "=" * 70)
    print("MURAL/MIRO EXPORT - COPY EVERYTHING BELOW")
    print("=" * 70)
    print("\n" + output + "\n")
    print("=" * 70)
    print("\nInstructions:")
    print("1. Select and copy all text above")
    print("2. In Mural/Miro, paste on the canvas")
    print("3. Each section (separated by ---) becomes a text block")
    print("=" * 70)