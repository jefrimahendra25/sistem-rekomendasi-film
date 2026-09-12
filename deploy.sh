#!/bin/bash

# FilmKu API Deployment Script
# This script helps deploy the application to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="filmku-api"
DOCKER_REGISTRY="your-registry.com"  # Change to your registry
VERSION=${1:-"latest"}

echo -e "${GREEN}🚀 Starting FilmKu API Deployment${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}📝 Please edit .env file with your configuration before continuing.${NC}"
    echo -e "${YELLOW}   Required variables: TMDB_API_KEY, SECRET_KEY${NC}"
    read -p "Press Enter after editing .env file..."
fi

# Validate required environment variables
source .env
if [ -z "$TMDB_API_KEY" ] || [ "$TMDB_API_KEY" = "your_tmdb_api_key_here" ]; then
    echo -e "${RED}❌ TMDB_API_KEY is not set in .env file${NC}"
    exit 1
fi

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your_super_secret_key_change_this_in_production" ]; then
    echo -e "${RED}❌ SECRET_KEY is not set in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables validated${NC}"

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p logs Data ssl

# Build Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t ${PROJECT_NAME}:${VERSION} .
docker tag ${PROJECT_NAME}:${VERSION} ${PROJECT_NAME}:latest

# Run database migrations (for production)
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
docker-compose -f docker-compose.yml up -d db redis
sleep 10

# Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
timeout 60 bash -c 'until docker-compose -f docker-compose.yml exec -T db pg_isready -U filmuser -d filmku; do sleep 2; done'

# Start the application
echo -e "${YELLOW}🚀 Starting application...${NC}"
docker-compose -f docker-compose.yml up -d

# Wait for application to be ready
echo -e "${YELLOW}⏳ Waiting for application to be ready...${NC}"
sleep 30

# Health check
echo -e "${YELLOW}🏥 Performing health check...${NC}"
if curl -f http://localhost:5002/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Application is healthy and running${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo -e "${YELLOW}📋 Checking logs...${NC}"
    docker-compose logs app
    exit 1
fi

# Show status
echo -e "${GREEN}📊 Deployment Status:${NC}"
docker-compose ps

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Application is available at: http://localhost:5002${NC}"
echo -e "${GREEN}📚 API Documentation: http://localhost:5002/docs/${NC}"
echo -e "${GREEN}🏥 Health Check: http://localhost:5002/health${NC}"

# Optional: Push to registry
if [ "$2" = "push" ]; then
    echo -e "${YELLOW}📤 Pushing to Docker registry...${NC}"
    docker tag ${PROJECT_NAME}:${VERSION} ${DOCKER_REGISTRY}/${PROJECT_NAME}:${VERSION}
    docker tag ${PROJECT_NAME}:latest ${DOCKER_REGISTRY}/${PROJECT_NAME}:latest
    docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}:${VERSION}
    docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}:latest
    echo -e "${GREEN}✅ Images pushed to registry${NC}"
fi

echo -e "${GREEN}🎯 Useful commands:${NC}"
echo -e "   View logs: docker-compose logs -f app"
echo -e "   Stop app: docker-compose down"
echo -e "   Restart app: docker-compose restart app"
echo -e "   Scale app: docker-compose up -d --scale app=3"
