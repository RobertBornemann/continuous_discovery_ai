"""
Configuration management for research guidelines.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_guidelines(config_path: str = "config/research_guidelines.yaml") -> Dict[str, Any]:
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, 'r') as f:
        guidelines = yaml.safe_load(f)
    
    return guidelines


def build_system_prompt(guidelines: Dict[str, Any]) -> str:
    prompt = "You are an expert product researcher.\n\n"
    prompt += "APPLY THESE FRAMEWORKS:\n\n"
    
    for framework_name, description in guidelines['frameworks'].items():
        prompt += f"{framework_name.upper().replace('_', ' ')}:\n"
        prompt += f"{description}\n\n"
    
    prompt += """
Extract ALL insights from the interview:
- Pain points: Problems causing time waste, costs, uncertainty, frustration
- Jobs-to-be-done: What they're trying to accomplish (functional + emotional goals)
- Workarounds: Current hacks/solutions they've created
- Desired outcomes: What success looks like to them
- Behavioral signals: Implicit patterns revealing underlying needs
- Mental models: How they conceptualize their work

Always include exact quotes as evidence.
"""
    return prompt