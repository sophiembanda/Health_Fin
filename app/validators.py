import re
from email_validator import validate_email as validate_email_validator, EmailNotValidError

# def validate_amount(amount):
#     try:
#         value = float(amount)
#         return value > 0
#     except ValueError:
#         return False

# validators.py

def validate_amount(amount):
    errors = []
    try:
        value = float(amount)
        if value <= 0:
            errors.append("Amount must be greater than 0")
    except ValueError:
        errors.append("Invalid amount format")
    return errors


def validate_email(email):
    try:
        validate_email_validator(email)
        return True
    except EmailNotValidError:
        return False

def validate_phone_number(phone_number):
    pattern = re.compile(r'^\+?254\d{9}$')
    return bool(pattern.match(phone_number))

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
