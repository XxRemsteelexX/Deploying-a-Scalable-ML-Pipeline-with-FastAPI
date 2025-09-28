#!/bin/bash

# Local Production Setup Script for Census ML API
# This script sets up a local production-like environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    if ! command -v pip &> /dev/null; then
        log_error "pip is not installed"
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]]; then
        log_error "Python 3.8+ is required. Current version: $python_version"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Setup virtual environment
setup_venv() {
    log_step "Setting up virtual environment..."
    
    if [ -d "venv" ]; then
        log_warn "Virtual environment already exists. Removing..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_info "Virtual environment created"
}

# Install dependencies
install_dependencies() {
    log_step "Installing dependencies..."
    
    source venv/bin/activate
    
    # Install production dependencies
    pip install -r requirements.txt
    
    # Install additional production tools
    pip install gunicorn uvicorn[standard] pytest-cov black flake8 mypy
    
    log_info "Dependencies installed"
}

# Setup directories
setup_directories() {
    log_step "Setting up directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p model
    mkdir -p tests
    
    # Set appropriate permissions
    chmod 755 logs data model tests
    
    log_info "Directories created"
}

# Validate model files
validate_models() {
    log_step "Validating model files..."
    
    if [ ! -f "model/model.pkl" ] || [ ! -f "model/encoder.pkl" ]; then
        log_warn "Model files not found. Training model..."
        source venv/bin/activate
        python train_model.py
    fi
    
    log_info "Model files validated"
}

# Run tests
run_tests() {
    log_step "Running tests..."
    
    source venv/bin/activate
    
    # Run unit tests
    pytest test_ml.py -v
    
    # Run code quality checks
    log_info "Running code quality checks..."
    black --check . || log_warn "Code formatting issues found. Run: black ."
    flake8 . --exclude=venv,__pycache__ || log_warn "Linting issues found"
    
    log_info "Tests completed"
}

# Create systemd service (for Linux systems)
create_systemd_service() {
    if [[ "$OSTYPE" == "linux-gnu"* ]] && command -v systemctl &> /dev/null; then
        log_step "Creating systemd service..."
        
        cat > census-ml-api.service << EOF
[Unit]
Description=Census ML API
After=network.target

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        log_info "Systemd service file created: census-ml-api.service"
        log_info "To install: sudo mv census-ml-api.service /etc/systemd/system/"
        log_info "To enable: sudo systemctl enable census-ml-api.service"
        log_info "To start: sudo systemctl start census-ml-api.service"
    fi
}

# Create nginx configuration
create_nginx_config() {
    log_step "Creating Nginx configuration..."
    
    cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream census_ml_api {
        server 127.0.0.1:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            proxy_pass http://census_ml_api;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # Health check
            location /v1/health {
                proxy_pass http://census_ml_api;
                access_log off;
            }
        }
        
        # Serve static files if needed
        location /static/ {
            alias /path/to/static/files/;
            expires 30d;
        }
    }
}
EOF
    
    log_info "Nginx configuration created: nginx.conf"
}

# Create startup script
create_startup_script() {
    log_step "Creating startup script..."
    
    cat > start_production.sh << 'EOF'
#!/bin/bash

# Production startup script for Census ML API

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export LOG_LEVEL=INFO
export MODEL_PATH=./model
export API_VERSION=v1

# Start the application with gunicorn
exec gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    --pid gunicorn.pid \
    --daemon
EOF
    
    chmod +x start_production.sh
    
    # Create stop script
    cat > stop_production.sh << 'EOF'
#!/bin/bash

# Stop production server
if [ -f gunicorn.pid ]; then
    kill $(cat gunicorn.pid)
    rm gunicorn.pid
    echo "Server stopped"
else
    echo "Server is not running"
fi
EOF
    
    chmod +x stop_production.sh
    
    log_info "Startup scripts created: start_production.sh, stop_production.sh"
}

# Create monitoring script
create_monitoring_script() {
    log_step "Creating monitoring script..."
    
    cat > monitor.sh << 'EOF'
#!/bin/bash

# Simple monitoring script for Census ML API

API_URL="http://localhost:8000"
HEALTH_ENDPOINT="/v1/health"
LOG_FILE="logs/monitor.log"

check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$HEALTH_ENDPOINT")
    if [ "$response" = "200" ]; then
        echo "$(date): API is healthy" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): API is unhealthy (HTTP $response)" >> "$LOG_FILE"
        return 1
    fi
}

# Main monitoring loop
while true; do
    if ! check_health; then
        echo "API health check failed at $(date)"
        # Add alerting logic here (email, Slack, etc.)
    fi
    sleep 60
done
EOF
    
    chmod +x monitor.sh
    
    log_info "Monitoring script created: monitor.sh"
}

# Display final instructions
show_instructions() {
    log_step "Setup completed successfully!"
    
    echo ""
    echo "Next steps:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Start development server: uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    echo "3. Start production server: ./start_production.sh"
    echo "4. Stop production server: ./stop_production.sh"
    echo "5. Monitor API: ./monitor.sh"
    echo ""
    echo "Endpoints:"
    echo "- API: http://localhost:8000"
    echo "- Health: http://localhost:8000/v1/health"
    echo "- Docs: http://localhost:8000/docs"
    echo "- Metrics: http://localhost:8000/v1/metrics"
    echo ""
    echo "Files created:"
    echo "- census-ml-api.service (systemd service)"
    echo "- nginx.conf (nginx configuration)"
    echo "- start_production.sh (startup script)"
    echo "- stop_production.sh (stop script)"
    echo "- monitor.sh (monitoring script)"
}

# Main setup flow
main() {
    log_info "Starting local production setup..."
    
    check_prerequisites
    setup_venv
    install_dependencies
    setup_directories
    validate_models
    run_tests
    create_systemd_service
    create_nginx_config
    create_startup_script
    create_monitoring_script
    show_instructions
}

# Run main function
main
