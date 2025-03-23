from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from typing import Dict, Any
import logging

from ..models import Entity, Zone, Alert
from ..monitoring import get_system_metrics
from ..visualization import create_spatial_map

dashboard = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)

@dashboard.route('/dashboard')
@login_required
def main_dashboard():
    """Render main dashboard."""
    try:
        metrics = get_system_metrics()
        entities = Entity.get_active()
        alerts = Alert.get_active()
        
        return render_template(
            'dashboard/main.html',
            metrics=metrics,
            entities=entities,
            alerts=alerts
        )
    except Exception as e:
        logger.error(f"Dashboard render error: {str(e)}")
        return render_template('error.html', error=str(e))

@dashboard.route('/api/spatial-map')
@login_required
def get_spatial_map():
    """Get spatial map data."""
    try:
        entities = Entity.get_active()
        zones = Zone.get_all()
        
        map_data = create_spatial_map(entities, zones)
        return jsonify(map_data)
        
    except Exception as e:
        logger.error(f"Spatial map generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500 