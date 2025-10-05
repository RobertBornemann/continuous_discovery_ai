"""
Discovery AI - Automated genAI interview analysis with privacy enforcement.
"""

from .models import (
    InterviewInsights,
    PainPoint,
    JobToBeDone,
    Workaround,
    DesiredOutcome,
    BehavioralSignal,
    MentalModel
)

from .config import load_guidelines, build_system_prompt
from .privacy import enforce_pii_removal, validate_no_pii, audit_pii_in_transcript
from .agents import create_insight_agent
from .analyzer import InterviewAnalyzer

__version__ = "0.1.0"

__all__ = [
    # Main interface
    'InterviewAnalyzer',
    
    # Models
    'InterviewInsights',
    'PainPoint',
    'JobToBeDone',
    'Workaround',
    'DesiredOutcome',
    'BehavioralSignal',
    'MentalModel',
    
    # Config
    'load_guidelines',
    'build_system_prompt',
    
    # Privacy
    'enforce_pii_removal',
    'validate_no_pii',
    'audit_pii_in_transcript',
    
    # Agents
    'create_insight_agent',
]