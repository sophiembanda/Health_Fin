#routes.py
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
    
@main_bp.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        if not data or not all(key in data for key in ('first_name', 'last_name', 'phone_number', 'email', 'password', 'confirm_password')):
            return jsonify(message="Missing data"), 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
            return jsonify(message="Invalid email format"), 400
        phone_number_error = validate_phone_number(data['phone_number'])
        if phone_number_error:
            return jsonify(message=phone_number_error), 400
        if data['password'] != data['confirm_password']:
            return jsonify(message="Passwords do not match"), 400
        password_error = validate_password(data['password'])
        if password_error:
            return jsonify(message=password_error), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify(message="Email already registered"), 400
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data['phone_number'],
            email=data['email'],
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify(message="User created"), 201

# User Login Endpoint
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


# Dashboard Data Endpoint
@main_bp.route('/dashboard', methods=['GET'])
@csrf.exempt
@jwt_required()
def get_dashboard_data():
    try:
        user_id = get_jwt_identity()
        savings = Savings.query.filter_by(user_id=user_id).first()
        income = db.session.query(db.func.sum(Income.amount)).filter_by(user_id=user_id).scalar() or 0
        expenses = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=user_id).scalar() or 0

        balance = savings.balance if savings else 0

        return jsonify({
            "balance": balance,
            "income": income,
            "savings": balance,
            "expenses": expenses
        }), 200
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify({"error": "Error fetching dashboard data"}), 500

# Finances Data Endpoint
@main_bp.route('/finances', methods=['GET'])
@csrf.exempt
@jwt_required()
def get_finances():
    try:
        user_id = get_jwt_identity()
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        finances = [
            {"date": transaction.timestamp, "amount": transaction.amount, "type": transaction.type}
            for transaction in transactions
        ]
        return jsonify({"finances": finances}), 200
    except Exception as e:
        logger.error(f"Error fetching finances: {str(e)}")
        return jsonify({"error": "Error fetching finances"}), 500

# Expense Summary Endpoint
@main_bp.route('/expenses/summary', methods=['GET'])
@csrf.exempt
@jwt_required()
def get_expense_summary():
    try:
        user_id = get_jwt_identity()
        daily_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            db.func.date(Expense.date) == db.func.date(db.func.now())
        ).scalar() or 0

        monthly_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            db.func.extract('month', Expense.date) == db.func.extract('month', db.func.now())
        ).scalar() or 0

        yearly_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            db.func.extract('year', Expense.date) == db.func.extract('year', db.func.now())
        ).scalar() or 0

        return jsonify({
            "daily": daily_expenses,
            "monthly": monthly_expenses,
            "yearly": yearly_expenses
        }), 200
    except Exception as e:
        logger.error(f"Error fetching expense summary: {str(e)}")
        return jsonify({"error": "Error fetching expense summary"}), 500

# Add Income Endpoint
@main_bp.route('/income', methods=['POST'])
@csrf.exempt
@jwt_required()
def add_income():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        amount = data.get('amount')
        
        if not validate_amount(amount):
            return jsonify({"error": "Invalid amount"}), 400

        income = Income(user_id=user_id, amount=amount)
        db.session.add(income)
        db.session.commit()
        
        return jsonify({"success": "Income added successfully"}), 200
    except Exception as e:
        logger.error(f"Error adding income: {str(e)}")
        return jsonify({"error": "Error adding income"}), 500

# Add Expense Endpoint
@main_bp.route('/expense', methods=['POST'])
@csrf.exempt
@jwt_required()
def add_expense():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        amount = data.get('amount')
        
        if not validate_amount(amount):
            return jsonify({"error": "Invalid amount"}), 400

        expense = Expense(user_id=user_id, amount=amount)
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({"success": "Expense added successfully"}), 200
    except Exception as e:
        logger.error(f"Error adding expense: {str(e)}")
        return jsonify({"error": "Error adding expense"}), 500

# Add Deposit Endpoint
@main_bp.route('/savings/deposit', methods=['POST'])
@csrf.exempt
@jwt_required()
def add_deposit():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        amount = data.get('amount')
        
        if not validate_amount(amount):
            return jsonify({"error": "Invalid amount"}), 400

        savings = Savings.query.filter_by(user_id=user_id).first()
        if not savings:
            savings = Savings(user_id=user_id, balance=0)
            db.session.add(savings)
        
        savings.balance += amount
        transaction = Transaction(user_id=user_id, type='deposit', amount=amount)
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({"success": "Deposit added successfully", "balance": savings.balance}), 200
    except Exception as e:
        logger.error(f"Error adding deposit: {str(e)}")
        return jsonify({"error": "Error adding deposit"}), 500

# Withdraw Endpoint
@main_bp.route('/savings/withdraw', methods=['POST'])
@csrf.exempt
@jwt_required()
def withdraw():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        amount = data.get('amount')
        
        if not validate_amount(amount):
            return jsonify({"error": "Invalid amount"}), 400

        savings = Savings.query.filter_by(user_id=user_id).first()
        if not savings or savings.balance < amount:
            return jsonify({"error": "Insufficient balance"}), 400

        savings.balance -= amount
        transaction = Transaction(user_id=user_id, type='withdraw', amount=amount)
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({"success": "Withdrawal successful", "balance": savings.balance}), 200
    except Exception as e:
        logger.error(f"Error processing withdrawal: {str(e)}")
        return jsonify({"error": "Error processing withdrawal"}), 500

# Saving Plans Endpoint
@main_bp.route('/saving-plans', methods=['GET'])
@csrf.exempt
@jwt_required()
def get_saving_plans():
    try:
        saving_plans = SavingPlan.query.all()
        logger.debug(f"Saving Plans fetched: {saving_plans}")
        saving_plans_data = [{"id": plan.id, "name": plan.name, "description": plan.description} for plan in saving_plans]
        return jsonify(saving_plans_data), 200
    except Exception as e:
        logger.error(f"Error fetching saving plans: {str(e)}")
        return jsonify({"error": "Error fetching saving plans"}), 500

# Single Saving Plan Endpoint
@main_bp.route('/saving-plans/<int:id>', methods=['GET'])
@csrf.exempt
@jwt_required()
def get_saving_plan(id):
    try:
        plan = SavingPlan.query.get(id)
        if not plan:
            return jsonify({"error": "Saving plan not found"}), 404
        return jsonify({"id": plan.id, "name": plan.name, "description": plan.description}), 200
    except Exception as e:
        logger.error(f"Error fetching saving plan: {str(e)}")
        return jsonify({"error": "Error fetching saving plan"}), 500

# Apply for Loan Endpoint
@main_bp.route('/loan/apply', methods=['POST'])
@csrf.exempt
@jwt_required()
def apply_for_loan():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        amount = data.get('amount')
        
        if not validate_amount(amount):
            return jsonify({"error": "Invalid amount"}), 400

        loan_application = LoanApplication(user_id=user_id, amount=amount, status="Pending")
        db.session.add(loan_application)
        db.session.commit()
        
        return jsonify({"success": "Loan application submitted"}), 200
    except Exception as e:
        logger.error(f"Error applying for loan: {str(e)}")
        return jsonify({"error": "Error applying for loan"}), 500

# Contact Form Endpoint
@main_bp.route('/contact', methods=['POST'])
@csrf.exempt
@limiter.limit("3 per hour")
def contact():
    try:
        data = request.get_json()
        
        if not validate_contact_form(data):
            return jsonify({"error": "Invalid contact form data"}), 400
        
        contact_message = ContactMessage(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            message=data.get('message')
        )
        db.session.add(contact_message)
        db.session.commit()
        
        send_contact_message(contact_message)
        
        return jsonify({"success": "Message sent successfully"}), 200
    except Exception as e:
        logger.error(f"Error sending contact message: {str(e)}")
        return jsonify({"error": "Error sending contact message"}), 500

