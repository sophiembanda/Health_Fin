from datetime import datetime
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from .validators import validate_password, validate_phone_number

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(13), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    session_start_time = db.Column(db.DateTime)

    savings = db.relationship('Savings', backref='owner', lazy=True)
    transactions = db.relationship('Transaction', backref='owner', lazy=True)
    loans = db.relationship('LoanApplication', backref='applicant', lazy=True)
    email_tokens = db.relationship('EmailVerificationToken', backref='user', lazy=True)
    password_tokens = db.relationship('PasswordResetToken', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.email}', '{self.email_verified}')"

    def set_password(self, password):
        validation_error = validate_password(password)
        if validation_error:
            raise ValueError(validation_error)
        self.password_hash = generate_password_hash(password)

    def set_phone_number(self, phone_number):
        validation_error = validate_phone_number(phone_number)
        if validation_error:
            raise ValueError(validation_error)
        self.phone_number = phone_number

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def start_session(self):
        self.session_start_time = datetime.now()
        db.session.commit()

    def end_session(self):
        self.session_start_time = None
        db.session.commit()

    @staticmethod
    def generate_verification_token(user_id):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(user_id, salt=current_app.config['SECURITY_PASSWORD_SALT'])

    @staticmethod
    def verify_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'])
        except:
            return None
        return user_id

class Savings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Pending")

class EmailVerificationToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(120), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_token(user_id):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(user_id, salt=current_app.config['SECURITY_PASSWORD_SALT'])

    @staticmethod
    def verify_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'])
        except:
            return None
        return user_id

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(120), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_token(user_id):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(user_id, salt=current_app.config['SECURITY_PASSWORD_SALT'])

    @staticmethod
    def verify_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'])
        except:
            return None
        return user_id

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class SavingPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
