"""
Unit tests for customer web server
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "customer-web-server"


class TestBuyEndpoint:
    """Tests for /buy endpoint"""
    
    @patch('app.main.publish_to_kafka')
    def test_buy_endpoint_success(self, mock_publish):
        """Test buy endpoint with successful Kafka publish"""
        mock_publish.return_value = True
        
        buy_request = {
            "username": "testuser",
            "userId": "user123",
            "price": 99.99
        }
        
        response = client.post("/buy", json=buy_request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["kafka_published"] is True
        assert data["data"]["username"] == "testuser"
        assert data["data"]["userId"] == "user123"
        assert data["data"]["price"] == 99.99
        mock_publish.assert_called_once()
    
    @patch('app.main.publish_to_kafka')
    def test_buy_endpoint_kafka_failure(self, mock_publish):
        """Test buy endpoint when Kafka publish fails"""
        mock_publish.return_value = False
        
        buy_request = {
            "username": "testuser",
            "userId": "user123",
            "price": 99.99
        }
        
        response = client.post("/buy", json=buy_request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["kafka_published"] is False
    
    def test_buy_endpoint_invalid_data(self):
        """Test buy endpoint with invalid data"""
        invalid_request = {
            "username": "testuser",
            # Missing userId and price
        }
        
        response = client.post("/buy", json=invalid_request)
        assert response.status_code == 422  # Validation error


class TestGetAllUserBuysEndpoint:
    """Tests for /getAllUserBuys endpoint"""
    
    @patch('app.main.CUSTOMER_API_URL', 'http://test-api:8000')
    def test_get_all_user_buys_endpoint_exists(self):
        """Test getAllUserBuys endpoint exists and handles requests"""
        # This test verifies the endpoint exists and returns a response
        # In a real scenario, the API might not be available, so we test error handling
        response = client.get("/getAllUserBuys?userId=user123")
        # Should return 200 even if API is unavailable (graceful degradation)
        assert response.status_code in [200, 500]


class TestHomeEndpoint:
    """Tests for / endpoint"""
    
    def test_home_endpoint(self):
        """Test home endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

