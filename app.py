from flask import Flask, jsonify
from flask_cors import CORS
import logging
import time
from dotenv import load_dotenv
from routes.api import api_bp
from file_watcher import initialize_and_start_watcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(api_bp, url_prefix='/api')
    setup_error_handlers(app)
    
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
    # app = create_app()
    # port = int(os.environ.get('PORT', 5001))
    # app.run(host='0.0.0.0', port=port, debug=True)
    initialize_and_start_watcher()
    while True:
        time.sleep(1)