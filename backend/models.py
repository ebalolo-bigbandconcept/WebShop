from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Utilisateur")

class Clients(db.Model):
    __tablename__ = "clients"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    rue = db.Column(db.String(200), nullable=False)
    ville = db.Column(db.String(100), nullable=False)
    code_postal = db.Column(db.String(20), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)

class Devis(db.Model):
    __tablename__ = "devis"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    client_id = db.Column(db.Integer(), db.ForeignKey('clients.id'), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date(), nullable=False)
    montant_HT = db.Column(db.Float(), nullable=False)
    montant_TVA = db.Column(db.Float(), nullable=False)
    tauxTVA_id = db.Column(db.Integer(), db.ForeignKey('taux_tva.id'), nullable=False)
    montant_TTC = db.Column(db.Float(), nullable=False)
    statut = db.Column(db.String(50), nullable=False)

class Articles(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    prix_achat_HT = db.Column(db.Float(), nullable=False)
    prix_vente_HT = db.Column(db.Float(), nullable=False)

class DevisArticles(db.Model):
    __tablename__ = "devis_articles"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    devis_id = db.Column(db.Integer(), db.ForeignKey('devis.id'), nullable=False)
    article_id = db.Column(db.Integer(), db.ForeignKey('articles.id'), nullable=False)

class TauxTVA(db.Model):
    __tablename__ = "taux_tva"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    taux = db.Column(db.Float(), nullable=False, default=0.20)

# Marshmallow Schema to strucuture the JSON response
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

class ClientsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Clients

class DevisSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Devis

class ArticlesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Articles