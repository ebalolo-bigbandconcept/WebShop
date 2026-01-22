"""Unit tests for validation functions in utils.py.

Tests cover:
- Email validation
- Password strength validation
- User field validation
- Client field validation
- Article field validation
- Number coercion functions
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils import (
    is_valid_email,
    is_strong_password,
    validate_user_fields,
    validate_client_fields,
    validate_article_fields,
    _coerce_float,
    _coerce_int
)


class TestEmailValidation:
    """Test email format validation."""
    
    def test_valid_email_formats(self):
        """Test: accepts valid email formats"""
        valid_emails = [
            'user@example.com',
            'test.user@example.com',
            'user+tag@example.co.uk',
            'user123@test-domain.com',
            'a@b.co',
        ]
        
        for email in valid_emails:
            assert is_valid_email(email), f"Should accept: {email}"
    
    def test_invalid_email_formats(self):
        """Test: rejects invalid email formats"""
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
            'user @example.com',
            'user@example',
            '',
        ]
        
        for email in invalid_emails:
            assert not is_valid_email(email), f"Should reject: {email}"
    
    def test_email_with_special_chars(self):
        """Test: handles special characters correctly"""
        assert is_valid_email('user+tag@example.com')
        assert is_valid_email('first.last@example.com')
        assert is_valid_email('user_name@example.com')
    
    def test_email_case_insensitive(self):
        """Test: email validation is case-insensitive"""
        assert is_valid_email('User@Example.COM')
        assert is_valid_email('TEST@EXAMPLE.COM')


class TestPasswordValidation:
    """Test password strength validation."""
    
    def test_strong_password_validation(self):
        """Test: accepts passwords meeting all requirements"""
        strong_passwords = [
            'Password1!',
            'Test@123Pass',
            'Str0ng#Pass',
            'MyP@ssw0rd',
            'Abc123!@#',
        ]
        
        for password in strong_passwords:
            assert is_strong_password(password), f"Should accept: {password}"
    
    def test_weak_password_too_short(self):
        """Test: rejects passwords < 8 characters"""
        weak_passwords = [
            'Pass1!',
            'Ab1!',
            'Test@1',
        ]
        
        for password in weak_passwords:
            assert not is_strong_password(password), f"Should reject (too short): {password}"
    
    def test_weak_password_missing_uppercase(self):
        """Test: rejects passwords without uppercase letters"""
        assert not is_strong_password('password1!')
        assert not is_strong_password('test@123pass')
    
    def test_weak_password_missing_lowercase(self):
        """Test: rejects passwords without lowercase letters"""
        assert not is_strong_password('PASSWORD1!')
        assert not is_strong_password('TEST@123PASS')
    
    def test_weak_password_missing_digit(self):
        """Test: rejects passwords without digits"""
        assert not is_strong_password('Password!')
        assert not is_strong_password('TestPass@')
    
    def test_weak_password_missing_special(self):
        """Test: rejects passwords without special characters"""
        assert not is_strong_password('Password1')
        assert not is_strong_password('TestPass123')
    
    def test_password_with_various_special_chars(self):
        """Test: accepts various special characters"""
        passwords_with_special = [
            'Pass@word1',
            'Pass#word1',
            'Pass$word1',
            'Pass%word1',
            'Pass&word1',
            'Pass*word1',
        ]
        
        for password in passwords_with_special:
            assert is_strong_password(password), f"Should accept: {password}"


class TestUserFieldValidation:
    """Test user field validation."""
    
    def test_valid_user_fields(self):
        """Test: accepts valid user fields"""
        result = validate_user_fields(
            email='user@example.com',
            nom='Dupont',
            prenom='Jean',
            mdp='Password1!',
            role='Utilisateur'
        )
        assert result is None
    
    def test_invalid_email_format(self):
        """Test: rejects invalid email format"""
        result = validate_user_fields(
            email='notanemail',
            nom='Dupont',
            prenom='Jean',
            mdp='Password1!',
            role='Utilisateur'
        )
        assert result is not None
        assert 'email' in result.lower()
    
    def test_email_too_long(self):
        """Test: rejects email > 345 characters"""
        long_email = 'a' * 340 + '@test.com'  # 349 chars
        result = validate_user_fields(
            email=long_email,
            nom='Dupont',
            prenom='Jean',
            mdp='Password1!',
            role='Utilisateur'
        )
        assert result is not None
    
    def test_nom_too_short(self):
        """Test: rejects nom < 1 character"""
        result = validate_user_fields(
            email='user@example.com',
            nom='',
            prenom='Jean',
            mdp='Password1!',
            role='Utilisateur'
        )
        assert result is not None
        assert 'nom' in result.lower()
    
    def test_nom_too_long(self):
        """Test: rejects nom > 50 characters"""
        result = validate_user_fields(
            email='user@example.com',
            nom='a' * 51,
            prenom='Jean',
            mdp='Password1!',
            role='Utilisateur'
        )
        assert result is not None
    
    def test_prenom_too_short(self):
        """Test: rejects prenom < 1 character"""
        result = validate_user_fields(
            email='user@example.com',
            nom='Dupont',
            prenom='',
            mdp='Password1!',
            role='Utilisateur'
        )
        assert result is not None
        assert 'prénom' in result.lower()
    
    def test_prenom_too_long(self):
        """Test: rejects prenom > 50 characters"""
        result = validate_user_fields(
            email='user@example.com',
            nom='Dupont',
            prenom='a' * 51,
            mdp='Password1!',
            role='Utilisateur'
        )
        assert result is not None
    
    def test_invalid_role(self):
        """Test: rejects invalid role"""
        result = validate_user_fields(
            email='user@example.com',
            nom='Dupont',
            prenom='Jean',
            mdp='Password1!',
            role='InvalidRole'
        )
        assert result is not None
        assert 'rôle' in result.lower()
    
    def test_weak_password(self):
        """Test: rejects weak password"""
        result = validate_user_fields(
            email='user@example.com',
            nom='Dupont',
            prenom='Jean',
            mdp='weak',
            role='Utilisateur'
        )
        assert result is not None
        assert 'mot de passe' in result.lower()
    
    def test_password_optional(self):
        """Test: password can be None (for updates without password change)"""
        result = validate_user_fields(
            email='user@example.com',
            nom='Dupont',
            prenom='Jean',
            mdp=None,
            role='Utilisateur'
        )
        assert result is None
    
    def test_valid_admin_role(self):
        """Test: accepts Administrateur role"""
        result = validate_user_fields(
            email='admin@example.com',
            nom='Admin',
            prenom='User',
            mdp='Password1!',
            role='Administrateur'
        )
        assert result is None


class TestClientFieldValidation:
    """Test client field validation."""
    
    def test_valid_client_fields(self):
        """Test: accepts valid client fields"""
        result = validate_client_fields(
            nom='Dupont',
            prenom='Jean',
            rue='123 Rue de Test',
            ville='Paris',
            code_postal='75001',
            telephone='0123456789',
            email='client@example.com'
        )
        assert result is None
    
    def test_invalid_email(self):
        """Test: rejects invalid email"""
        result = validate_client_fields(
            nom='Dupont',
            prenom='Jean',
            rue='123 Rue de Test',
            ville='Paris',
            code_postal='75001',
            telephone='0123456789',
            email='notanemail'
        )
        assert result is not None
        assert 'email' in result.lower()
    
    def test_nom_boundaries(self):
        """Test: validates nom length boundaries"""
        # Too short
        result = validate_client_fields(
            nom='',
            prenom='Jean',
            rue='123 Rue de Test',
            ville='Paris',
            code_postal='75001',
            telephone='0123456789',
            email='client@example.com'
        )
        assert result is not None
        
        # Too long
        result = validate_client_fields(
            nom='a' * 101,
            prenom='Jean',
            rue='123 Rue de Test',
            ville='Paris',
            code_postal='75001',
            telephone='0123456789',
            email='client@example.com'
        )
        assert result is not None
        
        # Just right
        result = validate_client_fields(
            nom='a' * 100,
            prenom='Jean',
            rue='123 Rue de Test',
            ville='Paris',
            code_postal='75001',
            telephone='0123456789',
            email='client@example.com'
        )
        assert result is None
    
    def test_rue_validation(self):
        """Test: validates rue (street) field"""
        result = validate_client_fields(
            nom='Dupont',
            prenom='Jean',
            rue='',
            ville='Paris',
            code_postal='75001',
            telephone='0123456789',
            email='client@example.com'
        )
        assert result is not None
        assert 'rue' in result.lower()
    
    def test_ville_validation(self):
        """Test: validates ville (city) field"""
        result = validate_client_fields(
            nom='Dupont',
            prenom='Jean',
            rue='123 Rue de Test',
            ville='',
            code_postal='75001',
            telephone='0123456789',
            email='client@example.com'
        )
        assert result is not None
        assert 'ville' in result.lower()


class TestArticleFieldValidation:
    """Test article field validation."""
    
    def test_valid_article_fields(self, db_session, taux_tva_20):
        """Test: accepts valid article fields"""
        result = validate_article_fields(
            nom='Caméra Test',
            reference='CAM-001',
            prix_achat_HT=100.0,
            prix_vente_HT=150.0,
            taux_tva_id=taux_tva_20.id
        )
        assert result is None
    
    def test_nom_too_short(self, db_session, taux_tva_20):
        """Test: rejects nom < 1 character"""
        result = validate_article_fields(
            nom='',
            reference='CAM-001',
            prix_achat_HT=100.0,
            prix_vente_HT=150.0,
            taux_tva_id=taux_tva_20.id
        )
        assert result is not None
    
    def test_nom_too_long(self, db_session, taux_tva_20):
        """Test: rejects nom > 200 characters"""
        result = validate_article_fields(
            nom='a' * 201,
            reference='CAM-001',
            prix_achat_HT=100.0,
            prix_vente_HT=150.0,
            taux_tva_id=taux_tva_20.id
        )
        assert result is not None
    
    def test_negative_prix_achat(self, db_session, taux_tva_20):
        """Test: rejects negative prix_achat_HT"""
        result = validate_article_fields(
            nom='Caméra Test',
            reference='CAM-001',
            prix_achat_HT=-100.0,
            prix_vente_HT=150.0,
            taux_tva_id=taux_tva_20.id
        )
        assert result is not None
        assert 'achat' in result.lower()
    
    def test_negative_prix_vente(self, db_session, taux_tva_20):
        """Test: rejects negative prix_vente_HT"""
        result = validate_article_fields(
            nom='Caméra Test',
            reference='CAM-001',
            prix_achat_HT=100.0,
            prix_vente_HT=-150.0,
            taux_tva_id=taux_tva_20.id
        )
        assert result is not None
        assert 'vente' in result.lower()
    
    def test_invalid_tva_id(self, db_session):
        """Test: rejects non-existent taux_tva_id"""
        result = validate_article_fields(
            nom='Caméra Test',
            reference='CAM-001',
            prix_achat_HT=100.0,
            prix_vente_HT=150.0,
            taux_tva_id=99999  # Non-existent
        )
        assert result is not None
        assert 'tva' in result.lower()
    
    def test_zero_prices_allowed(self, db_session, taux_tva_20):
        """Test: allows zero prices (edge case)"""
        result = validate_article_fields(
            nom='Free Item',
            reference='FREE-001',
            prix_achat_HT=0.0,
            prix_vente_HT=0.0,
            taux_tva_id=taux_tva_20.id
        )
        assert result is None


class TestNumberCoercion:
    """Test number coercion utility functions."""
    
    def test_coerce_float_valid_string(self):
        """Test: converts valid string to float"""
        assert _coerce_float('123.45') == 123.45
        assert _coerce_float('100') == 100.0
        assert _coerce_float('0.5') == 0.5
    
    def test_coerce_float_valid_number(self):
        """Test: handles numeric input"""
        assert _coerce_float(123.45) == 123.45
        assert _coerce_float(100) == 100.0
    
    def test_coerce_float_none_returns_default(self):
        """Test: None returns default value"""
        assert _coerce_float(None) == 0.0
        assert _coerce_float(None, default=10.0) == 10.0
    
    def test_coerce_float_empty_string_returns_default(self):
        """Test: empty string returns default value"""
        assert _coerce_float('') == 0.0
        assert _coerce_float('', default=5.0) == 5.0
    
    def test_coerce_float_invalid_raises_error(self):
        """Test: invalid input raises ValueError"""
        with pytest.raises(ValueError):
            _coerce_float('not a number')
        
        with pytest.raises(ValueError):
            _coerce_float('12.34.56')
    
    def test_coerce_int_valid_string(self):
        """Test: converts valid string to int"""
        assert _coerce_int('123') == 123
        assert _coerce_int('0') == 0
        assert _coerce_int('-5') == -5
    
    def test_coerce_int_valid_number(self):
        """Test: handles numeric input"""
        assert _coerce_int(123) == 123
        assert _coerce_int(100.0) == 100
    
    def test_coerce_int_none_returns_default(self):
        """Test: None returns default value"""
        assert _coerce_int(None) == 0
        assert _coerce_int(None, default=10) == 10
    
    def test_coerce_int_empty_string_returns_default(self):
        """Test: empty string returns default value"""
        assert _coerce_int('') == 0
        assert _coerce_int('', default=5) == 5
    
    def test_coerce_int_invalid_raises_error(self):
        """Test: invalid input raises ValueError"""
        with pytest.raises(ValueError):
            _coerce_int('not a number')
        
        with pytest.raises(ValueError):
            _coerce_int('12.34')  # Not an integer
    
    def test_coerce_int_rounds_float(self):
        """Test: float input is converted to int (truncated)"""
        assert _coerce_int(123.7) == 123
        assert _coerce_int(99.1) == 99
