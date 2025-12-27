# KnowledgeFlow 快速启动指南

## 🚀 最简单的启动方式

### 1. 设置环境变量

```bash
# 在终端中设置（临时有效）
export OPENAI_API_KEY='your-api-key-here'
```

或者编辑 `.env` 文件（确保没有中文注释）：
```bash
OPENAI_API_KEY=your-api-key-here
```

### 2. 一键启动（推荐）

```bash
./start_all.sh
```

这将自动启动：
- 网络服务器（localhost:8700）
- 6个 Agent（RSS Reader, Web Scraper, Summarizer, Tagger, Outline Generator, Writer）

### 3. 手动启动（7个终端）

**终端 1: 网络服务器（必须先启动）**
```bash
./start_network.sh
# 或直接运行：conda run -n openagents openagents network start network.yaml
```

等待看到 `Network server started` 后，再启动其他 Agent：

**终端 2: RSS Reader**
```bash
conda run -n openagents python agents/rss_reader.py
```

**终端 3: Web Scraper**
```bash
conda run -n openagents python agents/web_scraper.py
```

**终端 4: Summarizer**
```bash
conda run -n openagents python agents/summarizer.py
```

**终端 5: Tagger**
```bash
conda run -n openagents python agents/tagger.py
```

**终端 6: Outline Generator**
```bash
conda run -n openagents python agents/outline_generator.py
```

**终端 7: Writer**
```bash
conda run -n openagents python agents/writer.py
```

## 📊 验证 Agent 运行

每个 Agent 启动后应该看到类似输出：
```
INFO - 🤖 XXX Agent 启动中...
INFO - ✅ XXX Agent 初始化完成
```

## 🧪 测试功能

### 测试 RSS 采集
等待30分钟自动采集，或查看日志：
```bash
tail -f logs/test_run.log
```

### 测试手动URL提交
在 `scraper-requests` 频道发送：
```
请抓取：https://news.ycombinator.com/
```

### 测试文章创作
在 `creation` 频道发送：
```
写一篇关于AI的文章
```

等待大纲生成后，选择方案：
```
选择方案 1
```

## 🔍 查看结果

```bash
# 查看数据库
sqlite3 data/knowledge-flow/content.db "SELECT title, category, status FROM content_items LIMIT 5;"

# 查看大纲
sqlite3 data/knowledge-flow/content.db "SELECT topic, created_at FROM outlines;"

# 查看草稿
sqlite3 data/knowledge-flow/content.db "SELECT title, word_count FROM drafts;"
```

## ❌ 故障排除

### 问题1：Agent 无法连接到网络服务器
**错误信息**：`Failed to connect to server at localhost:8700`

**解决方法**：
```bash
# 1. 先启动网络服务器
./start_network.sh
# 或
openagents serve network.yaml

# 2. 等待服务器启动（看到 "Network server started"）
# 3. 然后再启动 Agent
```

### 问题2：Python 模块导入错误
```bash
conda activate openagents
pip install -r requirements.txt
```

### 问题3：API Key 错误
确保设置正确：
```bash
echo $OPENAI_API_KEY
# 应该显示你的 API Key
```

### 问题4：Agent 启动失败
检查依赖：
```bash
conda run -n openagents pip install -r requirements.txt
```

### 问题5：数据库错误
重建数据库：
```bash
rm -rf data/knowledge-flow/
mkdir -p data/knowledge-flow/
```

## 💡 提示

1. 建议使用 tmux 或多个终端窗口
2. 每个 Agent 独立运行，可以单独重启
3. 日志文件在 `logs/` 目录
4. 数据库文件在 `data/knowledge-flow/content.db`