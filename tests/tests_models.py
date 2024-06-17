import unittest
from myapp import create_app, db
from myapp.models import User, Savings, Transaction, LoanApplication, EmailVerificationToken, PasswordResetToken, ContactFormSubmission, ContactMessage, SavingPlan
from datetime import datetime

class TestModels(unittest.TestCase):

    def setUp(self):
        self.app = create_app('test')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_creation(self):
        user = User(first_name='John', last_name='Doe', phone_number='123456789', email='john@example.com')
        db.session.add(user)
        db.session.commit()

        saved_user = User.query.filter_by(email='john@example.com').first()
        self.assertIsNotNone(saved_user)
        self.assertEqual(saved_user.first_name, 'John')

    # Add more tests for other models...

if __name__ == '__main__':
    unittest.main()
