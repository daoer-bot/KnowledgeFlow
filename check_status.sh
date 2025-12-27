#!/bin/bash
# KnowledgeFlow 系统状态检查脚本

echo "=========================================="
echo "  KnowledgeFlow 系统状态检查"
echo "=========================================="
echo ""

# 检查网络服务器
echo "📡 网络服务器状态："
NETWORK_PID=$(ps aux | grep "openagents network start" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$NETWORK_PID" ]; then
    echo "  ✅ 运行中 (PID: $NETWORK_PID)"
    echo "  🌐 端口: 8700 (HTTP), 8600 (gRPC)"
else
    echo "  ❌ 未运行"
fi
echo ""

# 检查各个 Agent
echo "🤖 Agent 运行状态："

AGENTS=("rss_reader" "web_scraper" "summarizer" "tagger" "outline_generator" "writer")
AGENT_NAMES=("RSS采集器" "网页抓取器" "摘要生成器" "标签分类器" "大纲生成器" "文章写作器")

for i in "${!AGENTS[@]}"; do
    AGENT="${AGENTS[$i]}"
    NAME="${AGENT_NAMES[$i]}"
    
    PID=$(ps aux | grep "python agents/${AGENT}.py" | grep -v grep | awk '{print $2}' | head -1)
    
    if [ -n "$PID" ]; then
        echo "  ✅ $NAME (${AGENT}) - PID: $PID"
    else
        echo "  ❌ $NAME (${AGENT}) - 未运行"
    fi
done

echo ""
echo "=========================================="

# 统计运行中的服务数量
RUNNING_COUNT=$(ps aux | grep -E "(rss_reader|web_scraper|summarizer|tagger|outline_generator|writer)" | grep "python agents" | grep -v grep | wc -l | tr -d ' ')

echo "📊 总计: $RUNNING_COUNT/6 个 Agent 运行中"

if [ "$RUNNING_COUNT" -eq 6 ] && [ -n "$NETWORK_PID" ]; then
    echo "🎉 系统运行正常！"
else
    echo "⚠️  部分服务未运行，请检查日志"
fi

echo "=========================================="