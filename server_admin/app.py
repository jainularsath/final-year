"""
Server Admin - Port 3002
Full platform admin: manage vendors, services, approvals.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, send_from_directory, request
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from datetime import timedelta
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'admin_secret_2024') + '_admin'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
app.config['SESSION_COOKIE_NAME'] = 'admin_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True

from routes.auth import auth_bp
from routes.manage_vendors import vendors_bp
from routes.manage_services import services_bp

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(vendors_bp, url_prefix='/api')
app.register_blueprint(services_bp, url_prefix='/api')

@app.route('/')
@app.route('/index.html')
def index():
    return send_from_directory('static', 'index.html')

@app.before_request
def intercept_uploads():
    if request.path.startswith('/static/uploads/'):
        filename = request.path[len('/static/uploads/'):]
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'server_user', 'static', 'uploads')
        return send_from_directory(upload_dir, filename)

@app.route('/<path:filename>')
def static_files(filename):
    if os.path.exists(os.path.join(app.static_folder, filename)):
        return send_from_directory('static', filename)
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=3002)
