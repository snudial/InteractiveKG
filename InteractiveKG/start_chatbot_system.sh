#!/bin/bash

# 启动Chatbot系统的完整测试脚本

echo "🚀 启动知识图谱管理系统 + Chatbot"
echo "=================================="

# 检查环境
echo "📋 检查环境..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

# 检查Neo4j是否运行
echo "🔍 检查Neo4j数据库..."
if ! curl -s http://localhost:7474 > /dev/null; then
    echo "⚠️  Neo4j可能未运行，请确保Neo4j在端口7474上运行"
    echo "   可以使用: docker-compose up -d neo4j"
fi

# 设置环境变量
export LLM_PROVIDER=openai_gpt4o_mini
export LLM_MODEL_NAME=gpt-4o-mini-2024-07-18

if [ -z "$LLM_API_KEY" ]; then
    echo "⚠️  LLM_API_KEY 环境变量未设置"
    echo "   请设置您的OpenAI API密钥: export LLM_API_KEY=your-api-key"
fi

echo "✅ 环境检查完成"
echo ""

# 启动后端
echo "🔧 启动后端服务..."
cd backend
python3 -m pip install -r requirements.txt > /dev/null 2>&1
python3 main.py &
BACKEND_PID=$!
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 检查后端是否正常运行
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 启动前端
echo "🎨 启动前端服务..."
cd ../frontend
npm install > /dev/null 2>&1
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"

echo ""
echo "🎉 系统启动完成！"
echo "=================================="
echo "📱 前端地址: http://localhost:3000"
echo "🔧 后端地址: http://localhost:8000"
echo "📊 API文档: http://localhost:8000/docs"
echo ""
echo "🤖 Chatbot功能已集成到左侧边栏"
echo "📋 测试流程:"
echo "   1. 打开前端页面"
echo "   2. 在左侧找到 'User Test 引导助手'"
echo "   3. 按照chatbot指引完成Act I和Act II测试"
echo ""
echo "⚠️  按 Ctrl+C 停止所有服务"

# 清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ 所有服务已停止"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 保持脚本运行
wait
