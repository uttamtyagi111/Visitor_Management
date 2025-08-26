import secrets
import string

def generate_otp(length=6, only_digits=True):
    """
    Generate a cryptographically secure OTP.
    
    Args:
        length (int): Length of OTP (default 6)
        only_digits (bool): If True, OTP will be numeric only.
                            If False, OTP will include letters + digits.
    
    Returns:
        str: Secure OTP string
    """
    if only_digits:
        characters = string.digits
    else:
        characters = string.ascii_uppercase + string.digits

    return ''.join(secrets.choice(characters) for _ in range(length))
