#!/bin/bash

# Start the full InteractiveKG system (backend + frontend).
# Prerequisites: Neo4j running (docker-compose up -d neo4j), Python 3.10/3.11
# with backend dependencies installed, and Node.js.

echo "🚀 Starting the Knowledge Graph Management System + Chatbot"
echo "=================================="

echo "📋 Checking the environment..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

echo "🔍 Checking the Neo4j database..."
if ! curl -s http://localhost:7474 > /dev/null; then
    echo "⚠️  Neo4j does not appear to be running on port 7474"
    echo "   Start it with: docker-compose up -d neo4j"
fi

# LLM configuration
export LLM_PROVIDER=${LLM_PROVIDER:-openai_gpt4o_mini}
export LLM_MODEL_NAME=${LLM_MODEL_NAME:-gpt-4o-mini-2024-07-18}

if [ -z "$LLM_API_KEY" ]; then
    echo "⚠️  The LLM_API_KEY environment variable is not set"
    echo "   Set your OpenAI API key with: export LLM_API_KEY=your-api-key"
fi

echo "✅ Environment check finished"
echo ""

# Start the backend. Prefer a project virtual environment when one exists.
echo "🔧 Starting the backend..."
cd backend
if [ -f .venv310/bin/activate ]; then
    source .venv310/bin/activate
elif [ -f .venv311/bin/activate ]; then
    source .venv311/bin/activate
fi
python3 -m pip install -r requirements.txt > /dev/null 2>&1
python3 main.py &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

echo "⏳ Waiting for the backend to come up..."
sleep 5

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "🎨 Starting the frontend..."
cd ../frontend
npm install > /dev/null 2>&1
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "🎉 System is up!"
echo "=================================="
echo "📱 Frontend:  http://localhost:3000"
echo "🔧 Backend:   http://localhost:8000"
echo "📊 API docs:  http://localhost:8000/docs"
echo ""
echo "🤖 The chatbot assistant is integrated into the left sidebar"
echo "📋 Study flow:"
echo "   1. Open the frontend page"
echo "   2. Find the user-test assistant in the left sidebar"
echo "   3. Follow the chatbot guidance through the Act I and Act II tasks"
echo ""
echo "⚠️  Press Ctrl+C to stop all services"

cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

wait
