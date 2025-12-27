# KnowledgeFlow - AI 知识流系统

> 基于 OpenAgents 框架的智能多 Agent 协作系统，实现**信息采集 → 智能处理 → AI 创作**的完整工作流

<div align="center">

[![OpenAgents](https://img.shields.io/badge/OpenAgents-0.6.13+-blue.svg)](https://github.com/OpenAgentsInc/openagents)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[快速开始](#-快速开始) • [Agent 介绍](#-agent-) • [工作流程](#-) • [使用指南](#-) • [故障排查](#-故障排查)

</div>

---

## 📖 目录

- [项目简介](#-项目简介)
- [快速开始](#-快速开始)
- [Agent 介绍](#-agent-介绍)
- [工作流程](#-完整工作流程)
- [使用指南](#-详细使用指南)
- [配置说明](#-配置说明)
- [故障排查](#-故障排查)

---

## 🎯 项目简介

**KnowledgeFlow** 是一个由 6 个专业 AI Agent 协作的智能系统，它们各司其职，通过事件和消息频道协同工作，自动完成从灵感捕手到 AI 创作的全流程。

### ✨ 核心特点

🤖 **6 个专业 Agent**：每个 Agent 专注一个领域，协作完成复杂任务  
🔄 **自动化工作流**：内容自动流转，无需人工干预  
💬 **频道消息系统**：所有处理过程实时可见  
📊 **OpenAgents Studio**：可视化监控和交互界面  
🗄️ **智能数据库**：结构化存储，支持全文检索  

### 🎯 适用场景

- **📰 技术新闻订阅**：自动采集、摘要、分类技术文章
- **✍️ AI 内容创作**：基于知识库生成文章大纲和完整内容
- **🗂️ 知识管理**：结构化存储和检索技术资料
- **🔍 信息研究**：快速提取关键信息和引用

---

## 🚀 快速开始

### 第一步：环境准备

```bash
# 1. 创建 Python 环境（推荐使用 conda）
conda create -n openagents python=3.11
conda activate openagents

# 2. 安装依赖
pip install -r requirements.txt
pip install openagents-sdk

# 3. 验证安装
openagents --version
```

### 第二步：配置 API Key

```bash
# 1. 复制配置文件
cp .env.example .env

# 2. 编辑 .env 文件，填入你的 OpenAI API Key
# OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 第三步：一键启动

```bash
# 使用 tmux 启动所有服务（推荐）
./start_all.sh

# 这将自动启动：
# ✅ 网络服务器（http://localhost:8700）
# ✅ 6 个 AI Agent（自动协作）
```

### 第四步：访问 Studio

打开浏览器访问：**http://localhost:8700**

你将看到 OpenAgents Studio 界面，可以：
- 📊 监控所有 Agent 的运行状态
- 💬 在频道中查看实时消息
- ✍️ 与 Agent 进行交互

---

## 🤖 Agent 介绍

系统包含 **6 个专业 Agent**，每个 Agent 都有明确的职责：

### 1️⃣ RSS Reader（RSS 采集器）

**职责**：自动采集 RSS 订阅源的内容

- 📡 **定时采集**：每 30 分钟自动检查 RSS 源
- 🔍 **智能过滤**：去重、过滤短内容
- 📤 **内容分发**：将新内容发送到「灵感捕手」频道
- 🗄️ **数据存储**：保存原始内容到数据库

**配置文件**：[`config/rss_feeds.yaml`](config/rss_feeds.yaml)

```yaml
# 添加你的 RSS 源
feeds:
  - name: "我的技术博客"
    url: "https://example.com/feed.xml"
    category: "tech"
    enabled: true
```

---

### 2️⃣ Web Scraper（网页抓取器）

**职责**：手动抓取指定 URL 的内容

- 🎯 **按需抓取**：监听「灵感采集」频道的 URL
- 📄 **全文提取**：自动提取网页正文内容
- 🧹 **内容清洗**：去除广告、导航等无关内容
- 📤 **内容分发**：将抓取的内容发送到处理流程

**使用方式**：
1. 在 Studio 的「灵感采集」频道发送消息
2. 输入 URL 或包含 URL 的文本
3. Agent 自动抓取并处理

**示例**：
```
请抓取：https://openai.com/blog/gpt-4
```

---

### 3️⃣ Summarizer（摘要生成器）

**职责**：生成多级智能摘要

- 📝 **三级摘要**：
  - 一句话摘要（10-15字）
  - 段落摘要（50-80字）
  - 详细摘要（150-200字）
- 🎯 **关键信息**：提取核心要点和引用
- 💭 **情感分析**：分析内容的情感倾向
- 📊 **质量评估**：评估内容的信息密度

**提示词配置**：[`config/prompts/summarize.py`](config/prompts/summarize.py)

---

### 4️⃣ Tagger（标签分类器）

**职责**：自动打标签和分类

- 🏷️ **智能标签**：根据内容生成 3-5 个标签
- 📂 **自动分类**：
  - AI（人工智能）
  - Tech（技术）
  - Business（商业）
  - Science（科学）
  - Other（其他）
- 🎨 **难度评级**：初级、中级、高级
- 🌍 **语言检测**：中文、英文、其他

**提示词配置**：[`config/prompts/tag.py`](config/prompts/tag.py)

---

### 5️⃣ Outline Generator（大纲生成器）

**职责**：根据主题生成文章大纲

- 💡 **多方案生成**：为同一主题生成 2-3 个不同风格的大纲
- 🔍 **知识库检索**：搜索相关内容作为参考
- 📋 **结构化大纲**：
  - 标题和副标题
  - 章节要点
  - 参考资料
- 🎯 **风格多样**：技术分析、实践指南、综述等

**提示词配置**：[`config/prompts/outline.py`](config/prompts/outline.py)

---

### 6️⃣ Writer（内容写作器）

**职责**：基于大纲生成完整文章

- ✍️ **AI 写作**：根据大纲和知识库生成文章
- 📚 **引用整合**：自动引用知识库中的相关内容
- 🎨 **多种风格**：
  - 技术深度分析
  - 实践操作指南
  - 行业趋势综述
- 📏 **长度控制**：支持指定字数范围

**提示词配置**：[`config/prompts/write.py`](config/prompts/write.py)

---

## 🔄 完整工作流程与通信机制

### 🎯 Agent 通信架构

系统采用**频道消息（Channel）+ 事件驱动（Event）**的混合通信架构：

- **频道消息**：用于用户交互和公告通知（可视化）
- **事件驱动**：用于 Agent 之间的协作（高效可靠）

### 📊 通信时机总览表

| Agent | 监听方式 | 触发条件 | 输出方式 |
|-------|---------|---------|---------|
| **RSS阅读器** | 定时器 | 每30分钟 | 频道消息 + 事件 |
| **摘要生成器** | 事件 | `content.discovered` | 事件 |
| **标签生成器** | 事件 | `content.summarized` | 频道消息 + 事件 |
| **网页抓取器** | 频道消息 | 用户在"灵感采集"发URL | 频道消息 + 事件 |
| **创作协调器** | 频道消息 + 事件 | 用户在"创作工坊"发消息 | 频道消息 + 事件 |
| **大纲生成器** | 事件 | `creation.request_outlines` | 事件 |
| **文章写作器** | 事件 | `creation.start_writing` | 事件 |

---

### 流程 1：自动采集 RSS → 智能处理

```
RSS阅读器 (定时自动)
    ↓ [每 30 分钟]
    ├→ 频道: "通用频道" (上线通知)
    ├→ 频道: "灵感捕手" (新内容通知)
    └→ 事件: content.discovered
             ↓
    摘要生成器 (@on_event)
             ├→ 调用 LLM 生成三级摘要
             └→ 事件: content.summarized
                      ↓
         标签生成器 (@on_event)
                  ├→ 调用 LLM 生成标签
                  ├→ 频道: "知识库" (内容卡片)
                  └→ 事件: content.tagged
```

### 流程 2：手动抓取 URL → 智能处理

```
用户 → 频道: "灵感采集" (发送URL)
           ↓
    网页抓取代理 (@on_event监听频道)
           ├→ 频道: "灵感采集" (回复结果)
           └→ 事件: content.discovered
                   ↓
              (进入流程1处理管道)
```

### 流程 3：AI 创作文章

```
用户 → 频道: "创作工坊" ("写一篇关于XX的文章")
           ↓
    创作协调器 (@on_event监听频道)
           ├→ 频道: "创作工坊" (确认收到)
           └→ 事件: creation.request_outlines
                   ↓
         大纲生成器 (@on_event)
                   ├→ 搜索知识库
                   └→ 事件: creation.outlines_ready
                           ↓
                  创作协调器 (@on_event)
                           └→ 频道: "创作工坊" (展示大纲)

用户 → 频道: "创作工坊" (选择 "1")
           ↓
    创作协调器 (状态机路由)
           └→ 事件: creation.start_writing
                   ↓
          文章写作器 (@on_event)
                   └→ 事件: creation.draft_ready
                           ↓
                  创作协调器 (@on_event)
                           └→ 频道: "创作工坊" (展示文章)
```

---

## 📖 详细使用指南

### 场景 1：配置 RSS 自动采集

#### 步骤 1：编辑 RSS 配置

编辑文件：[`config/rss_feeds.yaml`](config/rss_feeds.yaml)

```yaml
feeds:
  # 技术博客
  - name: "阮一峰的网络日志"
    url: "http://www.ruanyifeng.com/blog/atom.xml"
    category: "tech"
    enabled: true
  
  # Hacker News
  - name: "Hacker News Front Page"
    url: "https://hnrss.org/frontpage"
    category: "tech-news"
    enabled: true
  
  # 暂时禁用的源
  - name: "暂时不用的博客"
    url: "https://example.com/feed"
    enabled: false
```

#### 步骤 2：重启 RSS Reader

```bash
# 如果使用 tmux
tmux kill-window -t knowledgeflow:1
tmux new-window -t knowledgeflow:1 -n 'RSS-Reader'
tmux send-keys -t knowledgeflow:1 'python agents/rss_reader.py' C-m

# 或手动重启
# Ctrl+C 停止，然后重新运行
python agents/rss_reader.py
```

#### 步骤 3：查看采集结果

在 OpenAgents Studio 中：
- 📊 访问「灵感捕手」频道：查看新采集的内容
- 📚 访问「知识库」频道：查看处理完成的内容（含摘要和标签）

使用命令行查询数据库：

```bash
# 进入数据库
sqlite3 data/knowledge-flow/content.db

# 查看最新采集的 10 条内容
SELECT id, title, category, collected_at
FROM content_items
ORDER BY collected_at DESC
LIMIT 10;

# 查看某个分类的内容
SELECT title, summary_one_sentence
FROM content_items
WHERE category = 'AI'
LIMIT 5;

# 退出
.quit
```

---

### 场景 2：手动抓取网页内容

#### 方式 A：通过 OpenAgents Studio（推荐）

1. **打开 Studio**：浏览器访问 http://localhost:8700

2. **进入「灵感采集」频道**

3. **发送灵感采集**：
   ```
   请抓取：https://openai.com/blog/gpt-4
   ```
   
   或直接发送 URL：
   ```
   https://example.com/article
   ```

4. **等待处理**：
   - Web Scraper 自动识别并抓取
   - Summarizer 生成摘要
   - Tagger 自动分类和打标签

5. **查看结果**：
   在「知识库」频道查看处理完成的内容

#### 方式 B：通过 Python 脚本

创建测试脚本 `test_scrape.py`：

```python
from openagents import Client
import asyncio

async def test_scrape():
    client = Client()
    await client.connect("http://localhost:8700")
    
    # 获取 messaging adapter
    messaging = client.mod_adapters.get("openagents.mods.workspace.messaging")
    
    # 发送灵感采集
    await messaging.send_channel_message(
        channel="灵感采集",
        text="请抓取：https://openai.com/blog/gpt-4"
    )
    
    print("✅ 灵感采集已发送")
    await asyncio.sleep(5)
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_scrape())
```

运行：
```bash
python test_scrape.py
```

---

### 场景 3：AI 创作文章

#### 步骤 1：发起创作请求

在 OpenAgents Studio 的「创作工坊」频道发送：

**简单请求**：
```
写一篇关于大语言模型的技术文章
```

**详细请求**：
```
主题：GPT-4 的技术创新与应用
关键词：Transformer, RLHF, 多模态
风格：技术深度分析
字数：2000 字左右
目标读者：AI 工程师和研究人员
```

#### 步骤 2：选择大纲方案

Outline Generator 会生成 2-3 个大纲方案：

```
📝 已为您生成 3 个大纲方案：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【方案 1：技术深度解析】
适合：深入理解技术细节的读者

一、GPT-4 的核心技术突破
   1.1 Transformer 架构的演进
   1.2 多模态能力的实现
   1.3 RLHF 训练方法

二、工程实现与优化
   2.1 模型规模与效率平衡
   2.2 推理加速技术
   ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【方案 2：实践应用指南】
适合：关注实际应用的开发者
...

请回复选择的方案编号，或提出修改建议。
```

#### 步骤 3：确认大纲

回复：
```
使用方案 1
```

或提出修改：
```
使用方案 1，但增加一个关于成本优化的章节
```

#### 步骤 4：获取完整文章

Writer Agent 会：
1. 基于选定的大纲展开写作
2. 从知识库中检索相关内容作为参考
3. 自动添加引用和链接
4. 生成完整的文章内容

最终在「创作工坊」频道输出完整文章！

---

## ⚙️ 配置说明

### 网络配置

文件：[`network.yaml`](network.yaml)

```yaml
network:
  name: "KnowledgeFlow"
  mode: "centralized"
  
  transports:
    - type: "http"
      config:
        port: 8700              # Web 端口
        serve_studio: true      # 启用 Studio
        serve_mcp: true
    - type: "grpc"
      config:
        port: 8600              # gRPC 端口

  # 频道配置
  mods:
    - name: "openagents.mods.workspace.messaging"
      config:
        default_channels:
          - name: "通用频道"
            description: "系统通知和状态公告"
          - name: "灵感捕手"
            description: "RSS和网页采集的新内容"
          - name: "知识库"
            description: "已处理的内容（含摘要和标签）"
          - name: "创作工坊"
            description: "内容创作空间（大纲和草稿）"
          - name: "灵感采集"
            description: "请求抓取指定URL"
```

### Agent 配置

每个 Agent 的提示词可以在 `config/prompts/` 目录中自定义：

- **[`summarize.py`](config/prompts/summarize.py)**：摘要生成提示词
- **[`tag.py`](config/prompts/tag.py)**：标签分类提示词
- **[`outline.py`](config/prompts/outline.py)**：大纲生成提示词
- **[`write.py`](config/prompts/write.py)**：文章写作提示词

### 数据库配置

SQLite 数据库位置：`data/knowledge-flow/content.db`

主要表结构：

```sql
-- 内容表
CREATE TABLE content_items (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE,
    raw_content TEXT,
    source TEXT,
    source_type TEXT,
    category TEXT,
    tags TEXT,
    summary_one_sentence TEXT,
    summary_paragraph TEXT,
    summary_detailed TEXT,
    processing_status TEXT,
    collected_at TIMESTAMP,
    processed_at TIMESTAMP
);

-- 大纲表
CREATE TABLE outlines (
    id INTEGER PRIMARY KEY,
    topic TEXT NOT NULL,
    outline_content TEXT,
    created_at TIMESTAMP
);

-- 草稿表
CREATE TABLE drafts (
    id INTEGER PRIMARY KEY,
    outline_id INTEGER,
    content TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (outline_id) REFERENCES outlines(id)
);
```

---

## 🛠️ 管理和监控

### 启动和停止

```bash
# 一键启动所有服务
./start_all.sh

# 停止所有服务
./stop_all.sh

# 查看运行状态
./check_status.sh
```

### Tmux 操作

```bash
# 连接到 tmux 会话
tmux attach -t knowledgeflow

# 切换窗口
Ctrl+B 然后按数字键（0-6）

# 窗口列表：
# 0: Network Server（网络服务器）
# 1: RSS Reader（RSS 采集器）
# 2: Web Scraper（网页抓取器）
# 3: Summarizer（摘要生成器）
# 4: Tagger（标签分类器）
# 5: Outline Generator（大纲生成器）
# 6: Writer（内容写作器）

# 分离会话（保持后台运行）
Ctrl+B 然后按 D

# 关闭所有服务
tmux kill-session -t knowledgeflow
```

### 查看日志

```bash
# 查看所有 Agent 日志
tail -f logs/agents/*.log

# 查看特定 Agent 日志
tail -f logs/agents/rss_reader.log
tail -f logs/agents/summarizer.log

# 查看网络日志
tail -f logs/network.log
```

### 数据库查询

```bash
# 进入数据库
sqlite3 data/knowledge-flow/content.db

# 常用查询
.schema                          # 查看表结构
SELECT COUNT(*) FROM content_items;  # 统计内容数量
SELECT * FROM content_items ORDER BY collected_at DESC LIMIT 5;  # 最新内容

# 退出
.quit
```

---

## 🔧 故障排查

### 问题 1：Agent 无法连接到网络服务器

**症状**：
```
Error: Failed to connect to network server
```

**解决方案**：
1. 确认网络服务器已启动：
   ```bash
   curl http://localhost:8700/health
   ```

2. 检查端口是否被占用：
   ```bash
   lsof -i :8700
   ```

3. 查看网络服务器日志：
   ```bash
   tail -f logs/network.log
   ```

---

### 问题 2：OpenAI API 调用失败

**症状**：
```
Error: Invalid API key or rate limit exceeded
```

**解决方案**：
1. 检查 API Key 是否正确：
   ```bash
   echo $OPENAI_API_KEY
   ```

2. 验证 API Key 可用性：
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. 如果使用代理，检查 `.env` 中的 `OPENAI_API_BASE` 配置

---

### 问题 3：RSS 采集没有新内容

**症状**：日志显示采集完成但没有新内容

**解决方案**：
1. 检查 RSS 配置：
   ```bash
   cat config/rss_feeds.yaml
   ```

2. 手动测试 RSS 源：
   ```bash
   python -c "
   from tools.content_tools import get_rss_reader
   reader = get_rss_reader()
   items = reader.fetch_all_feeds()
   print(f'Fetched {len(items)} items')
   "
   ```

3. 查看数据库中已有的 URL：
   ```bash
   sqlite3 data/knowledge-flow/content.db "SELECT url FROM content_items;"
   ```

---

### 问题 4：tmux 会话丢失

**症状**：
```
no sessions
```

**解决方案**：
1. 列出所有 tmux 会话：
   ```bash
   tmux ls
   ```

2. 重新启动：
   ```bash
   ./start_all.sh
   ```

---

## 📚 更多文档

- **[快速开始指南](QUICKSTART.md)**：5 分钟上手教程
- **[部署指南](DEPLOYMENT.md)**：生产环境部署
- **[故障排查](TROUBLESHOOTING.md)**：详细的问题解决方案
- **[OpenAgents 文档](docs/)**：框架架构和原理

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发新的 Agent

1. 继承 `WorkerAgent` 类
2. 实现 `on_startup()` 和 `on_shutdown()` 方法
3. 使用频道消息系统进行通信
4. 添加到 `start_all.sh` 启动脚本

示例：

```python
from openagents.agents.worker_agent import WorkerAgent

class MyAgent(WorkerAgent):
    default_agent_id = "my-agent"
    
    async def on_startup(self):
        # Agent 启动时执行
        await self._send_message("通用频道", "🤖 我上线了！")
    
    async def _send_message(self, channel: str, text: str):
        messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
        if messaging:
            await messaging.send_channel_message(channel=channel, text=text)
```

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [OpenAgents](https://github.com/OpenAgentsInc/openagents) - 多 Agent 协作框架
- [OpenAI](https://openai.com/) - GPT-4 API

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个 Star！**

Made with ❤️ by KnowledgeFlow Team

</div>
