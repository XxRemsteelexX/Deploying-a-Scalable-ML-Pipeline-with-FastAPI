#!/bin/bash

# Google Cloud Deployment Script for Census ML API
# Prerequisites:
# - gcloud CLI configured
# - Docker installed
# - Project created and billing enabled

set -e

# Configuration
PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="census-ml-api"
IMAGE_NAME="census-ml-api"
CLOUD_RUN_CPU="1"
CLOUD_RUN_MEMORY="2Gi"
MIN_INSTANCES="0"
MAX_INSTANCES="10"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check gcloud authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        log_error "gcloud not authenticated. Run: gcloud auth login"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Set project and enable APIs
setup_project() {
    log_info "Setting up GCP project..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        containerregistry.googleapis.com
    
    log_info "Project setup completed"
}

# Build and push image to Container Registry
build_and_push() {
    log_info "Building and pushing Docker image..."
    
    # Build image using Cloud Build
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME .
    
    log_info "Image built and pushed successfully"
}

# Deploy to Cloud Run
deploy_to_cloud_run() {
    log_info "Deploying to Cloud Run..."
    
    gcloud run deploy $SERVICE_NAME \
        --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --cpu $CLOUD_RUN_CPU \
        --memory $CLOUD_RUN_MEMORY \
        --min-instances $MIN_INSTANCES \
        --max-instances $MAX_INSTANCES \
        --port 8000 \
        --set-env-vars LOG_LEVEL=INFO,MODEL_PATH=/app/model,API_VERSION=v1 \
        --timeout 300
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
    
    log_info "Service deployed successfully"
    log_info "Service URL: $SERVICE_URL"
}

# Setup monitoring and alerting
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create uptime check
    cat > uptime-check.json << EOF
{
  "displayName": "$SERVICE_NAME Uptime Check",
  "httpCheck": {
    "path": "/v1/health",
    "port": 443,
    "useSsl": true
  },
  "monitoredResource": {
    "type": "uptime_url",
    "labels": {
      "project_id": "$PROJECT_ID",
      "host": "$SERVICE_URL"
    }
  },
  "period": "60s",
  "timeout": "10s"
}
EOF
    
    # Create the uptime check (requires monitoring API to be enabled)
    gcloud alpha monitoring uptime create --config-from-file uptime-check.json || log_warn "Could not create uptime check"
    
    # Clean up
    rm -f uptime-check.json
    
    log_info "Monitoring setup completed"
}

# Create traffic split for canary deployment
setup_traffic() {
    log_info "Setting up traffic management..."
    
    # Initially send 100% traffic to new revision
    gcloud run services update-traffic $SERVICE_NAME \
        --to-latest \
        --platform managed \
        --region $REGION
    
    log_info "Traffic management configured"
}

# Main deployment flow
main() {
    log_info "Starting GCP deployment..."
    
    # Prompt for project ID if not set
    if [ "$PROJECT_ID" = "your-project-id" ]; then
        read -p "Enter your GCP Project ID: " PROJECT_ID
        if [ -z "$PROJECT_ID" ]; then
            log_error "Project ID cannot be empty"
            exit 1
        fi
    fi
    
    check_prerequisites
    setup_project
    build_and_push
    deploy_to_cloud_run
    setup_monitoring
    setup_traffic
    
    log_info "Deployment completed successfully!"
    log_info "Test your API:"
    log_info "curl $SERVICE_URL/v1/health"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "traffic")
        if [ -z "$2" ] || [ -z "$3" ]; then
            log_error "Usage: $0 traffic <revision-name> <traffic-percentage>"
            exit 1
        fi
        gcloud run services update-traffic $SERVICE_NAME \
            --to-revisions=$2=$3 \
            --platform managed \
            --region $REGION
        ;;
    "logs")
        gcloud logs tail --follow --resource="resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME"
        ;;
    "rollback")
        log_info "Rolling back to previous revision..."
        gcloud run services update-traffic $SERVICE_NAME \
            --to-revisions=PREVIOUS=100 \
            --platform managed \
            --region $REGION
        ;;
    *)
        echo "Usage: $0 [deploy|traffic|logs|rollback]"
        exit 1
        ;;
esac
