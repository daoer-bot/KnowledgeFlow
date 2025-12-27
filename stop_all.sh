#!/bin/bash
# KnowledgeFlow 一键关闭脚本

echo "=========================================="
echo "  停止 KnowledgeFlow 所有服务"
echo "=========================================="
echo ""

# 停止所有 Agent
echo "🛑 正在停止 Agent..."

AGENTS=("rss_reader" "web_scraper" "summarizer" "tagger" "outline_generator" "writer" "creation_coordinator" "critic_technical" "critic_business" "critic_user")

for AGENT in "${AGENTS[@]}"; do
    PIDS=$(ps aux | grep "python agents/${AGENT}.py" | grep -v grep | awk '{print $2}')
    
    if [ -n "$PIDS" ]; then
        echo "  停止 ${AGENT}..."
        echo "$PIDS" | xargs kill -15 2>/dev/null
        sleep 1
    fi
done

echo ""

# 停止网络服务器
echo "🛑 正在停止网络服务器..."
NETWORK_PID=$(ps aux | grep "openagents network start" | grep -v grep | awk '{print $2}')

if [ -n "$NETWORK_PID" ]; then
    echo "  停止网络服务器 (PID: $NETWORK_PID)..."
    echo "$NETWORK_PID" | xargs kill -15 2>/dev/null
    sleep 2
fi

echo ""
echo "=========================================="
echo "✅ 所有服务已停止"
echo "=========================================="

# 验证是否还有残留进程
REMAINING=$(ps aux | grep -E "(openagents|agents/)" | grep python | grep -v grep | wc -l | tr -d ' ')

if [ "$REMAINING" -gt 0 ]; then
    echo ""
    echo "⚠️  发现 $REMAINING 个残留进程"
    echo "执行强制停止: kill -9"
    
    ps aux | grep -E "(openagents|agents/)" | grep python | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
    
    echo "✅ 强制停止完成"
fi