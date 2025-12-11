import re


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone numbers to a consistent +98 format for lookups.

    The function:
    - strips leading/trailing whitespace,
    - removes separators such as spaces, hyphens, and parentheses that often
      appear in user input and merge conflicts,
    - converts local Iranian numbers (starting with 0 or 9) to +98 format,
    - handles the 0098 prefix by converting it to +98,
    - converts numbers starting with 98 to +98, assuming missing plus sign,
    - preserves other international numbers without modification.
    """

    # Remove whitespace and common separator characters while keeping an
    # optional leading "+" for international formats.
    cleaned = phone_number.strip()
    cleaned = re.sub(r"[\s\-()]+", "", cleaned)

    if cleaned.startswith("+98"):
        return cleaned
    if cleaned.startswith("0098"):
        return "+98" + cleaned[4:]
    if cleaned.startswith("98"):
        return "+" + cleaned
    if cleaned.startswith("00"):
        # Generic international format such as 0044... -> +44...
        return "+" + cleaned[2:]
    if cleaned.startswith("0"):
        return "+98" + cleaned[1:]
    if cleaned.startswith("9"):
        return "+98" + cleaned

    # The number already appears to be in international format; return as-is.
    return cleaned
