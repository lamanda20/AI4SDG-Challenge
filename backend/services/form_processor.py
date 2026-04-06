"""
form_processor.py
Cleans and normalizes raw form input into a validated UserFormInput.
"""

from typing import Dict, Any
from schemas import UserFormInput


def clean_form_data(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw form fields before Pydantic validation."""
    cleaned = {}

    for key, value in raw.items():
        # Strip whitespace from strings
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                value = None
        # Normalize list fields
        if key in ("diseases", "medications", "injuries") and isinstance(value, str):
            value = [v.strip().lower() for v in value.split(",") if v.strip()]
        # Lowercase string enums
        if key in ("gender", "activity_level") and isinstance(value, str):
            value = value.lower()
        cleaned[key] = value

    # Normalize disease names
    if "diseases" in cleaned and isinstance(cleaned["diseases"], list):
        cleaned["diseases"] = [d.lower().replace(" ", "_") for d in cleaned["diseases"]]

    return cleaned


def process_form(raw: Dict[str, Any]) -> UserFormInput:
    """
    Full form processing pipeline:
    1. Clean raw input
    2. Validate with Pydantic
    Returns validated UserFormInput.
    """
    cleaned = clean_form_data(raw)
    return UserFormInput(**cleaned)
