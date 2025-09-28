"""
Integration tests for Census ML API

Run with: pytest tests/test_api_integration.py -v
"""

import pytest
import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30


class TestAPIIntegration:
    """Integration tests for the Census ML API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        # Wait for API to be ready
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(f"{API_BASE_URL}/", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    pytest.skip("API is not available")
                time.sleep(2)
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = requests.get(f"{API_BASE_URL}/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{API_BASE_URL}/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "model_loaded" in data
        assert "version" in data
        assert data["status"] in ["healthy", "unhealthy"]
        assert data["model_loaded"] is True
    
    def test_metrics_endpoint(self):
        """Test the metrics endpoint"""
        response = requests.get(f"{API_BASE_URL}/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "model_performance" in data
        assert "request_count" in data
        assert "prediction_distribution" in data
        assert "uptime_seconds" in data
        
        # Check model performance structure
        perf = data["model_performance"]
        assert "precision" in perf
        assert "recall" in perf
        assert "f1_score" in perf
    
    def test_model_info_endpoint(self):
        """Test the model info endpoint"""
        response = requests.get(f"{API_BASE_URL}/v1/model/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "model_type" in data
        assert "features" in data
        assert "target_classes" in data
        assert "model_version" in data
        assert data["model_type"] == "RandomForestClassifier"
        assert len(data["features"]) == 14
        assert set(data["target_classes"]) == {">50K", "<=50K"}
    
    def test_prediction_endpoint_valid_data(self):
        """Test prediction endpoint with valid data"""
        test_data = {
            "age": 37,
            "workclass": "Private",
            "fnlgt": 178356,
            "education": "HS-grad",
            "education-num": 10,
            "marital-status": "Married-civ-spouse",
            "occupation": "Prof-specialty",
            "relationship": "Husband",
            "race": "White",
            "sex": "Male",
            "capital-gain": 0,
            "capital-loss": 0,
            "hours-per-week": 40,
            "native-country": "United-States"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/v1/predict",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert "model_version" in data
        assert "timestamp" in data
        assert data["prediction"] in [">50K", "<=50K"]
        assert 0.0 <= data["confidence"] <= 1.0
    
    def test_prediction_endpoint_missing_fields(self):
        """Test prediction endpoint with missing required fields"""
        incomplete_data = {
            "age": 37,
            "workclass": "Private"
            # Missing other required fields
        }
        
        response = requests.post(
            f"{API_BASE_URL}/v1/predict",
            json=incomplete_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_prediction_endpoint_invalid_data_types(self):
        """Test prediction endpoint with invalid data types"""
        invalid_data = {
            "age": "not_a_number",  # Should be int
            "workclass": "Private",
            "fnlgt": 178356,
            "education": "HS-grad",
            "education-num": 10,
            "marital-status": "Married-civ-spouse",
            "occupation": "Prof-specialty",
            "relationship": "Husband",
            "race": "White",
            "sex": "Male",
            "capital-gain": 0,
            "capital-loss": 0,
            "hours-per-week": 40,
            "native-country": "United-States"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/v1/predict",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_legacy_endpoint_compatibility(self):
        """Test the legacy endpoint for backward compatibility"""
        test_data = {
            "age": 37,
            "workclass": "Private",
            "fnlgt": 178356,
            "education": "HS-grad",
            "education-num": 10,
            "marital-status": "Married-civ-spouse",
            "occupation": "Prof-specialty",
            "relationship": "Husband",
            "race": "White",
            "sex": "Male",
            "capital-gain": 0,
            "capital-loss": 0,
            "hours-per-week": 40,
            "native-country": "United-States"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/data/",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert data["result"] in [">50K", "<=50K"]
    
    def test_prediction_consistency(self):
        """Test that the same input produces consistent results"""
        test_data = {
            "age": 45,
            "workclass": "Private",
            "fnlgt": 200000,
            "education": "Masters",
            "education-num": 14,
            "marital-status": "Married-civ-spouse",
            "occupation": "Exec-managerial",
            "relationship": "Husband",
            "race": "White",
            "sex": "Male",
            "capital-gain": 15024,
            "capital-loss": 0,
            "hours-per-week": 50,
            "native-country": "United-States"
        }
        
        # Make multiple predictions with the same data
        responses = []
        for _ in range(5):
            response = requests.post(
                f"{API_BASE_URL}/v1/predict",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 200
            responses.append(response.json())
        
        # Check that predictions are consistent
        first_prediction = responses[0]["prediction"]
        first_confidence = responses[0]["confidence"]
        
        for response in responses[1:]:
            assert response["prediction"] == first_prediction
            assert response["confidence"] == first_confidence
    
    def test_api_performance(self):
        """Test API response time performance"""
        test_data = {
            "age": 30,
            "workclass": "Private",
            "fnlgt": 150000,
            "education": "Bachelors",
            "education-num": 13,
            "marital-status": "Never-married",
            "occupation": "Tech-support",
            "relationship": "Not-in-family",
            "race": "Asian-Pac-Islander",
            "sex": "Female",
            "capital-gain": 0,
            "capital-loss": 0,
            "hours-per-week": 40,
            "native-country": "United-States"
        }
        
        # Measure response time
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/v1/predict",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import queue
        
        test_data = {
            "age": 35,
            "workclass": "Private",
            "fnlgt": 120000,
            "education": "Some-college",
            "education-num": 10,
            "marital-status": "Divorced",
            "occupation": "Sales",
            "relationship": "Not-in-family",
            "race": "White",
            "sex": "Female",
            "capital-gain": 0,
            "capital-loss": 0,
            "hours-per-week": 35,
            "native-country": "United-States"
        }
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = requests.post(
                    f"{API_BASE_URL}/v1/predict",
                    json=test_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                results.put(("success", response.status_code))
            except Exception as e:
                results.put(("error", str(e)))
        
        # Create multiple threads to make concurrent requests
        threads = []
        num_threads = 10
        
        for _ in range(num_threads):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=15)
        
        # Check results
        success_count = 0
        while not results.empty():
            result_type, result_value = results.get()
            if result_type == "success":
                assert result_value == 200
                success_count += 1
        
        # At least 80% of requests should succeed
        assert success_count >= num_threads * 0.8
    
    def test_error_handling(self):
        """Test various error conditions"""
        # Test with malformed JSON
        response = requests.post(
            f"{API_BASE_URL}/v1/predict",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test with empty payload
        response = requests.post(
            f"{API_BASE_URL}/v1/predict",
            json={},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test non-existent endpoint
        response = requests.get(f"{API_BASE_URL}/v1/nonexistent")
        assert response.status_code == 404
    
    def test_openapi_documentation(self):
        """Test that OpenAPI documentation is available"""
        response = requests.get(f"{API_BASE_URL}/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert "paths" in openapi_spec
        
        # Check that our endpoints are documented
        paths = openapi_spec["paths"]
        assert "/" in paths
        assert "/v1/health" in paths
        assert "/v1/predict" in paths
        assert "/v1/metrics" in paths


class TestLoadScenarios:
    """Load testing scenarios using requests"""
    
    def test_burst_load(self):
        """Test handling burst load"""
        test_data = {
            "age": 40,
            "workclass": "Private",
            "fnlgt": 180000,
            "education": "Bachelors",
            "education-num": 13,
            "marital-status": "Married-civ-spouse",
            "occupation": "Prof-specialty",
            "relationship": "Husband",
            "race": "White",
            "sex": "Male",
            "capital-gain": 5000,
            "capital-loss": 0,
            "hours-per-week": 45,
            "native-country": "United-States"
        }
        
        # Send 20 requests in rapid succession
        start_time = time.time()
        successful_requests = 0
        
        for _ in range(20):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/v1/predict",
                    json=test_data,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                if response.status_code == 200:
                    successful_requests += 1
            except requests.exceptions.RequestException:
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle at least 15 out of 20 requests successfully
        assert successful_requests >= 15
        # Should complete within reasonable time
        assert total_time < 30


if __name__ == "__main__":
    # Run specific tests
    pytest.main([__file__, "-v"])
