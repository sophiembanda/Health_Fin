from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask_wtf.csrf import generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from .models import ContactMessage, Savings, SavingPlan, Transaction, User, LoanApplication, Income, Expense
from .validators import validate_contact_form, validate_amount, validate_email, validate_phone_number, validate_password
from .services import send_contact_message
from . import db, csrf, limiter
import re

# Define blueprint
main_bp = Blueprint('main', __name__, url_prefix='/api')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# CSRF Token Endpoint
@main_bp.route('/get-csrf-token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()
    return jsonify({"csrf_token": token})

# User Registration Endpoint
@main_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({"error": "Error registering user"}), 500

@main_bp.route('/signup', methods=['POST'])
def signup():
    if request.is_json:
        data = request.get_json()

        # Validate required fields
        required_fields = ['first_name', 'last_name', 'phone_number', 'email', 'password', 'confirm_password']
        if not all(key in data for key in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        first_name = data['first_name']
        last_name = data['last_name']
        phone_number = data['phone_number']
        email = data['email']
        password = data['password']
        confirm_password = data['confirm_password']

        validation_errors = []
        if len(first_name) < 2:
            validation_errors.append('First name must be at least 2 characters long.')
        if len(last_name) < 2:
            validation_errors.append('Last name must be at least 2 characters long.')
        if not re.match(r'^[A-Za-z\s]*$', first_name):
            validation_errors.append('First name should only contain letters and spaces.')
        if not re.match(r'^[A-Za-z\s]*$', last_name):
            validation_errors.append('Last name should only contain letters and spaces.')

        try:
            if not phone_number.isdigit():
                validation_errors.append('Phone number should only contain digits.')
        except ValueError:
            validation_errors.append('Phone number should only contain digits.')

        if len(phone_number) != 10:
            validation_errors.append('Phone number must be 10 digits long.')
        if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
            validation_errors.append('Invalid email address.')

        if password != confirm_password:
            validation_errors.append('Passwords do not match.')

        validation_error = validate_password(password)
        if validation_error:
            validation_errors.append(validation_error)

        if validation_errors:
            return jsonify({"error": validation_errors}), 400

        new_user = User(first_name=first_name, last_name=last_name, phone_number=phone_number, email=email)
        new_user.set_password(password)
        new_user.set_phone_number(phone_number)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

    return jsonify({"error": "Invalid request method or content type"}), 405


@main_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401

        access_token = create_access_token(identity=user.id)
        return jsonify({"token": access_token}), 200
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}")
        return jsonify({"error": "Error logging in"}), 500

# User Dashboard Route
@main_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    savings = Savings.query.filter_by(user_id=user_id).all()
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    loans = LoanApplication.query.filter_by(user_id=user_id).all()
    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()

    return jsonify({
        "user": user.email,
        "savings": [{"id": s.id, "balance": s.balance} for s in savings],
        "transactions": [{"id": t.id, "type": t.type, "amount": t.amount, "timestamp": t.timestamp} for t in transactions],
        "loans": [{"id": l.id, "amount": l.amount, "status": l.status} for l in loans],
        "incomes": [{"id": i.id, "amount": i.amount, "date": i.date} for i in incomes],
        "expenses": [{"id": e.id, "amount": e.amount, "date": e.date} for e in expenses]
    }), 200

@main_bp.route('/contact', methods=['POST'])
@limiter.limit("5 per hour")
def contact():
    data = request.get_json()
    errors = validate_contact_form(data)
    if errors:
        return jsonify({"errors": errors}), 400

    contact_message = ContactMessage(
        name=data['name'],
        email=data['email'],
        message=data['message']
    )
    db.session.add(contact_message)
    db.session.commit()

    send_contact_message(contact_message)
    return jsonify({"message": "Contact message sent successfully"}), 200

@main_bp.route('/savings', methods=['POST'])
@jwt_required()
def create_savings():
    data = request.get_json()
    user_id = get_jwt_identity()
    savings = Savings(user_id=user_id, balance=0.0)
    db.session.add(savings)
    db.session.commit()
    return jsonify({"message": "Savings account created successfully"}), 201

@main_bp.route('/savings/<int:savings_id>/deposit', methods=['POST'])
@jwt_required()
def deposit(savings_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    savings = Savings.query.get_or_404(savings_id)
    if savings.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    amount = data.get('amount')
    if not validate_amount(amount):
        return jsonify({"error": "Invalid amount"}), 400

    savings.balance += amount
    transaction = Transaction(user_id=user_id, type='deposit', amount=amount)
    db.session.add(transaction)
    db.session.commit()
    return jsonify({"message": "Deposit successful", "balance": savings.balance}), 200

@main_bp.route('/savings/<int:savings_id>/withdraw', methods=['POST'])
@jwt_required()
def withdraw(savings_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    savings = Savings.query.get_or_404(savings_id)
    if savings.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    amount = data.get('amount')
    if not validate_amount(amount):
        return jsonify({"error": "Invalid amount"}), 400

    if savings.balance < amount:
        return jsonify({"error": "Insufficient balance"}), 400

    savings.balance -= amount
    transaction = Transaction(user_id=user_id, type='withdrawal', amount=amount)
    db.session.add(transaction)
    db.session.commit()
    return jsonify({"message": "Withdrawal successful", "balance": savings.balance}), 200

@main_bp.route('/income', methods=['POST'])
@jwt_required()
def add_income():
    data = request.get_json()
    user_id = get_jwt_identity()
    amount = data.get('amount')
    if not validate_amount(amount):
        return jsonify({"error": "Invalid amount"}), 400

    income = Income(user_id=user_id, amount=amount)
    db.session.add(income)
    db.session.commit()
    return jsonify({"message": "Income added successfully"}), 201

@main_bp.route('/expense', methods=['POST'])
@jwt_required()
def add_expense():
    data = request.get_json()
    user_id = get_jwt_identity()
    amount = data.get('amount')
    if not validate_amount(amount):
        return jsonify({"error": "Invalid amount"}), 400

    expense = Expense(user_id=user_id, amount=amount)
    db.session.add(expense)
    db.session.commit()
    return jsonify({"message": "Expense added successfully"}), 201
