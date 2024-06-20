from app import create_app, db
from app.models import User, Savings, SavingPlan, Transaction, Income, Expense
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()

    # Create test users
    user1 = User(email="user1@example.com", password_hash=generate_password_hash("password123"))
    user2 = User(email="user2@example.com", password_hash=generate_password_hash("password123"))
    user3 = User(email="user3@example.com", password_hash=generate_password_hash("password123"))
    user4 = User(email="user4@example.com", password_hash=generate_password_hash("password123"))

    db.session.add_all([user1, user2, user3, user4])
    db.session.commit()

    print(f"Created users: {[user1.id, user2.id, user3.id, user4.id]}")

    # Create savings for the test users
    savings1 = Savings(user_id=user1.id, balance=1000.00)
    savings2 = Savings(user_id=user2.id, balance=500.00)
    savings3 = Savings(user_id=user3.id, balance=1200.00)
    savings4 = Savings(user_id=user4.id, balance=800.00)

    db.session.add_all([savings1, savings2, savings3, savings4])
    db.session.commit()

    print(f"Created savings: {[savings1.id, savings2.id, savings3.id, savings4.id]}")

    # Create saving plans
    plan1 = SavingPlan(name="Monthly Deposit", description="Save monthly")
    plan2 = SavingPlan(name="Fixed Deposit", description="Save with fixed interest")
    plan3 = SavingPlan(name="Yearly Deposit", description="Save yearly")
    plan4 = SavingPlan(name="Weekly Deposit", description="Save weekly")

    db.session.add_all([plan1, plan2, plan3, plan4])
    db.session.commit()

    # Verify saving plans are added
    saving_plans = SavingPlan.query.all()
    for plan in saving_plans:
        print(f"Saving Plan: {plan.id}, {plan.name}, {plan.description}")

    # Create transactions for each user
    transactions = []
    for user in [user1, user2, user3, user4]:
        transactions.append(Transaction(user_id=user.id, type="deposit", amount=500.00, timestamp=datetime.now() - timedelta(days=1)))
        transactions.append(Transaction(user_id=user.id, type="withdraw", amount=200.00, timestamp=datetime.now() - timedelta(days=2)))
        transactions.append(Transaction(user_id=user.id, type="deposit", amount=300.00, timestamp=datetime.now() - timedelta(days=3)))
        transactions.append(Transaction(user_id=user.id, type="withdraw", amount=100.00, timestamp=datetime.now() - timedelta(days=4)))

    db.session.add_all(transactions)
    db.session.commit()

    print("Created transactions")

    # Create incomes for each user
    incomes = []
    for user in [user1, user2, user3, user4]:
        incomes.append(Income(user_id=user.id, amount=200.00, date=datetime.now() - timedelta(days=1)))
        incomes.append(Income(user_id=user.id, amount=150.00, date=datetime.now() - timedelta(days=2)))
        incomes.append(Income(user_id=user.id, amount=300.00, date=datetime.now() - timedelta(days=3)))
        incomes.append(Income(user_id=user.id, amount=250.00, date=datetime.now() - timedelta(days=4)))

    db.session.add_all(incomes)
    db.session.commit()

    print("Created incomes")

    # Create expenses for each user
    expenses = []
    for user in [user1, user2, user3, user4]:
        expenses.append(Expense(user_id=user.id, amount=50.00, date=datetime.now() - timedelta(days=1)))
        expenses.append(Expense(user_id=user.id, amount=30.00, date=datetime.now() - timedelta(days=2)))
        expenses.append(Expense(user_id=user.id, amount=70.00, date=datetime.now() - timedelta(days=3)))
        expenses.append(Expense(user_id=user.id, amount=60.00, date=datetime.now() - timedelta(days=4)))

    db.session.add_all(expenses)
    db.session.commit()

    print("Created expenses")

    print("Test data created successfully.")
