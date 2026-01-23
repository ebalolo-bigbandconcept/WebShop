"""Integration tests for Clients API endpoints."""


class TestClientsRetrieval:
    """Tests for clients retrieval endpoints."""
    
    def test_get_all_clients(self, client, test_client_record):
        """Test getting all clients."""
        response = client.get('/api/clients/all')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'pagination' in data
        assert data['pagination']['total_items'] >= 1
    
    def test_get_all_clients_pagination(self, client, test_client_record):
        """Test pagination parameters."""
        response = client.get('/api/clients/all?page=1&per_page=10')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['pagination']['per_page'] == 10
        assert data['pagination']['current_page'] == 1
    
    def test_get_client_info(self, client, test_client_record):
        """Test getting specific client info."""
        response = client.get(f'/api/clients/info/{test_client_record.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == test_client_record.id
        assert data['email'] == test_client_record.email


class TestClientsCreate:
    """Tests for creating clients."""
    
    def test_create_client_success(self, client):
        """Test successful client creation."""
        response = client.post(
            '/api/clients/create',
            json={
                'nom': 'TestNom',
                'prenom': 'TestPrenom',
                'rue': '123 Test Street',
                'ville': 'TestVille',
                'code_postal': '75001',
                'telephone': '0123456789',
                'email': 'newclient@test.com',
                'force': False
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data
    
    def test_create_client_duplicate_email_without_force(self, client, test_client_record):
        """Test creating client with duplicate email without force flag."""
        response = client.post(
            '/api/clients/create',
            json={
                'nom': 'DuplicateTest',
                'prenom': 'Test',
                'rue': '123 Test',
                'ville': 'Paris',
                'code_postal': '75001',
                'telephone': '0123456789',
                'email': test_client_record.email,
                'force': False
            }
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'error' in data
    
    def test_create_client_duplicate_email_with_force(self, client, test_client_record):
        """Test creating client with duplicate email with force flag."""
        response = client.post(
            '/api/clients/create',
            json={
                'nom': 'ForceTest',
                'prenom': 'Test',
                'rue': '123 Test',
                'ville': 'Paris',
                'code_postal': '75001',
                'telephone': '0123456789',
                'email': test_client_record.email,
                'force': True
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data
    
    def test_create_client_invalid_email(self, client):
        """Test creating client with invalid email."""
        response = client.post(
            '/api/clients/create',
            json={
                'nom': 'TestNom',
                'prenom': 'TestPrenom',
                'rue': '123 Test',
                'ville': 'Paris',
                'code_postal': '75001',
                'telephone': '0123456789',
                'email': 'invalid-email',
                'force': False
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestClientsUpdate:
    """Tests for updating clients."""
    
    def test_update_client_success(self, client, test_client_record):
        """Test successful client update."""
        response = client.post(
            f'/api/clients/update/{test_client_record.id}',
            json={
                'nom': 'UpdatedNom',
                'prenom': 'UpdatedPrenom',
                'rue': '456 Updated Street',
                'ville': 'UpdatedVille',
                'code_postal': '75002',
                'telephone': '0987654321',
                'email': 'updated@test.com',
                'caduque': False,
                'force': False
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Client mis à jour avec succès'
    
    def test_update_nonexistent_client(self, client):
        """Test updating non-existent client."""
        response = client.post(
            '/api/clients/update/99999',
            json={
                'nom': 'Test',
                'prenom': 'Test',
                'rue': '123 Test',
                'ville': 'Paris',
                'code_postal': '75001',
                'telephone': '0123456789',
                'email': 'test@test.com',
                'caduque': False,
                'force': False
            }
        )
        
        assert response.status_code == 404
    
    def test_update_client_duplicate_email_without_force(self, client, db_session):
        """Test updating client with duplicate email without force."""
        from models import Clients
        
        # Create two clients
        client1 = Clients(
            nom='Client1', prenom='Test1', rue='Rue1', ville='Ville1',
            code_postal='75001', telephone='0111111111',
            email='client1@test.com', caduque=False
        )
        client2 = Clients(
            nom='Client2', prenom='Test2', rue='Rue2', ville='Ville2',
            code_postal='75002', telephone='0222222222',
            email='client2@test.com', caduque=False
        )
        db_session.add(client1)
        db_session.add(client2)
        db_session.commit()
        
        # Try to update client2 with client1's email
        response = client.post(
            f'/api/clients/update/{client2.id}',
            json={
                'nom': 'Client2',
                'prenom': 'Test2',
                'rue': 'Rue2',
                'ville': 'Ville2',
                'code_postal': '75002',
                'telephone': '0222222222',
                'email': 'client1@test.com',
                'caduque': False,
                'force': False
            }
        )
        
        assert response.status_code == 409
