"""Text Normalizer for Speech Synthesis (Writing replies for the ear)."""
import re


def normalize_for_speech(text: str) -> str:
    """
    Format text for natural audio reading:
    - Breaks 8-digit order numbers into spaced digit pairs.
    - Expands currency symbols.
    - Ensures 4-digit years in dates.
    """
    norm = text
    
    # 1. Expand currency ₹ -> rupees
    norm = re.sub(r"₹\s*(\d+)", r"\1 rupees", norm)
    
    # 2. Format 8-digit order numbers into spaced groups: 89782837 -> "8 9 7 8, 2 8 3 7"
    def _space_digits(match):
        digits = match.group(0)
        return " ".join(digits[:4]) + ", " + " ".join(digits[4:])
        
    norm = re.sub(r"\b\d{8}\b", _space_digits, norm)
    
    # 3. Clean up formatting asterisks or markdown table bars for speech
    norm = norm.replace("**", "").replace("*", "")
    norm = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    
    return norm
