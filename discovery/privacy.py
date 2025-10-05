"""
Privacy and PII handling.
"""

import re
from typing import Dict, Any, List


def enforce_pii_removal(text, privacy_rules) -> str:
    if not privacy_rules['pii_removal']['enabled']:
        return text
    
    patterns = privacy_rules['pii_removal']['patterns']
    replacements = privacy_rules['pii_removal']['replacement_tokens']
    
    # Apply replacements
    text = re.sub(patterns['api_token'], replacements['api_token'], text)
    text = re.sub(patterns['iban'], replacements['iban'], text)
    text = re.sub(patterns['email'], replacements['email'], text, flags=re.IGNORECASE)
    text = re.sub(patterns['phone'], replacements['phone'], text)
    text = re.sub(patterns['employee_id'], replacements['employee_id'], text, flags=re.IGNORECASE)
    text = re.sub(patterns['names'], replacements['names'], text)
    
    return text


def validate_no_pii(insights, privacy_rules) -> bool:
    all_text = insights.model_dump_json()
    patterns = privacy_rules['pii_removal']['patterns']
    
    issues = []
    
    if re.search(patterns['email'], all_text):
        issues.append("EMAIL detected in output")
    
    if re.search(patterns['phone'], all_text):
        issues.append("PHONE NUMBER detected in output")
    
    if re.search(patterns['employee_id'], all_text):
        issues.append("EMPLOYEE ID detected in output")
    
    if issues:
        for issue in issues:
            print(f"WARNING: {issue}")
        raise ValueError("PII VALIDATION FAILED - output blocked for compliance")
    
    return True


def audit_pii_in_transcript(text, privacy_rules) -> Dict[str, int]:
    patterns = privacy_rules['pii_removal']['patterns']
    
    findings = {
        'Emails': len(re.findall(patterns['email'], text)),
        'Phone Numbers': len(re.findall(patterns['phone'], text)),
        'Employee IDs': len(re.findall(patterns['employee_id'], text)),
        'Names': len(re.findall(patterns['names'], text)),
        'IBANs': len(re.findall(patterns['iban'], text)),
        'API Tokens': len(re.findall(patterns['api_token'], text))
    }
    
    print("\nPII Detection Summary:")
    print("-" * 30)
    for pii_type, count in findings.items():
        print(f"{pii_type:20} {count:>5}")
    print("-" * 30)
    print(f"{'TOTAL':20} {sum(findings.values()):>5}")
    
    return findings