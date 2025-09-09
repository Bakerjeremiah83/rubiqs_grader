import re
import unicodedata

def slugify(text: str) -> str:
    """
    Convert text into a URL-safe slug.
    Example: "Ethics Essay #1" -> "ethics-essay-1"
    """
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "untitled"
