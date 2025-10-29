from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session
from config import ApplicationConfig
from models import db, ma, User, TauxTVA
from dotenv import load_dotenv
import os, logging
from routes.admin import admin_bp
from routes.articles import articles_bp
from routes.auth import auth_bp
from routes.clients import clients_bp
from routes.devis import devis_bp

# CONSTANTS
load_dotenv()
ADMIN_MAIL = os.getenv('ADMIN_MAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Config App
app = Flask(__name__)
app.config.from_object(ApplicationConfig)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
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

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(articles_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(devis_bp)

with app.app_context():
    db.create_all()
    # Créer le 1er admin si la table users est vide.
    table_empty_user = User.query.filter_by(email=ADMIN_MAIL).first() is None

    if table_empty_user:
        hashed_admin_password = bcrypt.generate_password_hash(ADMIN_PASSWORD)
        admin_user = User(first_name='Admin',last_name='Admin',email=ADMIN_MAIL,password=hashed_admin_password,role='Administrateur')
        db.session.add(admin_user)
        db.session.commit()
    
    table_empty_tva = TauxTVA.query.first() is None
    if table_empty_tva:
        taux20 = TauxTVA(taux=0.20)
        db.session.add(taux20)
        db.session.commit()

### Main ###

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)