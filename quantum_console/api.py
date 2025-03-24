from flask import Blueprint, jsonify

# Create a Blueprint for the API
api_bp = Blueprint('api', __name__)

@api_bp.route('/api/health', methods=['GET'])
def api_health_check():
    """Health check endpoint for the API."""
    return jsonify({
        'status': 'healthy',
        'message': 'API is running'
    })

# Add more API routes as needed 