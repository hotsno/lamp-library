from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime
from routes.api import api_bp
from file_watcher import start_watcher, stop_watcher

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(api_bp, url_prefix='/api')
    setup_error_handlers(app)
    
    # Initialize file watcher if MANGA_PATH is set
    manga_path = os.environ.get('MANGA_PATH')
    if manga_path:
        try:
            start_watcher()
            print(f"File watcher initialized for MANGA_PATH: {manga_path}")
        except Exception as e:
            print(f"Failed to initialize file watcher: {e}")
    
    return app

def setup_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
