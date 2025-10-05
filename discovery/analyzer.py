"""
Main analysis orchestration for interview insights extraction.
"""

from pathlib import Path
from typing import Optional

from .config import load_guidelines
from .agents import create_insight_agent
from .privacy import enforce_pii_removal, validate_no_pii, audit_pii_in_transcript
from .models import InterviewInsights


class InterviewAnalyzer:
    """
    Orchestrates the complete interview analysis workflow.
    """
    
    def __init__(self, config_path: str = "config/research_guidelines.yaml"):
        """
        Initialize analyzer with configuration.
        
        Args:
            config_path: Path to research guidelines YAML
        """
        self.guidelines = load_guidelines(config_path)
        self.agent = create_insight_agent(self.guidelines)
        self.privacy_rules = self.guidelines['privacy_enforcement']
    
    def load_transcript(self, filepath: str) -> str:
        """
        Load interview transcript from file.
        
        Args:
            filepath: Path to transcript file
            
        Returns:
            Transcript text
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Transcript not found: {filepath}")
        
        with open(path, 'r') as f:
            return f.read()
    
    async def analyze(
        self,
        transcript: str,
        audit: bool = True,
        validate: bool = True
    ) -> InterviewInsights:
        """
        Analyze interview transcript with privacy enforcement.
        
        Args:
            transcript: Interview text to analyze
            audit: Whether to audit PII before processing
            validate: Whether to validate output for PII
            
        Returns:
            Extracted interview insights
        """
        # Optional: Audit PII in original transcript
        if audit:
            audit_pii_in_transcript(transcript, self.privacy_rules)
        
        # Remove PII before sending to LLM
        clean_transcript = enforce_pii_removal(transcript, self.privacy_rules)
        print("\nPII removed from transcript")
        
        # Extract insights
        result = await self.agent.run(clean_transcript)
        insights = result.output
        
        # Optional: Validate no PII in output
        if validate:
            validate_no_pii(insights, self.privacy_rules)
            print("Output validated - no PII detected")
        
        return insights
    
    async def analyze_file(
        self,
        filepath: str,
        audit: bool = True,
        validate: bool = True
    ) -> InterviewInsights:
        """
        Analyze interview from file.
        
        Args:
            filepath: Path to transcript file
            audit: Whether to audit PII before processing
            validate: Whether to validate output for PII
            
        Returns:
            Extracted interview insights
        """
        transcript = self.load_transcript(filepath)
        return await self.analyze(transcript, audit=audit, validate=validate)