def normalize_phone_number(phone_number: str) -> str:
    """
    Normalizes a phone number to the +98 format.
    Handles numbers starting with 0, 9, or already in the correct format.
    """
    if phone_number.startswith("0"):
        return "+98" + phone_number[1:]
    if phone_number.startswith("9"):
        return "+98" + phone_number
    if phone_number.startswith("+98"):
        return phone_number
    # You might want to add more robust validation or error handling here
    return phone_number
