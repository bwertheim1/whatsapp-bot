from flask import Blueprint, send_from_directory, render_template
from utils.logging_utils import log_info, log_error

# Initialize blueprint
landing_bp = Blueprint('landing', __name__)

@landing_bp.route('/')
def index():
    """Serve the landing page"""
    return send_from_directory('.', 'index.html')

@landing_bp.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename) 