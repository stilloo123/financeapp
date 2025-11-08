"""
Flask Application

Main entry point for the mortgage vs investment optimizer API.
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__,
                static_folder='../frontend',
                static_url_path='')

    # Enable CORS for frontend
    CORS(app)

    # Import and register blueprints
    from backend.api.routes import api_bp
    app.register_blueprint(api_bp)

    # Serve frontend
    @app.route('/')
    def index():
        """Serve the main HTML page."""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def static_files(path):
        """Serve static files (CSS, JS, etc.)."""
        return send_from_directory(app.static_folder, path)

    return app


if __name__ == '__main__':
    app = create_app()
    print("\n" + "=" * 70)
    print("Mortgage vs. Investment Optimizer - Backend Server")
    print("=" * 70)
    print("\nServer starting...")
    print("API Endpoints:")
    print("  GET  http://localhost:8080/api/health")
    print("  GET  http://localhost:8080/api/data-info")
    print("  POST http://localhost:8080/api/calculate")
    print("\nFrontend:")
    print("  http://localhost:8080/")
    print("\n" + "=" * 70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=8080)
