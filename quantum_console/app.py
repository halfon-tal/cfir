from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_login import LoginManager, login_required
import logging
from typing import Dict, Any
import os
from datetime import datetime

from .auth import auth_bp, init_auth
from .dashboard import dashboard_bp
from .monitoring import monitoring_bp
from .api import api_bp
from .websocket import init_websocket
from .config import Config
from .database import init_db
from .logging import init_logging

app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
socketio = SocketIO(app)
login_manager = LoginManager()
db = init_db(app)
logger = init_logging(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(api_bp)

# Initialize authentication
init_auth(app, login_manager)

# Initialize WebSocket handlers
init_websocket(socketio)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not found',
        'message': str(error)
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500 