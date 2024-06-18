import logging
from flask_mail import Message
from flask import current_app
from . import mail

logger = logging.getLogger(__name__)

def send_contact_message(data):
    try:
        # Send the main contact message to the specified recipient
        msg = Message(
            subject="New Contact Message",
            sender=data['email'],
            recipients=[current_app.config['MAIL_DEFAULT_RECIPIENT']],
            body=f"Name: {data['name']}\nEmail: {data['email']}\nMessage: {data['message']}"
        )
        mail.send(msg)
        
        # Send a confirmation email to the sender
        confirmation_msg = Message(
            subject="Your Message Received",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[data['email']],
            body="Thank you for contacting us. We have received your message and will get back to you shortly."
        )
        mail.send(confirmation_msg)
        
        logger.debug("Emails sent successfully.")
        return True, ""
    except Exception as e:
        logger.error(f"Email sending error: {str(e)}")
        return False, str(e)
