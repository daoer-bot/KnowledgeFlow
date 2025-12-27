#!/bin/bash
# KnowledgeFlow 一键启动脚本
# 先启动网络服务器，再启动所有 Agent

echo "🚀 KnowledgeFlow 一键启动"
echo "======================================"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 将项目目录添加到 PYTHONPATH（用于加载自定义 mods）
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# 加载 .env 文件
if [ -f .env ]; then
    echo "📄 加载 .env 文件..."
    while IFS='=' read -r key value; do
        # 跳过注释和空行
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        # 移除引号
        value="${value%\"}"
        value="${value#\"}"
        # 导出变量
        export "$key=$value"
    done < .env
fi

# 检查 OpenAgents 是否安装
if ! command -v openagents &> /dev/null; then
    echo "❌ OpenAgents CLI 未安装"
    echo "请安装: pip install openagents-sdk"
    exit 1
fi

# 检查环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  未设置 OPENAI_API_KEY"
    echo "请设置: export OPENAI_API_KEY='your-api-key'"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 创建日志和数据目录
mkdir -p logs/agents
mkdir -p data/knowledge-flow

# 使用 tmux 或 screen 启动多个会话
if command -v tmux &> /dev/null; then
    echo "使用 tmux 启动网络服务器和所有 Agent..."
    
    # 创建新会话
    tmux new-session -d -s knowledgeflow
    
    # Network Server (窗口 0)
    tmux rename-window -t knowledgeflow:0 'Network-Server'
    tmux send-keys -t knowledgeflow:0 "export PYTHONPATH='${SCRIPT_DIR}:\$PYTHONPATH' && conda run -n openagents openagents network start network.yaml" C-m
    
    echo "⏳ 等待网络服务器启动..."
    sleep 5
    
    # RSS Reader
    tmux new-window -t knowledgeflow:1 -n 'RSS-Reader'
    tmux send-keys -t knowledgeflow:1 'conda run -n openagents python agents/rss_reader.py' C-m
    
    # Web Scraper
    tmux new-window -t knowledgeflow:2 -n 'Web-Scraper'
    tmux send-keys -t knowledgeflow:2 'conda run -n openagents python agents/web_scraper.py' C-m
    
    # Summarizer
    tmux new-window -t knowledgeflow:3 -n 'Summarizer'
    tmux send-keys -t knowledgeflow:3 'conda run -n openagents python agents/summarizer.py' C-m
    
    # Tagger
    tmux new-window -t knowledgeflow:4 -n 'Tagger'
    tmux send-keys -t knowledgeflow:4 'conda run -n openagents python agents/tagger.py' C-m
    
    # Creation Coordinator (新增)
    tmux new-window -t knowledgeflow:5 -n 'Coordinator'
    tmux send-keys -t knowledgeflow:5 'conda run -n openagents python agents/creation_coordinator.py' C-m
    
    # Outline Generator
    tmux new-window -t knowledgeflow:6 -n 'Outline-Gen'
    tmux send-keys -t knowledgeflow:6 'conda run -n openagents python agents/outline_generator.py' C-m
    
    # Writer
    tmux new-window -t knowledgeflow:7 -n 'Writer'
    tmux send-keys -t knowledgeflow:7 'conda run -n openagents python agents/writer.py' C-m
    
    # Sensitive Word Reviewer (敏感词审查)
    tmux new-window -t knowledgeflow:8 -n 'Critic-Sensitive'
    tmux send-keys -t knowledgeflow:8 'conda run -n openagents python agents/critic_technical.py' C-m

    # AI Flavor Reviewer (AI味审查)
    tmux new-window -t knowledgeflow:9 -n 'Critic-AIFlavor'
    tmux send-keys -t knowledgeflow:9 'conda run -n openagents python agents/critic_business.py' C-m

    # Public Opinion Reviewer (舆情审查)
    tmux new-window -t knowledgeflow:10 -n 'Critic-Opinion'
    tmux send-keys -t knowledgeflow:10 'conda run -n openagents python agents/critic_user.py' C-m
    
    echo ""
    echo "✨ 网络服务器和所有 Agent 已启动！"
    echo ""
    echo "🌐 网络服务器: http://localhost:8700"
    echo "📊 OpenAgents Studio: http://localhost:8700/studio"
    echo ""
    echo "查看运行状态: tmux attach -t knowledgeflow"
    echo "切换窗口: Ctrl+B 然后按数字键 0-10"
    echo "  - 窗口 0: 网络服务器"
    echo "  - 窗口 1: RSS Reader"
    echo "  - 窗口 2: Web Scraper"
    echo "  - 窗口 3: Summarizer"
    echo "  - 窗口 4: Tagger"
    echo "  - 窗口 5: Creation Coordinator"
    echo "  - 窗口 6: Outline Generator"
    echo "  - 窗口 7: Writer"
    echo "  - 窗口 8: Sensitive Word Reviewer 🚫 (敏感词审查)"
    echo "  - 窗口 9: AI Flavor Reviewer 🤖 (AI味审查)"
    echo "  - 窗口 10: Public Opinion Reviewer 🔥 (舆情审查)"
    echo "分离会话: Ctrl+B 然后按 D"
    echo "停止所有: tmux kill-session -t knowledgeflow"
    echo ""
    
elif command -v screen &> /dev/null; then
    echo "使用 screen 启动网络服务器和所有 Agent..."
    
    # 启动网络服务器
    screen -dmS network-server bash -c "export PYTHONPATH='${SCRIPT_DIR}:\$PYTHONPATH' && conda run -n openagents openagents network start network.yaml"
    
    echo "⏳ 等待网络服务器启动..."
    sleep 5
    
    # 启动 Agents
    screen -dmS rss-reader bash -c 'conda run -n openagents python agents/rss_reader.py'
    screen -dmS web-scraper bash -c 'conda run -n openagents python agents/web_scraper.py'
    screen -dmS summarizer bash -c 'conda run -n openagents python agents/summarizer.py'
    screen -dmS tagger bash -c 'conda run -n openagents python agents/tagger.py'
    screen -dmS coordinator bash -c 'conda run -n openagents python agents/creation_coordinator.py'
    screen -dmS outline-gen bash -c 'conda run -n openagents python agents/outline_generator.py'
    screen -dmS writer bash -c 'conda run -n openagents python agents/writer.py'
    screen -dmS critic-sensitive bash -c 'conda run -n openagents python agents/critic_technical.py'
    screen -dmS critic-aiflavor bash -c 'conda run -n openagents python agents/critic_business.py'
    screen -dmS critic-opinion bash -c 'conda run -n openagents python agents/critic_user.py'
    
    echo ""
    echo "✨ 网络服务器和所有 Agent 已启动！"
    echo ""
    echo "🌐 网络服务器: http://localhost:8700"
    echo "📊 OpenAgents Studio: http://localhost:8700/studio"
    echo ""
    echo "查看 Agent 列表: screen -ls"
    echo "连接到 Agent: screen -r <name>"
    echo "分离会话: Ctrl+A 然后按 D"
    echo ""
    
else
    echo "❌ 未安装 tmux 或 screen"
    echo ""
    echo "请手动启动网络服务器和 Agent："
    echo ""
    echo "# 终端 1: 网络服务器 (必须先启动)"
    echo "conda run -n openagents openagents network start network.yaml"
    echo ""
    echo "# 终端 2: RSS Reader"
    echo "conda run -n openagents python agents/rss_reader.py"
    echo ""
    echo "# 终端 3: Web Scraper"
    echo "conda run -n openagents python agents/web_scraper.py"
    echo ""
    echo "# 终端 4: Summarizer"
    echo "conda run -n openagents python agents/summarizer.py"
    echo ""
    echo "# 终端 5: Tagger"
    echo "conda run -n openagents python agents/tagger.py"
    echo ""
    echo "# 终端 6: Creation Coordinator (新增)"
    echo "conda run -n openagents python agents/creation_coordinator.py"
    echo ""
    echo "# 终端 7: Outline Generator"
    echo "conda run -n openagents python agents/outline_generator.py"
    echo ""
    echo "# 终端 8: Writer"
    echo "conda run -n openagents python agents/writer.py"
    echo ""
    echo "# 终端 9: Sensitive Word Reviewer 🚫 (敏感词审查)"
    echo "conda run -n openagents python agents/critic_technical.py"
    echo ""
    echo "# 终端 10: AI Flavor Reviewer 🤖 (AI味审查)"
    echo "conda run -n openagents python agents/critic_business.py"
    echo ""
    echo "# 终端 11: Public Opinion Reviewer 🔥 (舆情审查)"
    echo "conda run -n openagents python agents/critic_user.py"
    echo ""
fi

echo "======================================"
echo "📊 监控提示："
echo "  - 查看日志: tail -f logs/agents/*.log"
echo "  - 查看数据库: sqlite3 knowledge.db 'SELECT * FROM content_items;'"
echo "======================================"