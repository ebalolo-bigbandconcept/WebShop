"""Integration tests for Articles API endpoints."""


class TestArticlesRetrieval:
    """Tests for articles retrieval endpoints."""
    
    def test_get_all_articles_requires_auth(self, client):
        """Test that getting all articles requires authentication."""
        response = client.get('/api/articles/all')
        
        assert response.status_code == 401
    
    def test_get_all_articles_with_auth(self, client, auth_headers, test_article):
        """Test getting all articles with authentication."""
        response = client.get('/api/articles/all', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'pagination' in data
        assert data['pagination']['total_items'] >= 1
    
    def test_get_all_articles_pagination(self, client, auth_headers, test_article):
        """Test pagination parameters."""
        response = client.get(
            '/api/articles/all?page=1&per_page=10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['pagination']['per_page'] == 10
        assert data['pagination']['current_page'] == 1
    
    def test_get_article_info_requires_auth(self, client, test_article):
        """Test that getting article info requires authentication."""
        response = client.get(f'/api/articles/info/{test_article.id}')
        
        assert response.status_code == 401
    
    def test_get_article_info_with_auth(self, client, auth_headers, test_article):
        """Test getting specific article info with authentication."""
        response = client.get(
            f'/api/articles/info/{test_article.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == test_article.id
        assert data['nom'] == test_article.nom
    
    def test_get_nonexistent_article(self, client, auth_headers):
        """Test getting non-existent article."""
        response = client.get('/api/articles/info/99999', headers=auth_headers)
        
        assert response.status_code == 404


class TestArticlesCreate:
    """Tests for creating articles."""
    
    def test_create_article_requires_auth(self, client):
        """Test that creating an article requires authentication."""
        response = client.post(
            '/api/articles/create',
            json={
                'nom': 'Test Article',
                'reference': 'TEST-001',
                'prix_achat_HT': 100.0,
                'taux_tva': 20.0
            }
        )
        
        assert response.status_code == 401
    
    def test_create_article_success(self, client, auth_headers, taux_tva_20, test_parameters):
        """Test successful article creation."""
        response = client.post(
            '/api/articles/create',
            json={
                'nom': 'New Article',
                'reference': 'NEW-001',
                'prix_achat_HT': 100.0,
                'taux_tva': 20.0
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data
    
    def test_create_article_without_tva(self, client, auth_headers):
        """Test creating article without TVA."""
        response = client.post(
            '/api/articles/create',
            json={
                'nom': 'Article sans TVA',
                'reference': 'NO-TVA-001',
                'prix_achat_HT': 100.0,
                'taux_tva': None
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestArticlesUpdate:
    """Tests for updating articles."""
    
    def test_update_article_requires_auth(self, client, test_article):
        """Test that updating an article requires authentication."""
        response = client.post(
            f'/api/articles/update/{test_article.id}',
            json={
                'nom': 'Updated Article',
                'reference': 'UPD-001',
                'prix_achat_HT': 150.0,
                'taux_tva': 20.0
            }
        )
        
        assert response.status_code == 401
    
    def test_update_article_success(self, client, auth_headers, test_article, taux_tva_20, test_parameters):
        """Test successful article update."""
        response = client.post(
            f'/api/articles/update/{test_article.id}',
            json={
                'nom': 'Updated Article Name',
                'reference': 'UPD-REF',
                'prix_achat_HT': 200.0,
                'taux_tva': 20.0
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data
        assert data['id'] == test_article.id
    
    def test_update_nonexistent_article(self, client, auth_headers):
        """Test updating non-existent article."""
        response = client.post(
            '/api/articles/update/99999',
            json={
                'nom': 'Test',
                'reference': 'TEST',
                'prix_achat_HT': 100.0,
                'taux_tva': 20.0
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_update_article_without_tva(self, client, auth_headers, test_article):
        """Test updating article without TVA."""
        response = client.post(
            f'/api/articles/update/{test_article.id}',
            json={
                'nom': 'Article sans TVA',
                'reference': 'NO-TVA',
                'prix_achat_HT': 100.0,
                'taux_tva': None
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400


class TestArticlesDelete:
    """Tests for deleting articles."""
    
    def test_delete_article_requires_auth(self, client, test_article):
        """Test that deleting an article requires authentication."""
        response = client.delete(f'/api/articles/delete/{test_article.id}')
        
        assert response.status_code == 401
    
    def test_delete_article_success(self, client, auth_headers, db_session):
        """Test successful article deletion."""
        from models import Articles, TauxTVA
        
        # Create a TVA rate
        tva = TauxTVA.query.filter_by(taux=20.0).first()
        if not tva:
            tva = TauxTVA(taux=20.0)
            db_session.add(tva)
            db_session.commit()
        
        # Create an article to delete
        article = Articles(
            nom='Article to Delete',
            reference='DEL-001',
            prix_achat_HT=100.0,
            prix_vente_HT=120.0,
            taux_tva_id=tva.id
        )
        db_session.add(article)
        db_session.commit()
        article_id = article.id
        
        response = client.delete(
            f'/api/articles/delete/{article_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Article supprimé avec succès'
    
    def test_delete_nonexistent_article(self, client, auth_headers):
        """Test deleting non-existent article."""
        response = client.delete('/api/articles/delete/99999', headers=auth_headers)
        
        assert response.status_code == 404
