"""
Agent creation and management for analysis.
"""

from pydantic_ai import Agent
from typing import Dict, Any

from .models import InterviewInsights
from .config import build_system_prompt


def create_insight_agent(
    guidelines: Dict[str, Any],
    model: str = 'openai:gpt-4o-mini',
    temperature: float = 0.3
) -> Agent:
    system_prompt = build_system_prompt(guidelines)
    
    agent = Agent(
        model=model,
        output_type=InterviewInsights,
        system_prompt=system_prompt,
        model_settings={'temperature': temperature}
    )
    
    return agent