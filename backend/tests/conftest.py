"""Pytest configuration and fixtures for WebShop backend tests.

This module provides shared fixtures for testing the Flask application,
including database setup, authentication helpers, and test data factories.
"""

import os
import sys
from datetime import datetime

import pytest
from flask_bcrypt import Bcrypt

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app import app as flask_app
from models import (
    Articles,
    Clients,
    Devis,
    DevisArticles,
    Parameters,
    TauxTVA,
    User,
    db,
)
from tests.fixtures.test_config import TestConfig


@pytest.fixture(scope="function")
def app():
    """Create and configure a Flask application instance for testing.

    Yields:
        Flask: Configured Flask application with test settings
    """
    # Configure app for testing
    flask_app.config.from_object(TestConfig)

    # Disable CSRF for testing
    flask_app.config["WTF_CSRF_ENABLED"] = False

    # Create application context
    with flask_app.app_context():
        # Create all tables
        db.create_all()

        # Initialize default data
        _init_test_defaults()

        yield flask_app

        # Cleanup
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Create a test client for the Flask application.

    Args:
        app: Flask application fixture

    Yields:
        FlaskClient: Test client for making HTTP requests
    """
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """Provide a database session for tests.

    Args:
        app: Flask application fixture

    Yields:
        Session: SQLAlchemy database session
    """
    with app.app_context():
        yield db.session


@pytest.fixture(scope="function")
def bcrypt_instance(app):
    """Provide a Bcrypt instance for password hashing.

    Args:
        app: Flask application fixture

    Returns:
        Bcrypt: Configured Bcrypt instance
    """
    return Bcrypt(app)


@pytest.fixture
def admin_user(db_session, bcrypt_instance):
    """Create an admin user for testing.

    Args:
        db_session: Database session fixture
        bcrypt_instance: Bcrypt fixture for password hashing

    Returns:
        User: Admin user instance
    """
    hashed_password = bcrypt_instance.generate_password_hash("AdminPass123!").decode(
        "utf-8"
    )
    admin = User(
        nom="Admin",
        prenom="Test",
        email="admin@test.com",
        mdp=hashed_password,
        role="Administrateur",
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def regular_user(db_session, bcrypt_instance):
    """Create a regular user for testing.

    Args:
        db_session: Database session fixture
        bcrypt_instance: Bcrypt fixture for password hashing

    Returns:
        User: Regular user instance
    """
    hashed_password = bcrypt_instance.generate_password_hash("UserPass123!").decode(
        "utf-8"
    )
    user = User(
        nom="User",
        prenom="Test",
        email="user@test.com",
        mdp=hashed_password,
        role="Utilisateur",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_client_record(db_session):
    """Create a test client record.

    Args:
        db_session: Database session fixture

    Returns:
        Clients: Client instance
    """
    client_record = Clients(
        nom="Dupont",
        prenom="Jean",
        rue="123 Rue de Test",
        ville="Paris",
        code_postal="75001",
        telephone="0123456789",
        email="jean.dupont@test.com",
        caduque=False,
    )
    db_session.add(client_record)
    db_session.commit()
    return client_record


@pytest.fixture
def taux_tva_20(db_session):
    """Get or create 20% VAT rate.

    Args:
        db_session: Database session fixture

    Returns:
        TauxTVA: 20% VAT rate instance
    """
    tva = TauxTVA.query.filter_by(taux=0.20).first()
    if not tva:
        tva = TauxTVA(taux=0.20)
        db_session.add(tva)
        db_session.commit()
    return tva


@pytest.fixture
def taux_tva_10(db_session):
    """Get or create 10% VAT rate.

    Args:
        db_session: Database session fixture

    Returns:
        TauxTVA: 10% VAT rate instance
    """
    tva = TauxTVA.query.filter_by(taux=0.10).first()
    if not tva:
        tva = TauxTVA(taux=0.10)
        db_session.add(tva)
        db_session.commit()
    return tva


@pytest.fixture
def test_article(db_session, taux_tva_20):
    """Create a test article.

    Args:
        db_session: Database session fixture
        taux_tva_20: 20% VAT rate fixture

    Returns:
        Articles: Article instance
    """
    article = Articles(
        nom="Caméra Test",
        reference="CAM-001",
        prix_achat_HT=100.0,
        prix_vente_HT=150.0,
        taux_tva_id=taux_tva_20.id,
    )
    db_session.add(article)
    db_session.commit()
    return article


@pytest.fixture
def test_article_2(db_session, taux_tva_10):
    """Create a second test article with different VAT rate.

    Args:
        db_session: Database session fixture
        taux_tva_10: 10% VAT rate fixture

    Returns:
        Articles: Article instance
    """
    article = Articles(
        nom="Installation",
        reference="INST-001",
        prix_achat_HT=50.0,
        prix_vente_HT=75.0,
        taux_tva_id=taux_tva_10.id,
    )
    db_session.add(article)
    db_session.commit()
    return article


@pytest.fixture
def test_parameters(db_session):
    """Get or create test parameters.

    Args:
        db_session: Database session fixture

    Returns:
        Parameters: Parameters instance
    """
    params = Parameters.query.first()
    if not params:
        params = Parameters(
            margin_rate=1.5,
            margin_rate_location=1.8,
            location_time=36,
            location_subscription_cost=50.0,
            location_interests_cost=100.0,
            name="Test Company",
            address="123 Test Street",
            phone="0123456789",
            email="contact@test.com",
            IBAN="FR1234567890",
            TVA="FR12345678901",
            SIRET="12345678901234",
            APRM="ABC123",
            general_conditions_sales="<p>Terms and conditions</p>",
        )
        db_session.add(params)
        db_session.commit()
    return params


@pytest.fixture
def test_devis(db_session, test_client_record, test_article, taux_tva_20):
    """Create a test devis with one article.

    Args:
        db_session: Database session fixture
        test_client_record: Client fixture
        test_article: Article fixture
        taux_tva_20: VAT rate fixture

    Returns:
        Devis: Devis instance with calculated totals
    """
    # Calculate expected totals based on article
    # Article: prix_vente_HT=150.0, quantity=2
    unit_price = 150.0
    qty = 2
    taux_rate = 0.20  # 20% VAT

    line_ht = round(unit_price * qty, 2)  # 300.0
    line_tva = round(line_ht * taux_rate, 2)  # 60.0
    line_ttc = round(line_ht + line_tva, 2)  # 360.0

    devis = Devis(
        client_id=test_client_record.id,
        titre="Test Devis",
        description="Test description",
        date=datetime.now(),
        statut="Brouillon",
        remise=0.0,
        is_location=False,
        selected_scenario=None,
        montant_HT=line_ht,  # Initialize with calculated value
        montant_TVA=line_tva,  # Initialize with calculated value
        montant_TTC=line_ttc,  # Initialize with calculated value
    )
    db_session.add(devis)
    db_session.flush()

    # Add article
    devis_article = DevisArticles(
        devis_id=devis.id,
        article_id=test_article.id,
        quantite=qty,
        taux_tva_id=taux_tva_20.id,
        commentaire="Test comment",
        montant_HT=line_ht,
        montant_TVA=line_tva,
        montant_TTC=line_ttc,
    )
    db_session.add(devis_article)
    db_session.commit()
    return devis


@pytest.fixture
def signed_devis(db_session, test_devis):
    """Create a signed devis with snapshot.

    Args:
        db_session: Database session fixture
        test_devis: Devis fixture

    Returns:
        Devis: Signed devis with snapshot data
    """
    test_devis.statut = "Signé"
    test_devis.signed_at = datetime.now()

    # Create snapshot
    snapshot_data = {
        "articles": [],
        "totals": {
            "montant_HT": float(test_devis.montant_HT),
            "montant_TVA": float(test_devis.montant_TVA),
            "montant_TTC": float(test_devis.montant_TTC),
        },
        "parameters": {"margin_rate": 1.5, "location_costs": {}},
    }

    for article in test_devis.articles:
        snapshot_data["articles"].append(
            {
                "nom": article.article.nom,
                "reference": article.article.reference,
                "quantite": article.quantite,
                "prix_unitaire_ht": float(article.article.prix_vente_HT),
                "taux_tva": float(article.taux_tva.taux),
                "montant_HT": float(article.montant_HT),
                "montant_TVA": float(article.montant_TVA),
                "montant_TTC": float(article.montant_TTC),
            }
        )

    test_devis.signed_data = snapshot_data
    db_session.commit()
    return test_devis


@pytest.fixture
def auth_headers(client, regular_user):
    """Login and return headers with CSRF token for authenticated requests.

    Args:
        client: Flask test client
        regular_user: User fixture

    Returns:
        dict: Headers with CSRF token
    """
    # Login
    response = client.post(
        "/api/user/login", json={"email": "user@test.com", "password": "UserPass123!"}
    )

    # Extract CSRF token from cookie
    csrf_token = None
    for cookie in response.headers.getlist("Set-Cookie"):
        if "XSRF-TOKEN" in cookie:
            csrf_token = cookie.split("XSRF-TOKEN=")[1].split(";")[0]
            break

    return {"X-CSRF-Token": csrf_token, "Content-Type": "application/json"}


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Login as admin and return headers with CSRF token.

    Args:
        client: Flask test client
        admin_user: Admin user fixture

    Returns:
        dict: Headers with CSRF token
    """
    # Login
    response = client.post(
        "/api/user/login", json={"email": "admin@test.com", "password": "AdminPass123!"}
    )

    # Extract CSRF token from cookie
    csrf_token = None
    for cookie in response.headers.getlist("Set-Cookie"):
        if "XSRF-TOKEN" in cookie:
            csrf_token = cookie.split("XSRF-TOKEN=")[1].split(";")[0]
            break

    return {"X-CSRF-Token": csrf_token, "Content-Type": "application/json"}


def _init_test_defaults():
    """Initialize default test data (VAT rates, parameters)."""
    # Create default VAT rates if they don't exist
    if not TauxTVA.query.filter_by(taux=0.20).first():
        db.session.add(TauxTVA(taux=0.20))
    if not TauxTVA.query.filter_by(taux=0.10).first():
        db.session.add(TauxTVA(taux=0.10))

    # Create default parameters if they don't exist
    if not Parameters.query.first():
        params = Parameters(
            margin_rate=1.5,
            margin_rate_location=1.8,
            location_time=36,
            location_subscription_cost=50.0,
            location_interests_cost=100.0,
        )
        db.session.add(params)

    db.session.commit()
