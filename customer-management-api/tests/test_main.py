"""
Unit tests for customer management API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint"""
    
    @patch('app.main.get_mongo_client')
    @patch('app.main.consumer_running', True)
    def test_health_endpoint_healthy(self, mock_mongo):
        """Test health endpoint when all services are healthy"""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = True
        mock_mongo.return_value = mock_client
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "customer-management-api"
        assert data["mongodb"] == "connected"
        assert data["kafka"] == "consuming"
    
    @patch('app.main.get_mongo_client')
    @patch('app.main.consumer_running', False)
    def test_health_endpoint_degraded(self, mock_mongo):
        """Test health endpoint when services are degraded"""
        mock_mongo.side_effect = Exception("Connection failed")
        
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert "error" in data["mongodb"]
        assert data["kafka"] == "not running"


class TestGetPurchasesEndpoint:
    """Tests for /api/purchases/{userId} endpoint"""
    
    @patch('app.main.get_collection')
    def test_get_purchases_success(self, mock_get_collection):
        """Test get purchases endpoint with successful query"""
        mock_collection = MagicMock()
        mock_purchase = {
            "_id": "507f1f77bcf86cd799439011",
            "userId": "user123",
            "username": "testuser",
            "price": 99.99,
            "timestamp": "2024-01-01T00:00:00Z",
            "createdAt": "2024-01-01T00:00:00Z"
        }
        mock_collection.find.return_value.sort.return_value = [mock_purchase]
        mock_get_collection.return_value = mock_collection
        
        response = client.get("/api/purchases/user123")
        assert response.status_code == 200
        data = response.json()
        assert "purchases" in data
        assert data["userId"] == "user123"
        assert len(data["purchases"]) == 1
        assert data["purchases"][0]["userId"] == "user123"
    
    @patch('app.main.get_collection')
    def test_get_purchases_empty(self, mock_get_collection):
        """Test get purchases endpoint with no purchases"""
        mock_collection = MagicMock()
        mock_collection.find.return_value.sort.return_value = []
        mock_get_collection.return_value = mock_collection
        
        response = client.get("/api/purchases/user123")
        assert response.status_code == 200
        data = response.json()
        assert data["purchases"] == []
        assert data["userId"] == "user123"
    
    @patch('app.main.get_collection')
    def test_get_purchases_error(self, mock_get_collection):
        """Test get purchases endpoint with database error"""
        mock_get_collection.side_effect = Exception("Database error")
        
        response = client.get("/api/purchases/user123")
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


class TestGetAllPurchasesEndpoint:
    """Tests for /api/purchases endpoint"""
    
    @patch('app.main.get_collection')
    def test_get_all_purchases_success(self, mock_get_collection):
        """Test get all purchases endpoint with successful query"""
        mock_collection = MagicMock()
        mock_purchase = {
            "_id": "507f1f77bcf86cd799439011",
            "userId": "user123",
            "username": "testuser",
            "price": 99.99,
            "timestamp": "2024-01-01T00:00:00Z",
            "createdAt": "2024-01-01T00:00:00Z"
        }
        mock_collection.find.return_value.sort.return_value.limit.return_value = [mock_purchase]
        mock_get_collection.return_value = mock_collection
        
        response = client.get("/api/purchases")
        assert response.status_code == 200
        data = response.json()
        assert "purchases" in data
        assert "count" in data
        assert data["count"] == 1
    
    @patch('app.main.get_collection')
    def test_get_all_purchases_with_limit(self, mock_get_collection):
        """Test get all purchases endpoint with limit parameter"""
        mock_collection = MagicMock()
        mock_collection.find.return_value.sort.return_value.limit.return_value = []
        mock_get_collection.return_value = mock_collection
        
        response = client.get("/api/purchases?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
    
    @patch('app.main.get_collection')
    def test_get_all_purchases_error(self, mock_get_collection):
        """Test get all purchases endpoint with database error"""
        mock_get_collection.side_effect = Exception("Database error")
        
        response = client.get("/api/purchases")
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()

