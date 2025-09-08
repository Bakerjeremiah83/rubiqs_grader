# app/utils/extractor.py
from io import BytesIO

def extract_pdf_text(file_or_bytes) -> str:
    # Minimal placeholder so your app runs. Replace with your real PDF extractor.
    # Accepts path/bytes/BytesIO; returns a simple string to avoid crashes.
    if isinstance(file_or_bytes, (bytes, bytearray, BytesIO)):
        return "[PDF text placeholder]"
    try:
        with open(file_or_bytes, "rb"):
            pass
    except Exception:
        pass
    return "[PDF text placeholder]"

def extract_filled_fields_from_pdf(file_or_bytes) -> dict:
    # Minimal placeholder. Replace with your real form-field extraction.
    return {}
