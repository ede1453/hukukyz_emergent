#!/bin/bash

echo "🏛️ HukukYZ - Starting..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found. Creating from .env.example..."
    cp .env.example backend/.env
    echo ""
    echo "⚠️  Please edit backend/.env and add your OPENAI_API_KEY"
    echo "   Then run this script again."
    exit 1
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk-" backend/.env; then
    echo "⚠️  OPENAI_API_KEY not configured in backend/.env"
    echo "   Please add your OpenAI API key and run this script again."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p qdrant_storage mongo_data
echo "✅ Directories created"
echo ""

# Start services
echo "🚀 Starting Docker services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health checks
echo ""
echo "🔍 Checking service health..."

# Check Qdrant
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant is running"
else
    echo "⚠️  Qdrant is not responding"
fi

# Check Backend
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend is not responding"
fi

# Check Frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend is not responding (it may take a minute to start)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 HukukYZ is starting!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 Access points:"
echo "   Frontend:  http://localhost:3000"
echo "   API Docs:  http://localhost:8001/docs"
echo "   Qdrant:    http://localhost:6333/dashboard"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
