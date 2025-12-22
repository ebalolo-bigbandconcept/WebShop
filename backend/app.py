from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session
from flask_migrate import Migrate
from config import ApplicationConfig
from models import db, ma, User, TauxTVA, Parameters
from dotenv import load_dotenv
import os, logging
from routes.admin import admin_bp
from routes.articles import articles_bp
from routes.auth import auth_bp
from routes.clients import clients_bp
from routes.devis import devis_bp

# CONSTANTS
load_dotenv()

ADMIN_MAIL = open("/run/secrets/ADMIN_MAIL").read().strip() if os.path.exists("/run/secrets/ADMIN_MAIL") else os.getenv('ADMIN_MAIL')
ADMIN_PASSWORD = open("/run/secrets/ADMIN_PASSWORD").read().strip() if os.path.exists("/run/secrets/ADMIN_PASSWORD") else os.getenv('ADMIN_PASSWORD')
FRONTEND_URL = os.getenv('FRONTEND_URL')

if not ADMIN_MAIL or not ADMIN_PASSWORD:
    logging.error("ADMIN_MAIL et ADMIN_PASSWORD doivent être définis dans les variables d'environnement ou les secrets Docker.")
    raise ValueError("ADMIN_MAIL et ADMIN_PASSWORD doivent être définis dans les variables d'environnement ou les secrets Docker.")

# Config App
app = Flask(__name__,template_folder="pdf")
app.config.from_object(ApplicationConfig)
CORS(app, origins=[FRONTEND_URL], supports_credentials=True)
bcrypt = Bcrypt()
bcrypt.init_app(app)
server_session = Session(app)

# Config logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler("app.log"),logging.StreamHandler()]
)

# Config BDD
db.init_app(app)
ma.init_app(app)
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(articles_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(devis_bp)

# Initialize default data (only if tables exist)
# This will be called after migrations are run
def init_default_data():
    with app.app_context():
        try:
            # Créer le 1er admin si la table users est vide.
            table_empty_user = User.query.filter_by(email=ADMIN_MAIL).first() is None

            if table_empty_user:
                hashed_admin_password = bcrypt.generate_password_hash(ADMIN_PASSWORD).decode('utf-8')
                admin_user = User(nom='Admin',prenom='Admin',email=ADMIN_MAIL,mdp=hashed_admin_password,role='Administrateur')
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