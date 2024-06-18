# app/__init__.py

from flask import Flask, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from .config import Config

# Initialize extensions
csrf = CSRFProtect()
db = SQLAlchemy()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()

def create_app():
    # Create the Flask application
    app = Flask(__name__)

    # Load configuration from the config object
    app.config.from_object(Config)

    # Initialize extensions with the app
    csrf.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate with the app and db instance

    # Set up Flask-Limiter with SQLAlchemy as the storage backend
    limiter.init_app(app)

    # Set CSRF token in a cookie after each request
    @app.after_request
    def set_csrf_cookie(response):
        response.set_cookie('csrf_token', generate_csrf())
        return response

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
