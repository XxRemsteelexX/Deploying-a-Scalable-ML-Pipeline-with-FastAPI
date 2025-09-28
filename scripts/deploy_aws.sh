#!/bin/bash

# AWS Deployment Script for Census ML API
# Prerequisites:
# - AWS CLI configured
# - Docker installed
# - ECR repository created

set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="census-ml-api"
ECS_CLUSTER="ml-cluster"
ECS_SERVICE="census-ml-service"
TASK_DEFINITION="census-ml-task"

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
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Get AWS Account ID
get_account_id() {
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    log_info "Using AWS Account: $ACCOUNT_ID"
}

# Build and push Docker image to ECR
build_and_push() {
    log_info "Building and pushing Docker image..."
    
    # Get ECR login token
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    
    # Build image
    docker build -t $ECR_REPOSITORY .
    
    # Tag image
    docker tag $ECR_REPOSITORY:latest $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
    
    # Push image
    docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
    
    log_info "Image pushed successfully"
}

# Create or update ECS task definition
update_task_definition() {
    log_info "Updating ECS task definition..."
    
    # Create task definition JSON
    cat > task-definition.json << EOF
{
    "family": "$TASK_DEFINITION",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "executionRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "$ECR_REPOSITORY",
            "image": "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest",
            "portMappings": [
                {
                    "containerPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "essential": true,
            "environment": [
                {
                    "name": "LOG_LEVEL",
                    "value": "INFO"
                },
                {
                    "name": "MODEL_PATH",
                    "value": "/app/model"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/$TASK_DEFINITION",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8000/v1/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
EOF
    
    # Register task definition
    aws ecs register-task-definition --cli-input-json file://task-definition.json
    
    # Clean up
    rm task-definition.json
    
    log_info "Task definition updated"
}

# Update ECS service
update_service() {
    log_info "Updating ECS service..."
    
    # Update service to use new task definition
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --task-definition $TASK_DEFINITION
    
    # Wait for service to stabilize
    log_info "Waiting for service to stabilize..."
    aws ecs wait services-stable \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE
    
    log_info "Service updated successfully"
}

# Main deployment flow
main() {
    log_info "Starting AWS deployment..."
    
    check_prerequisites
    get_account_id
    build_and_push
    update_task_definition
    update_service
    
    log_info "Deployment completed successfully!"
    log_info "Service URL: Check your ALB DNS name"
}

# Run main function
main
