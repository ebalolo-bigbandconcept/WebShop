from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    mdp = db.Column(db.Text, nullable=False)
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
    email = db.Column(db.String(345), nullable=False)
    caduque = db.Column(db.Boolean, nullable=False, default=False)

class Devis(db.Model):
    __tablename__ = "devis"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    client_id = db.Column(db.Integer(), db.ForeignKey('clients.id'), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date(), nullable=False)
    montant_HT = db.Column(db.Float(), nullable=False)
    montant_TVA = db.Column(db.Float(), nullable=False)
    montant_TTC = db.Column(db.Float(), nullable=False)
    statut = db.Column(db.String(50), nullable=False)
    date_paiement = db.Column(db.Date(), nullable=True)
    
    is_location = db.Column(db.Boolean, nullable=False, default=False)
    first_contribution_amount = db.Column(db.Float(), nullable=True)
    location_monthly_total = db.Column(db.Float(), nullable=True)
    location_monthly_total_ht = db.Column(db.Float(), nullable=True)
    location_total = db.Column(db.Float(), nullable=True)
    location_total_ht = db.Column(db.Float(), nullable=True)
    
    client = db.relationship('Clients', backref='devis', lazy=True)
    articles = db.relationship('DevisArticles', backref='devis', lazy=True)

class Articles(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    prix_achat_HT = db.Column(db.Float(), nullable=False)
    prix_vente_HT = db.Column(db.Float(), nullable=False)
    taux_tva_id = db.Column(db.Integer(), db.ForeignKey('taux_tva.id'), nullable=False)
    
    taux_tva = db.relationship('TauxTVA', backref='articles', lazy=True)

class DevisArticles(db.Model):
    __tablename__ = "devis_articles"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    devis_id = db.Column(db.Integer(), db.ForeignKey('devis.id'), nullable=False)
    article_id = db.Column(db.Integer(), db.ForeignKey('articles.id'), nullable=False)
    quantite = db.Column(db.Integer(), nullable=False)
    taux_tva_id = db.Column(db.Integer(), db.ForeignKey('taux_tva.id'), nullable=True)
    commentaire = db.Column(db.Text, nullable=True)
    
    article = db.relationship('Articles', backref='devis_articles', lazy=True)
    taux_tva = db.relationship('TauxTVA', lazy=True)

class TauxTVA(db.Model):
    __tablename__ = "taux_tva"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    taux = db.Column(db.Float(), nullable=False, default=0.20)


class Parameters(db.Model):
    __tablename__ = "parameters"
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    margin_rate = db.Column(db.Float(), nullable=False, default=0.0)
    margin_rate_location = db.Column(db.Float(), nullable=False, default=0.0)
    location_time = db.Column(db.Integer(), nullable=False, default=0)
    location_subscription_cost = db.Column(db.Float(), nullable=False, default=0.0)
    location_interests_cost = db.Column(db.Float(), nullable=False, default=0.0)
    general_conditions_sales = db.Column(db.Text, nullable=False, default="")
    company_name = db.Column(db.String(200), nullable=False, default="")
    company_address_line1 = db.Column(db.String(200), nullable=False, default="")
    company_address_line2 = db.Column(db.String(200), nullable=False, default="")
    company_zip = db.Column(db.String(20), nullable=False, default="")
    company_city = db.Column(db.String(100), nullable=False, default="")
    company_phone = db.Column(db.String(50), nullable=False, default="")
    company_email = db.Column(db.String(200), nullable=False, default="")
    company_iban = db.Column(db.String(64), nullable=False, default="")
    company_tva = db.Column(db.String(64), nullable=False, default="")
    company_siret = db.Column(db.String(64), nullable=False, default="")
    company_aprm = db.Column(db.String(64), nullable=False, default="")

# Marshmallow Schema to strucuture the JSON response
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

class ClientsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Clients
        load_instance = True

class TauxTVASchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TauxTVA
        load_instance = True

class ArticlesSchema(ma.SQLAlchemyAutoSchema):
    taux_tva = ma.Nested('TauxTVASchema')
    
    class Meta:
        model = Articles
        load_instance = True

class DevisArticlesSchema(ma.SQLAlchemyAutoSchema):
    article = ma.Nested('ArticlesSchema')
    taux_tva = ma.Nested('TauxTVASchema')
    
    class Meta:
        model = DevisArticles
        load_instance = True

class DevisSchema(ma.SQLAlchemyAutoSchema):
    client = ma.Nested('ClientsSchema')
    articles = ma.Nested('DevisArticlesSchema', many=True)
    
    class Meta:
        model = Devis
        load_instance = True


class ParametersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Parameters
        load_instance = True