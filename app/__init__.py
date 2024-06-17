from flask import Flask, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from .config import Config

csrf = CSRFProtect()
db = SQLAlchemy()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    csrf.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    
    @app.after_request
    def set_csrf_cookie(response):
        response.set_cookie('csrf_token', generate_csrf())
        return response
    
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    with app.app_context():
        db.create_all()
    
    return app
