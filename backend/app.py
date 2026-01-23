from flask import Flask, request, session, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import ApplicationConfig
from models import db, ma, User, TauxTVA, Parameters
from dotenv import load_dotenv
import os
import secrets
import logging
import json
from datetime import datetime
from routes.admin import admin_bp
from routes.articles import articles_bp
from routes.auth import auth_bp, auth_alias_bp, limiter
from routes.clients import clients_bp
from routes.devis import devis_bp
from routes.docusign import docusign_bp
from werkzeug.middleware.proxy_fix import ProxyFix

# Log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# CONSTANTS
load_dotenv()

ADMIN_MAIL = open("/run/secrets/ADMIN_MAIL").read().strip() if os.path.exists("/run/secrets/ADMIN_MAIL") else os.getenv('ADMIN_MAIL')
ADMIN_PASSWORD = open("/run/secrets/ADMIN_PASSWORD").read().strip() if os.path.exists("/run/secrets/ADMIN_PASSWORD") else os.getenv('ADMIN_PASSWORD')
FRONTEND_URL = os.getenv('FRONTEND_URL')

if not ADMIN_MAIL or not ADMIN_PASSWORD:
    logging.error("ADMIN_MAIL et ADMIN_PASSWORD doivent être définis dans les variables d'environnement ou les secrets Docker.")
    raise ValueError("ADMIN_MAIL et ADMIN_PASSWORD doivent être définis dans les variables d'environnement ou les secrets Docker.")

# Config App
app = Flask(__name__, template_folder="pdf")
app.config.from_object(ApplicationConfig)
CORS(app, origins=[FRONTEND_URL], supports_credentials=True, allow_headers=["Content-Type", "X-CSRF-Token"])
bcrypt = Bcrypt()
bcrypt.init_app(app)
server_session = Session(app)

# Initialize rate limiter
limiter.init_app(app)

# Trust reverse proxy headers (X-Forwarded-Proto, Host, etc.) for correct https URLs
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Config structured logging with JSON format for better parsing
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'user_email'):
            log_data['user_email'] = record.user_email
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'action'):
            log_data['action'] = record.action
        if hasattr(record, 'resource'):
            log_data['resource'] = record.resource
        if hasattr(record, 'status'):
            log_data['status'] = record.status
            
        return json.dumps(log_data)

# Configure file and console handlers
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "app.log"))
file_handler.setFormatter(JSONFormatter())
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
console_handler.setLevel(logging.INFO)

# Security events log (separate file for audit trail)
security_handler = logging.FileHandler(os.path.join(LOG_DIR, "security.log"))
security_handler.setFormatter(JSONFormatter())
security_handler.setLevel(logging.WARNING)

# Get logger and configure
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Security logger for audit events
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)
security_logger.addHandler(security_handler)
security_logger.addHandler(console_handler)
security_logger.propagate = False

# Request logging middleware
@app.before_request
def log_request():
    # Log all requests with relevant info
    if request.endpoint and not request.endpoint.startswith('static'):
        extra = {
            'ip_address': request.remote_addr,
            'action': f"{request.method} {request.path}",
            'user_id': session.get('user_id', 'anonymous')
        }
        logging.info(f"Request: {request.method} {request.path}", extra=extra)


# CSRF protection middleware: require token on unsafe methods
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
CSRF_EXEMPT = {
    'auth_bp.login_user',
    'auth_bp.register',
    'auth_alias_bp.login_user_alias',
    'docusign.webhook',
}


@app.before_request
def enforce_csrf():
    # Allow disabling CSRF entirely via config (used in tests)
    if not app.config.get('WTF_CSRF_ENABLED', True):
        return None

    if request.method in SAFE_METHODS:
        return None

    # Skip endpoints that are explicitly exempted
    if request.endpoint in CSRF_EXEMPT:
        return None

    token_session = session.get("csrf_token")
    token_request = request.headers.get("X-CSRF-Token") or request.cookies.get("XSRF-TOKEN")

    if not token_session:
        return jsonify({"error": "Missing CSRF session token"}), 401

    if not token_request or token_request != token_session:
        return jsonify({"error": "CSRF token missing or invalid"}), 403

    return None

# Sync rate limiter enabled flag with config on each request (so tests can disable it)
@app.before_request
def sync_rate_limiter_enabled():
    try:
        limiter.enabled = app.config.get('RATELIMIT_ENABLED', True)
    except Exception:
        pass

# Config BDD
db.init_app(app)
ma.init_app(app)
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(articles_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(auth_alias_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(devis_bp)
app.register_blueprint(docusign_bp)

# Initialize default data (only if tables exist)
# This will be called after migrations are run
def init_default_data():
    with app.app_context():
        try:
            # Créer le 1er admin si la table users est vide.
            table_empty_user = User.query.filter_by(email=ADMIN_MAIL).first() is None

            if table_empty_user:
                hashed_admin_password = bcrypt.generate_password_hash(ADMIN_PASSWORD).decode('utf-8')
                admin_user = User(
                    nom='Admin',
                    prenom='Admin',
                    email=ADMIN_MAIL,
                    mdp=hashed_admin_password,
                    role='Administrateur'
                )
                db.session.add(admin_user)
                db.session.commit()
            
            # Ajoute la TVA 20% si la table est vide
            existing_tva = {row.taux for row in TauxTVA.query.all()}
            needed_tva = [0.20, 0.10]
            for rate in needed_tva:
                if rate not in existing_tva:
                    db.session.add(TauxTVA(taux=rate))
            db.session.commit()

            # Ajoute une ligne de parametres par defaut si la table est vide
            has_params = Parameters.query.first() is not None
            if not has_params:
                params = Parameters()
                db.session.add(params)
                db.session.commit()
        except Exception as e:
            logging.warning(f"Could not initialize default data (tables may not exist yet): {e}")
            logging.info("Run 'flask db upgrade' to create tables, then restart the app.")

### Main ###

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)