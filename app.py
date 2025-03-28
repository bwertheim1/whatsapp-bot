from flask import Flask
from routes.webhook_routes import webhook_bp
from routes.landing_routes import landing_bp
from services.supabase_service import SupabaseService
from utils.logging_utils import log_info, log_error
import os

def create_app():
    """Create and configure the Flask application"""
    # Initialize Flask app
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(webhook_bp)
    app.register_blueprint(landing_bp)
    
    # Initialize database
    initialize_database()
    
    log_info("Application initialized successfully")
    return app

def initialize_database():
    """Initialize the database connection and verify tables"""
    log_info("Initializing database...")
    if SupabaseService.initialize_database():
        log_info("Database initialized successfully")
    else:
        log_error("Failed to initialize database")

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=port)
    log_info(f"Application started on port {port}") 