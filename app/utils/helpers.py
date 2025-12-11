def normalize_phone_number(phone_number: str) -> str:
    """
    Normalizes a phone number to the +98 format and strips whitespace.

    The function:
    - removes surrounding whitespace and any internal spaces to avoid
      mismatches between stored and queried phone numbers,
    - converts local Iranian numbers starting with 0 or 9 to the +98 format,
    - leaves any other already-formatted international numbers unchanged.
    """

    cleaned_number = phone_number.strip().replace(" ", "")

    if cleaned_number.startswith("0"):
        return "+98" + cleaned_number[1:]
    if cleaned_number.startswith("9"):
        return "+98" + cleaned_number
    if cleaned_number.startswith("+98"):
        return cleaned_number

    # The number already appears to be in international format; return as-is.
    return cleaned_number
