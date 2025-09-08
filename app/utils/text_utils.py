# app/utils/text_utils.py
import re

def normalize_title(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s
