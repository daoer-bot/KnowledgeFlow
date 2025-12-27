#!/bin/bash

# KnowledgeFlow 网络服务器启动脚本

echo "🚀 启动 KnowledgeFlow 网络服务器..."

# 加载环境变量
if [ -f .env ]; then
    echo "📝 加载环境变量..."
    while IFS='=' read -r key value; do
        # 跳过注释和空行
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        # 去除引号
        value="${value%\"}"
        value="${value#\"}"
        export "$key=$value"
    done < .env
fi

# 检查 network.yaml 是否存在
if [ ! -f "network.yaml" ]; then
    echo "❌ 错误: 找不到 network.yaml 配置文件"
    exit 1
fi

# 创建数据目录
mkdir -p data/knowledge-flow

# 启动网络服务器
echo "🌐 启动网络服务器 (http://localhost:8700)..."
echo "💡 提示: 使用 Ctrl+C 停止服务器"
echo ""

conda run -n openagents openagents network start network.yaml

# 如果服务器停止，显示消息
echo ""
echo "⏹️  网络服务器已停止"