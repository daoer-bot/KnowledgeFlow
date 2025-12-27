#!/bin/bash
# 强制日志输出的启动脚本

echo "========================================"
echo "  🚀 启动 KnowledgeFlow（日志模式）"
echo "========================================"
echo ""

# 加载环境变量
if [ -f .env ]; then
    echo "📝 加载 .env 文件..."
    set -a
    source .env
    set +a
fi

# 检查环境
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 未设置 OPENAI_API_KEY"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 创建日志目录
mkdir -p logs/agents

# 清理旧日志
> logs/network_live.log

echo "🌐 启动网络服务器..."
echo "📝 日志文件: logs/network_live.log"
echo ""

# 启动网络服务器并实时输出日志
conda run -n openagents openagents network start network.yaml 2>&1 | tee logs/network_live.log &

NETWORK_PID=$!

echo "✅ 网络服务器已启动 (PID: $NETWORK_PID)"
echo ""
echo "========================================"
echo "📊 Studio UI: http://localhost:8700/studio"
echo "📝 实时日志: tail -f logs/network_live.log"
echo ""
echo "💡 提示："
echo "  - 在另一个终端运行 agents"
echo "  - 或访问 Studio UI 查看状态"
echo "  - 按 Ctrl+C 停止服务器"
echo "========================================"
echo ""

# 等待服务器启动
sleep 3

# 检查服务器是否成功启动
if curl -s http://localhost:8700/api/health > /dev/null 2>&1; then
    echo "✅ 网络服务器启动成功！"
    echo "🎉 可以启动 agents 了"
else
    echo "⚠️  正在启动中，请稍候..."
fi

echo ""

# 等待中断信号
wait $NETWORK_PID