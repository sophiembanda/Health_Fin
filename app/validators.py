#valdators.py
import re
from email_validator import validate_email as validate_email_validator, EmailNotValidError

def validate_contact_form(data):
    errors = []
    
    name = data.get('name')
    if not name or len(name) > 50:
        errors.append("Invalid name")
    
    email = data.get('email')
    try:
        validate_email(email)
    except EmailNotValidError:
        errors.append("Invalid email")
    
    message = data.get('message')
    if not message or len(message) > 1000:
        errors.append("Invalid message")
    
    return errors


def validate_amount(amount):
    try:
        value = float(amount)
        return value > 0
    except ValueError:
        return False

def validate_email(email):
    try:
        validate_email_validator(email)
        return True
    except EmailNotValidError:
        return False

# def validate_phone_number(phone_number):
#     pattern = re.compile(r'^\+?254\d{9}$')
#     return bool(pattern.match(phone_number))


def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character"
    return None

def validate_phone_number(phone_number):
    if phone_number.startswith("07"):
        if len(phone_number) != 10:
            return "Invalid phone number"
    elif phone_number.startswith("254"):
        if len(phone_number) != 12:
            return "Invalid phone number"
    else:
        return "Enter a correct phone number"
    return None


