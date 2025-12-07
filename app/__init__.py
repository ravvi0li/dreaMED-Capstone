"""
Flask Application Factory
"""

from flask import Flask
from flask_cors import CORS
import os

def create_app(config_name='development'):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load config
    if config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register main route
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
