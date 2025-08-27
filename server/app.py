from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure app
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

CORS(app)
jwt = JWTManager(app)

# Import and register blueprints
from routes.uploads import uploads_bp
from routes.simple_validation import simple_validation_bp
from routes.history import history_bp

app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
app.register_blueprint(simple_validation_bp)
app.register_blueprint(history_bp,url_prefix='/api/history')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)