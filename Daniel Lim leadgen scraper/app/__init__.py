import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    """Initialize the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-for-testing')
    
    csrf.init_app(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.search import search_bp
    from app.routes.financial import financial_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(financial_bp)
    
    return app
