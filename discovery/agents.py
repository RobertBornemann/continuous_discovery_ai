"""
Agent creation and management for analysis.
"""
import os
from typing import Dict, Any
from pydantic_ai import Agent


def _require_openai_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        # This makes the Railway logs crystal clear when the var is missing.
        raise RuntimeError("OPENAI_API_KEY missing. Set it in Railway → Variables.")
    return key

from .models import InterviewInsights
from .config import build_system_prompt

def create_insight_agent(
    guidelines: Dict[str, Any],
    model: str = "openai:gpt-4o-mini",
    temperature: float = 0.3,
) -> Agent:
    # Ensure the key exists before we let pydantic-ai build the provider.
    _require_openai_key()

    system_prompt = build_system_prompt(guidelines)

    agent = Agent(
        model=model,                             # keep "openai:gpt-4o-mini"
        output_type=InterviewInsights,
        system_prompt=system_prompt,
        model_settings={"temperature": temperature},
    )
    return agent
