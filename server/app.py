from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os
import logging
import random
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure app with PostgreSQL (fallback to SQLite for development)
database_url = os.getenv(
    'DATABASE_URL',
    # 'sqlite:///middesk_validator.db'  # SQLite fallback for development
    # 'postgresql://postgres:password@localhost/middesk_validator'  # Use this for production
)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
print(f"🔗 Database URL: {database_url}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fsbdgfnhgvjnvhmvh' + str(random.randint(1, 1000000000000)))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'JKSRVHJVFBSRDFV' + str(random.randint(1, 1000000000000)))

# Initialize extensions
from models import db
db.init_app(app)

CORS(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# Create database tables
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created/verified successfully!")
    except Exception as e:
        print(f"⚠️ Database table creation warning: {e}")

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