"""
Web interface for Discovery AI interview analysis.
Simple upload and analyze interface.
"""

import streamlit as st
import asyncio
from pathlib import Path
import tempfile
from dotenv import load_dotenv
import os

from discovery import InterviewAnalyzer
from discovery.exporter import to_mural_text_blocks

# Load environment
load_dotenv()

# Page config
st.set_page_config(
    page_title="Discovery AI",
    page_icon="🎯",
    layout="wide"
)

# Title
st.title("🎯 Discovery AI")
st.markdown("**Automated qualitative interview analysis with privacy enforcement**")
st.markdown("---")


def display_insights(insights):
    """Display insights in nice formatted boxes."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pain Points
        if insights.pain_points:
            with st.expander(f"🔴 Pain Points ({len(insights.pain_points)})", expanded=False):
                for i, pp in enumerate(insights.pain_points, 1):
                    st.markdown(f"**{i}. {pp.description}**")
                    st.caption(f"Impact: {pp.impact}")
                    st.info(f'"{pp.quote}"')
                    st.markdown("---")
        
        # Jobs-to-be-Done
        if insights.jobs_to_be_done:
            with st.expander(f"🎯 Jobs-to-be-Done ({len(insights.jobs_to_be_done)})", expanded=False):
                for i, job in enumerate(insights.jobs_to_be_done, 1):
                    st.markdown(f"**{i}. {job.functional_job}**")
                    st.caption(f"Emotional: {job.emotional_job}")
                    st.caption(f"Context: {job.context}")
                    st.markdown("---")
        
        # Workarounds
        if insights.workarounds:
            with st.expander(f"🔧 Workarounds ({len(insights.workarounds)})", expanded=False):
                for i, w in enumerate(insights.workarounds, 1):
                    st.markdown(f"**{i}. {w.what_they_do}**")
                    st.caption(f"Why: {w.why_needed}")
                    st.caption(f"Cost: {w.cost}")
                    st.markdown("---")
    
    with col2:
        # Desired Outcomes
        if insights.desired_outcomes:
            with st.expander(f"✨ Desired Outcomes ({len(insights.desired_outcomes)})", expanded=False):
                for i, outcome in enumerate(insights.desired_outcomes, 1):
                    st.markdown(f"**{i}. {outcome.outcome}**")
                    st.caption(f"Gap: {outcome.current_gap}")
                    st.markdown("---")
        
        # Behavioral Signals
        if insights.behavioral_signals:
            with st.expander(f"🔍 Behavioral Signals ({len(insights.behavioral_signals)})", expanded=False):
                for i, signal in enumerate(insights.behavioral_signals, 1):
                    st.markdown(f"**{i}. {signal.observation}**")
                    st.caption(f"Reveals: {signal.what_it_reveals}")
                    st.markdown("---")
        
        # Mental Models
        if insights.mental_models:
            with st.expander(f"🧠 Mental Models ({len(insights.mental_models)})", expanded=False):
                for i, model in enumerate(insights.mental_models, 1):
                    st.markdown(f"**{i}. {model.description}**")
                    if model.metaphor_or_analogy:
                        st.caption(f"Metaphor: {model.metaphor_or_analogy}")
                    if model.mismatch_with_reality:
                        st.caption(f"Mismatch: {model.mismatch_with_reality}")
                    st.markdown("---")


async def analyze_interview(analyzer, content, is_audio=False):
    """Run analysis."""
    if is_audio:
        # Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            insights = await analyzer.analyze_audio_file(
                tmp_path,
                audit=True,
                validate=True
            )
        finally:
            # Clean up temp file
            Path(tmp_path).unlink()
    else:
        # Text content
        insights = await analyzer.analyze(
            content.decode('utf-8') if isinstance(content, bytes) else content,
            audit=True,
            validate=True
        )
    
    return insights


def main():
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        st.error("OPENAI_API_KEY not found. Please set it in your .env file.")
        st.stop()
    
    # Initialize analyzer (cached)
    if 'analyzer' not in st.session_state:
        with st.spinner("Initializing analyzer..."):
            st.session_state.analyzer = InterviewAnalyzer()
    
    analyzer = st.session_state.analyzer
    
    # Sidebar
    with st.sidebar:
        st.header("Upload Interview")
        
        input_type = st.radio(
            "Input Type",
            ["Text File", "Audio File", "Paste Text"],
            help="Choose how to provide the interview"
        )
        
        content = None
        is_audio = False
        
        if input_type == "Text File":
            uploaded_file = st.file_uploader(
                "Upload transcript (.txt)",
                type=['txt'],
                help="Upload a text transcript"
            )
            if uploaded_file:
                content = uploaded_file.read()
        
        elif input_type == "Audio File":
            uploaded_file = st.file_uploader(
                "Upload audio (.m4a, .mp3, .wav)",
                type=['m4a', 'mp3', 'wav', 'mp4'],
                help="Upload iPhone recording or audio file"
            )
            if uploaded_file:
                content = uploaded_file.read()
                is_audio = True
        
        else:  # Paste Text
            content = st.text_area(
                "Paste interview text",
                height=300,
                help="Paste your interview transcript here"
            )
        
        analyze_button = st.button(
            "🚀 Analyze Interview",
            type="primary",
            use_container_width=True,
            disabled=not content
        )
    
    # Main area
    if analyze_button and content:
        with st.spinner("Analyzing interview... This may take a minute."):
            try:
                # Run analysis
                insights = asyncio.run(
                    analyze_interview(analyzer, content, is_audio)
                )
                
                # Store in session
                st.session_state.insights = insights
                st.success("Analysis complete!")
            
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                st.stop()
    
    # Display results
    if 'insights' in st.session_state:
        insights = st.session_state.insights
        
        # Display insights
        st.markdown("## Results")
        display_insights(insights)
        
        # Export section
        st.markdown("---")
        st.markdown("## Export for Mural/Miro")
        
        mural_text = to_mural_text_blocks(insights)
        
        st.text_area(
            "Copy this text and paste into Mural/Miro",
            value=mural_text,
            height=400,
            help="Select all (Cmd+A / Ctrl+A) and copy (Cmd+C / Ctrl+C)"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download as Text",
                mural_text,
                file_name="interview_insights.txt",
                mime="text/plain"
            )
        
        with col2:
            st.download_button(
                "Download as JSON",
                insights.model_dump_json(indent=2),
                file_name="interview_insights.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()