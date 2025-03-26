# utils/validators.py
import re

def is_valid_full_name(name: str) -> bool:
    """Check if the name contains only Russian letters and at least two words."""
    # Disallow English letters by checking for their presence
    if re.search(r'[A-Za-z]', name):
        return False
    # Require at least two words (split by whitespace)
    parts = [p for p in name.split() if p]
    return len(parts) >= 2

def normalize_name(name: str) -> str:
    """Normalize the name: convert to lowercase and replace 'ё' with 'е'."""
    name_lower = name.strip().lower()
    return name_lower.replace('ё', 'е')
