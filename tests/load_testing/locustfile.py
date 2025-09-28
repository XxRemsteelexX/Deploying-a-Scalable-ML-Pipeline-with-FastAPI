"""
Load testing script for Census ML API using Locust

Usage:
    locust -f tests/load_testing/locustfile.py --host=http://localhost:8000
    
Web UI: http://localhost:8089
"""

import json
import random
from locust import HttpUser, task, between

class CensusAPIUser(HttpUser):
    """
    Simulates a user interacting with the Census ML API
    """
    
    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        # Test initial connection
        response = self.client.get("/")
        if response.status_code != 200:
            print(f"Failed to connect to API: {response.status_code}")
    
    @task(5)
    def predict_income(self):
        """
        Main prediction task - weighted to run more frequently
        """
        # Generate realistic test data
        test_data = self.generate_test_data()
        
        with self.client.post(
            "/v1/predict",
            json=test_data,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "prediction" in result and "confidence" in result:
                    response.success()
                else:
                    response.failure("Invalid response format")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def check_health(self):
        """Health check task"""
        with self.client.get("/v1/health", catch_response=True) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "healthy":
                    response.success()
                else:
                    response.failure("API reports unhealthy")
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(1)
    def get_metrics(self):
        """Metrics endpoint task"""
        with self.client.get("/v1/metrics", catch_response=True) as response:
            if response.status_code == 200:
                result = response.json()
                if "model_performance" in result:
                    response.success()
                else:
                    response.failure("Invalid metrics response")
            else:
                response.failure(f"Metrics failed: {response.status_code}")
    
    @task(1)
    def get_model_info(self):
        """Model info endpoint task"""
        with self.client.get("/v1/model/info", catch_response=True) as response:
            if response.status_code == 200:
                result = response.json()
                if "model_type" in result:
                    response.success()
                else:
                    response.failure("Invalid model info response")
            else:
                response.failure(f"Model info failed: {response.status_code}")
    
    @task(1)
    def test_legacy_endpoint(self):
        """Test legacy endpoint for backward compatibility"""
        test_data = self.generate_test_data()
        
        with self.client.post(
            "/data/",
            json=test_data,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    response.success()
                else:
                    response.failure("Invalid legacy response format")
            else:
                response.failure(f"Legacy endpoint failed: {response.status_code}")
    
    def generate_test_data(self):
        """
        Generate realistic test data for predictions
        """
        
        # Realistic value distributions based on census data
        workclass_options = ["Private", "Self-emp-not-inc", "Self-emp-inc", "Federal-gov", "Local-gov", "State-gov"]
        education_options = ["Bachelors", "Some-college", "11th", "HS-grad", "Prof-school", "Assoc-acdm", "Assoc-voc", "9th", "7th-8th", "12th", "Masters", "1st-4th", "10th", "Doctorate", "5th-6th", "Preschool"]
        marital_status_options = ["Married-civ-spouse", "Divorced", "Never-married", "Separated", "Widowed", "Married-spouse-absent", "Married-AF-spouse"]
        occupation_options = ["Tech-support", "Craft-repair", "Other-service", "Sales", "Exec-managerial", "Prof-specialty", "Handlers-cleaners", "Machine-op-inspct", "Adm-clerical", "Farming-fishing", "Transport-moving", "Priv-house-serv", "Protective-serv", "Armed-Forces"]
        relationship_options = ["Wife", "Own-child", "Husband", "Not-in-family", "Other-relative", "Unmarried"]
        race_options = ["White", "Asian-Pac-Islander", "Amer-Indian-Eskimo", "Other", "Black"]
        sex_options = ["Female", "Male"]
        country_options = ["United-States", "Cambodia", "England", "Puerto-Rico", "Canada", "Germany", "Outlying-US(Guam-USVI-etc)", "India", "Japan", "Greece", "South", "China", "Cuba", "Iran", "Honduras", "Philippines", "Italy", "Poland", "Jamaica", "Vietnam", "Mexico", "Portugal", "Ireland", "France", "Dominican-Republic", "Laos", "Ecuador", "Taiwan", "Haiti", "Columbia", "Hungary", "Guatemala", "Nicaragua", "Scotland", "Thailand", "Yugoslavia", "El-Salvador", "Trinadad&Tobago", "Peru", "Hong", "Holand-Netherlands"]
        
        return {
            "age": random.randint(17, 90),
            "workclass": random.choice(workclass_options),
            "fnlgt": random.randint(12285, 1484705),
            "education": random.choice(education_options),
            "education-num": random.randint(1, 16),
            "marital-status": random.choice(marital_status_options),
            "occupation": random.choice(occupation_options),
            "relationship": random.choice(relationship_options),
            "race": random.choice(race_options),
            "sex": random.choice(sex_options),
            "capital-gain": random.randint(0, 99999) if random.random() < 0.1 else 0,
            "capital-loss": random.randint(0, 4356) if random.random() < 0.1 else 0,
            "hours-per-week": random.randint(1, 99),
            "native-country": random.choice(country_options)
        }


class StressTestUser(HttpUser):
    """
    Stress test user with aggressive load patterns
    """
    
    wait_time = between(0.1, 0.5)  # Shorter wait times for stress testing
    
    @task
    def rapid_predictions(self):
        """Rapid-fire predictions for stress testing"""
        test_data = {
            "age": 39,
            "workclass": "State-gov",
            "fnlgt": 77516,
            "education": "Bachelors",
            "education-num": 13,
            "marital-status": "Never-married",
            "occupation": "Adm-clerical",
            "relationship": "Not-in-family",
            "race": "White",
            "sex": "Male",
            "capital-gain": 2174,
            "capital-loss": 0,
            "hours-per-week": 40,
            "native-country": "United-States"
        }
        
        self.client.post("/v1/predict", json=test_data)


class HealthCheckUser(HttpUser):
    """
    User that only performs health checks - useful for monitoring
    """
    
    wait_time = between(5, 10)  # Check every 5-10 seconds
    
    @task
    def health_check(self):
        """Continuous health monitoring"""
        self.client.get("/v1/health")
        
    @task
    def metrics_check(self):
        """Periodic metrics collection"""
        self.client.get("/v1/metrics")


class ConcurrentUser(HttpUser):
    """
    User simulating concurrent access patterns
    """
    
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """Initialize user session"""
        self.test_cases = [
            {
                "name": "high_income_profile",
                "data": {
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
            },
            {
                "name": "low_income_profile",
                "data": {
                    "age": 23,
                    "workclass": "Private",
                    "fnlgt": 100000,
                    "education": "HS-grad",
                    "education-num": 9,
                    "marital-status": "Never-married",
                    "occupation": "Handlers-cleaners",
                    "relationship": "Own-child",
                    "race": "Black",
                    "sex": "Male",
                    "capital-gain": 0,
                    "capital-loss": 0,
                    "hours-per-week": 30,
                    "native-country": "United-States"
                }
            }
        ]
    
    @task
    def test_prediction_scenarios(self):
        """Test different prediction scenarios"""
        test_case = random.choice(self.test_cases)
        
        with self.client.post(
            "/v1/predict",
            json=test_case["data"],
            name=f"predict_{test_case['name']}"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                # Log interesting results for analysis
                if result.get("confidence", 0) < 0.6:
                    print(f"Low confidence prediction for {test_case['name']}: {result.get('confidence')}")
