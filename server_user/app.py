"""
Server User - Port 3000
Handles user-facing features: browsing, booking, payments.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, session, send_from_directory
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from datetime import timedelta
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'user_secret_2024')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
app.config['SESSION_COOKIE_NAME'] = 'user_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True

from routes.auth import auth_bp
from routes.booking import booking_bp
from routes.services import services_bp

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(booking_bp, url_prefix='/api')
app.register_blueprint(services_bp, url_prefix='/api')

# Serve frontend HTML files
@app.route('/')
@app.route('/index.html')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    if os.path.exists(os.path.join(app.static_folder, filename)):
        return send_from_directory('static', filename)
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=3000)
