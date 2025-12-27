#!/bin/bash
# 简化的测试启动脚本 - 诊断 agents 无输出问题

echo "========================================"
echo "  🧪 简化测试启动"
echo "========================================"
echo ""

# 加载环境变量
if [ -f .env ]; then
    echo "📝 加载 .env 文件..."
    set -a
    source .env
    set +a
else
    echo "⚠️  未找到 .env 文件"
fi

# 检查环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 未设置 OPENAI_API_KEY"
    echo "请在 .env 文件中设置或运行: export OPENAI_API_KEY='your-key'"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 步骤 1: 在前台启动网络服务器（便于查看输出）
echo "========================================"
echo "步骤 1: 启动网络服务器"
echo "========================================"
echo ""
echo "💡 提示: 网络服务器将在前台运行"
echo "💡 成功启动后，按 Ctrl+C 停止，然后我们测试 agent"
echo ""

conda run -n openagents openagents network start network.yaml

echo ""
echo "========================================"
echo "网络服务器已停止"
echo "========================================"