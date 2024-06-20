# routes.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask_wtf.csrf import generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from .validators import validate_contact_form, validate_amount, validate_email, validate_phone_number
from .services import send_contact_message
from .models import ContactMessage, Savings, SavingPlan, Transaction, User, LoanApplication, Income, Expense
from . import db, csrf

main_bp = Blueprint('main', __name__, url_prefix='/api')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@main_bp.route('/about-us', methods=['GET'])
def get_about_us():
    try:
        content = {
            "title": "ABOUT US",
            "description": "Healthfin recognizes the burden of healthcare costs. We bridge the gap to affordability by offering flexible and affordable health insurance plans, along with expert advice and personalized support, aiming to provide value with competitive rates and flexible repayment options."
        }
        return jsonify(content)
    except Exception as e:
        logger.error(f"Error fetching about us content: {str(e)}")
        return jsonify({"error": "Error fetching about us content"}), 500

@main_bp.route('/mission', methods=['GET'])
def get_mission():
    try:
        content = {
            "title": "OUR MISSION",
            "description": "To champion well-being by providing accessible, comprehensive health insurance and fostering a culture of preventative care for a healthier and more vibrant future."
        }
        return jsonify(content)
    except Exception as e:
        logger.error(f"Error fetching mission content: {str(e)}")
        return jsonify({"error": "Error fetching mission content"}), 500

@main_bp.route('/vision', methods=['GET'])
def get_vision():
    try:
        content = {
            "title": "OUR VISION",
            "description": "We envision a future where healthy living is accessible to all. By connecting people with affordable and comprehensive health services, we empower individuals to live healthier, more fulfilling lives."
        }
        return jsonify(content)
    except Exception as e:
        logger.error(f"Error fetching vision content: {str(e)}")
        return jsonify({"error": "Error fetching vision content"}), 500

@main_bp.route('/message', methods=['GET'])
def get_message():
    try:
        content = {
            "title": "OUR MESSAGE",
            "description": "Healthfin is a health insurance company built on the foundation of empowering your well-being. We believe health insurance should be more than just a policy; it is the support you need to be an active partner in your journey to a healthier, happier you."
        }
        return jsonify(content)
    except Exception as e:
        logger.error(f"Error fetching message content: {str(e)}")
        return jsonify({"error": "Error fetching message content"}), 500


@main_bp.route('/contact-info', methods=['GET'])
def contact_info():
    return jsonify({
        "email": "email@gmail.com",
        "phone": "+254712345678"
    })

@main_bp.route('/get-csrf-token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()
    return jsonify({"csrf_token": token})

@main_bp.route('/send-message', methods=['POST'])
def send_message():
    logger.debug("Received a request to send a message.")
    data = request.get_json()
    logger.debug(f"Request data: {data}")

    errors = validate_contact_form(data)
    if errors:
        logger.debug(f"Validation errors: {errors}")
        return jsonify({"errors": errors}), 400
    
    success, error_message = send_contact_message(data)
    if not success:
        logger.error(f"Failed to send message: {error_message}")
        return jsonify({"error": error_message}), 500
    
    new_message = ContactMessage(name=data['name'], email=data['email'], message=data['message'])
    try:
        db.session.add(new_message)
        db.session.commit()
        logger.debug("Message saved to database successfully.")
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to save message to database."}), 500
    
    return jsonify({"success": "Message sent"}), 200

@main_bp.route('/register', methods=['POST'])
def register():
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

@main_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({"token": access_token}), 200

@main_bp.route('/dashboard', methods=['GET'])
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

@main_bp.route('/finances', methods=['GET'])
@jwt_required()
def get_finances():
    try:
        user_id = get_jwt_identity()
        income = Income.query.filter_by(user_id=user_id).all()
        expenses = Expense.query.filter_by(user_id=user_id).all()
        transactions = Transaction.query.filter_by(user_id=user_id).all()

        income_data = [{"id": i.id, "amount": i.amount} for i in income]
        expenses_data = [{"id": e.id, "amount": e.amount} for e in expenses]
        transactions_data = [{"id": t.id, "amount": t.amount, "type": t.type} for t in transactions]

        return jsonify({
            "income": income_data,
            "expenses": expenses_data,
            "transactions": transactions_data
        }), 200
    except Exception as e:
        logger.error(f"Error fetching finances data: {str(e)}")
        return jsonify({"error": "Error fetching finances data"}), 500

@main_bp.route('/expenses/summary', methods=['GET'])
@jwt_required()
def get_expenses_summary():
    try:
        user_id = get_jwt_identity()
        expenses = Expense.query.filter_by(user_id=user_id).all()

        total_expenses = sum([expense.amount for expense in expenses])

        return jsonify({
            "total_expenses": total_expenses
        }), 200
    except Exception as e:
        logger.error(f"Error fetching expenses summary: {str(e)}")
        return jsonify({"error": "Error fetching expenses summary"}), 500

# Route to add income
@main_bp.route('/income', methods=['POST'])
@jwt_required()
def add_income():
    data = request.get_json()
    amount = data.get('amount')

    # Validate the amount
    errors = validate_amount(amount)
    if errors:
        return jsonify({"errors": errors}), 400

    user_id = get_jwt_identity()
    new_income = Income(user_id=user_id, amount=amount)

    try:
        db.session.add(new_income)
        db.session.commit()
        return jsonify({"message": "Income added successfully"}), 201
    except Exception as e:
        logger.error(f"Error adding income: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to add income"}), 500

# Route to add expense
@main_bp.route('/expense', methods=['POST'])
@jwt_required()
def add_expense():
    data = request.get_json()
    amount = data.get('amount')

    # Validate the amount
    errors = validate_amount(amount)
    if errors:
        return jsonify({"errors": errors}), 400

    user_id = get_jwt_identity()
    new_expense = Expense(user_id=user_id, amount=amount)

    try:
        db.session.add(new_expense)
        db.session.commit()
        return jsonify({"message": "Expense added successfully"}), 201
    except Exception as e:
        logger.error(f"Error adding expense: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to add expense"}), 500

@main_bp.route('/savings/deposit', methods=['POST'])
@jwt_required()
def deposit_savings():
    data = request.get_json()
    amount = data.get('amount')

    # Validate the amount
    errors = validate_amount(amount)
    if errors:
        return jsonify({"errors": errors}), 400

    user_id = get_jwt_identity()
    savings = Savings.query.filter_by(user_id=user_id).first()

    if not savings:
        # Create a savings account for the user if it doesn't exist
        savings = Savings(user_id=user_id, balance=0)
        db.session.add(savings)

    savings.balance += amount

    try:
        db.session.commit()
        return jsonify({"message": "Savings deposited successfully"}), 200
    except Exception as e:
        logger.error(f"Error depositing savings: {str(e)}")
        return jsonify({"error": "Failed to deposit savings"}), 500


@main_bp.route('/savings/withdraw', methods=['POST'])
@jwt_required()
def withdraw_savings():
    data = request.get_json()
    amount = data.get('amount')

    errors = validate_amount(amount)
    if errors:
        return jsonify({"errors": errors}), 400

    user_id = get_jwt_identity()
    savings = Savings.query.filter_by(user_id=user_id).first()

    if not savings:
        return jsonify({"error": "Savings account not found"}), 404

    if amount > savings.balance:
        return jsonify({"error": "Insufficient funds"}), 400

    savings.balance -= amount

    try:
        db.session.commit()
        return jsonify({"message": "Savings withdrawn successfully"}), 200
    except Exception as e:
        logger.error(f"Error withdrawing savings: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to withdraw savings"}), 500

@main_bp.route('/saving-plans', methods=['GET'])
@jwt_required()
def get_saving_plans():
    user_id = get_jwt_identity()
    saving_plans = SavingPlan.query.filter_by(user_id=user_id).all()
    saving_plans_data = [{"id": plan.id, "name": plan.name, "amount": plan.amount} for plan in saving_plans]
    return jsonify(saving_plans_data), 200

@main_bp.route('/saving-plans/<int:id>', methods=['GET'])
@jwt_required()
def get_saving_plan(id):
    user_id = get_jwt_identity()
    saving_plan = SavingPlan.query.filter_by(user_id=user_id, id=id).first()

    if not saving_plan:
        return jsonify({"error": "Saving plan not found"}), 404

    saving_plan_data = {
        "id": saving_plan.id,
        "name": saving_plan.name,
        "amount": saving_plan.amount
    }
    return jsonify(saving_plan_data), 200

@main_bp.route('/savings/history', methods=['GET'])
@jwt_required()
def get_savings_history():
    user_id = get_jwt_identity()
    savings = Savings.query.filter_by(user_id=user_id).first()

    if not savings:
        return jsonify({"error": "Savings account not found"}), 404

    transactions = Transaction.query.filter_by(user_id=user_id).all()
    transactions_data = [{"id": t.id, "amount": t.amount, "type": t.type} for t in transactions]
    return jsonify(transactions_data), 200

# Error handlers
@main_bp.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400

@main_bp.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": "Unauthorized"}), 401

@main_bp.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@main_bp.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500
