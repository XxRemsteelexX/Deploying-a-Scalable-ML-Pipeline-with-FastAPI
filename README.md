# Scalable ML Pipeline with FastAPI

A production-ready machine learning pipeline for income prediction using Census data, deployed as a scalable REST API with FastAPI. This project demonstrates end-to-end ML deployment practices including data processing, model training, API development, and comprehensive testing.

## Project Overview

This application predicts whether an individual's income exceeds $50K based on demographic and employment features from the 1994 US Census data. The system is designed for production deployment with proper API versioning, monitoring, and scalability considerations.

### Key Features

- **Production ML Pipeline**: Complete workflow from data processing to model deployment
- **RESTful API**: FastAPI-based service with automatic documentation
- **Comprehensive Testing**: Unit tests, integration tests, and CI/CD pipeline
- **Model Monitoring**: Performance tracking and bias analysis across demographic slices
- **Containerized Deployment**: Docker support for consistent environments
- **API Versioning**: Structured endpoints with version management
- **Health Monitoring**: Built-in health checks and metrics endpoints

## Architecture

```
├── data/              # Census dataset
├── ml/                # Core ML modules
│   ├── data.py       # Data processing utilities
│   └── model.py      # Model training and inference
├── model/            # Trained model artifacts
├── tests/            # Unit and integration tests
├── main.py           # FastAPI application
└── train_model.py    # Model training script
```

## Technology Stack

- **API Framework**: FastAPI with Pydantic data validation
- **ML Framework**: scikit-learn with RandomForest classifier
- **Data Processing**: Pandas and NumPy
- **Testing**: pytest with comprehensive coverage
- **CI/CD**: GitHub Actions
- **Containerization**: Docker and docker-compose
- **Monitoring**: Built-in health checks and performance metrics

## Quick Start

### Prerequisites

- Python 3.8+
- pip or conda package manager
- Docker (optional, for containerized deployment)

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/XxRemsteelexX/Deploying-a-Scalable-ML-Pipeline-with-FastAPI.git
   cd Deploying-a-Scalable-ML-Pipeline-with-FastAPI
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Using conda
   conda env create -f environment.yml
   conda activate census-ml
   
   # Or using pip
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Train the model** (if not using pre-trained):
   ```bash
   python train_model.py
   ```

4. **Start the API server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access the API**:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - OpenAPI spec: http://localhost:8000/openapi.json

### Docker Deployment

1. **Build the Docker image**:
   ```bash
   docker build -t census-ml-api .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 census-ml-api
   ```

3. **Using docker-compose** (recommended for development):
   ```bash
   docker-compose up --build
   ```

## API Documentation

### Endpoints

#### GET /
Welcome message and API information.

**Response**:
```json
{
  "message": "Welcome to the Census Income Prediction API",
  "version": "1.0.0",
  "docs_url": "/docs"
}
```

#### POST /v1/predict
Predict income category based on individual characteristics.

**Request Body**:
```json
{
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
```

**Response**:
```json
{
  "prediction": ">50K",
  "confidence": 0.87,
  "model_version": "v1.0.0"
}
```

#### GET /v1/health
Health check endpoint for monitoring.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "model_loaded": true,
  "version": "1.0.0"
}
```

#### GET /v1/metrics
Model performance metrics and statistics.

**Response**:
```json
{
  "model_performance": {
    "precision": 0.7369,
    "recall": 0.6294,
    "f1_score": 0.6789
  },
  "request_count": 1250,
  "last_updated": "2024-01-01T00:00:00Z"
}
```

## Model Information

### Performance Metrics
- **Precision**: 0.7369
- **Recall**: 0.6294
- **F1 Score**: 0.6789

### Model Features
The model uses the following demographic and employment features:
- Age, education level, and work hours
- Work class and occupation
- Marital status and relationship
- Race, sex, and native country
- Capital gains and losses

### Bias Analysis
Comprehensive slice-based performance analysis is available in `slice_output.txt`, showing model performance across different demographic groups to identify potential biases.

## Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=ml --cov-report=html
```

### Load Testing
```bash
# Install locust first: pip install locust
locust -f tests/load_test.py --host=http://localhost:8000
```

## Deployment

### Production Deployment

1. **Environment Variables**:
   ```bash
   export MODEL_PATH=/app/model
   export LOG_LEVEL=INFO
   export API_VERSION=v1
   ```

2. **Production Server**:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

### Cloud Deployment

#### AWS Deployment
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t census-ml-api .
docker tag census-ml-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/census-ml-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/census-ml-api:latest
```

#### Google Cloud Run
```bash
# Deploy to Cloud Run
gcloud run deploy census-ml-api --image gcr.io/PROJECT-ID/census-ml-api --platform managed --region us-central1 --allow-unauthenticated
```

## Monitoring and Observability

### Logging
The application uses structured logging with different levels:
- INFO: General application flow
- WARNING: Unusual but handled situations
- ERROR: Error conditions

### Metrics
Built-in metrics tracking:
- Request count and latency
- Model prediction distribution
- Error rates by endpoint

### Health Checks
Multiple health check endpoints for different purposes:
- `/health`: Basic application health
- `/v1/health`: Detailed health with model status
- `/v1/metrics`: Performance metrics

## Development

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## Acknowledgments

- UCI Machine Learning Repository for the Census dataset
- FastAPI community for excellent documentation and examples
- scikit-learn contributors for robust ML tools
