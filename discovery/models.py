"""
Pydantic data models for interview insights extraction.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class PainPoint(BaseModel):
    """A problem the user is experiencing"""
    description: str = Field(description="What's not working for the user")
    impact: str = Field(description="Time lost, extra work, costs, uncertainty")
    quote: str = Field(description="User's exact words")


class JobToBeDone(BaseModel):
    """What the user is trying to accomplish"""
    functional_job: str = Field(description="What task are they trying to complete?")
    emotional_job: str = Field(description="How do they want to feel?")
    context: str = Field(description="When/where does this happen?")
    quote: str


class Workaround(BaseModel):
    """Manual solution the user created"""
    what_they_do: str = Field(description="The workaround they've created")
    why_needed: str = Field(description="What problem does this solve?")
    cost: str = Field(description="Time/effort this workaround takes")
    quote: str


class DesiredOutcome(BaseModel):
    """What success looks like to the user"""
    outcome: str = Field(description="What do they really want?")
    current_gap: str = Field(description="Why can't they achieve this now?")
    quote: str


class BehavioralSignal(BaseModel):
    """Implicit pattern revealing underlying needs"""
    observation: str = Field(description="What did they say/do that was revealing?")
    what_it_reveals: str = Field(description="The underlying need or belief")
    quote: str


class MentalModel(BaseModel):
    """How the user conceptualizes their work"""
    description: str = Field(description="How they think about or categorize something")
    metaphor_or_analogy: Optional[str] = Field(default=None)
    mismatch_with_reality: Optional[str] = Field(default=None)
    quote: str


class InterviewInsights(BaseModel):
    """All insights extracted from a single interview"""
    pain_points: List[PainPoint] = []
    jobs_to_be_done: List[JobToBeDone] = []
    workarounds: List[Workaround] = []
    desired_outcomes: List[DesiredOutcome] = []
    behavioral_signals: List[BehavioralSignal] = []
    mental_models: List[MentalModel] = []