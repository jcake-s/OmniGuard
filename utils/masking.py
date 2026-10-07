"""
OmniGuard PII Sanitization & Data Masking Engine
Protects sensitive consumer banking identifiers before external LLM calls.
"""

import re
from typing import Any, Dict

# Regex pattern for 13 to 19 digit payment card numbers (with optional spaces or dashes)
CARD_PATTERN = re.compile(r'\b(?:\d[ -]*?){13,19}\b')

# Regex for US SSN (9 digits formatted as AAA-GG-SSSS or continuous)
SSN_PATTERN = re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b')

# Regex for phone numbers
PHONE_PATTERN = re.compile(r'\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b')

# Regex for emails
EMAIL_PATTERN = re.compile(r'\b([A-Za-z0-9._%+-]{1,3})[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b')


def mask_card_number(text: str) -> str:
    """Masks credit/debit card numbers preserving only the last 4 digits."""
    def _repl(match):
        raw = re.sub(r'\D', '', match.group(0))
        if 13 <= len(raw) <= 19:
            last4 = raw[-4:]
            return f"****-****-****-{last4}"
        return match.group(0)

    return CARD_PATTERN.sub(_repl, text)


def mask_ssn(text: str) -> str:
    """Masks SSN identifiers preserving only last 4 digits."""
    def _repl(match):
        raw = re.sub(r'\D', '', match.group(0))
        if len(raw) == 9:
            return f"***-**-{raw[-4:]}"
        return match.group(0)

    return SSN_PATTERN.sub(_repl, text)


def mask_phone(text: str) -> str:
    """Masks phone numbers to (***) ***-1234."""
    return PHONE_PATTERN.sub(r'(***) ***-\3', text)


def mask_email(text: str) -> str:
    """Masks email addresses, e.g., j***@example.com."""
    return EMAIL_PATTERN.sub(r'\1***@\2', text)


def sanitize_text(text: str) -> str:
    """Runs all masking passes across a text string."""
    if not isinstance(text, str):
        return text
    sanitized = mask_card_number(text)
    sanitized = mask_ssn(sanitized)
    sanitized = mask_phone(sanitized)
    sanitized = mask_email(sanitized)
    return sanitized


def sanitize_transaction_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes all string fields within a transaction record dictionary
    prior to sending it to an AI inference endpoint.
    """
    sanitized = {}
    for key, value in payload.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_text(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_transaction_payload(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_text(v) if isinstance(v, str) else v for v in value
            ]
        else:
            sanitized[key] = value
    return sanitized
