# KnowledgeFlow MVP - 架构设计文档

## 🎯 系统架构概览

```
用户界面层 (OpenAgents Studio Web)
              ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        OpenAgents Network
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              ↓
    ┌─────────────────────┐
    │   Event Gateway     │
    │  (事件分发中心)      │
    └─────────────────────┘
              ↓
    ┌─────────────────────┐
    │  Messaging Mod      │
    │  (频道和消息系统)    │
    └─────────────────────┘
              ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          Agent 网络
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[采集层]
RSS Reader ──┐
             ├──→ content.discovered
Web Scraper ─┘

[处理层]
Summarizer ──┐
             ├──→ content.processed
Tagger ──────┘

[创作层]
Outline Gen ─┐
             ├──→ content.ready
Writer ──────┘
```

---

## 📊 数据库设计

```sql
-- 内容表
CREATE TABLE content_items (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE,
    raw_content TEXT,
    source TEXT,
    source_type TEXT, -- rss/web
    collected_at DATETIME,
    
    -- 处理后数据
    summary_one_line TEXT,
    summary_paragraph TEXT,
    summary_detailed TEXT,
    key_points JSON,
    key_quotes JSON,
    
    -- 标签和分类
    tags JSON,
    category TEXT,
    sentiment TEXT,
    relevance_score REAL,
    
    -- 状态
    status TEXT, -- discovered/processed/archived
    processed_at DATETIME
);

-- 大纲表
CREATE TABLE outlines (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    content TEXT,
    style TEXT,
    related_content_ids JSON,
    created_at DATETIME,
    selected BOOLEAN DEFAULT FALSE
);

-- 草稿表
CREATE TABLE drafts (
    id TEXT PRIMARY KEY,
    outline_id TEXT,
    title TEXT,
    content TEXT,
    word_count INTEGER,
    status TEXT, -- draft/reviewed/published
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (outline_id) REFERENCES outlines(id)
);

-- 配置表
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME
);
```

---

## 🔄 事件流详细设计

### 1. 灵感捕手事件

```python
# content.discovered
{
    "event_name": "content.discovered",
    "source_agent": "rss-reader",
    "payload": {
        "content_id": "uuid-xxx",
        "source_type": "rss",  # rss/web
        "source_name": "HackerNews",
        "title": "文章标题",
        "url": "https://...",
        "raw_content": "完整正文",
        "metadata": {
            "published_at": "2025-01-15T10:00:00Z",
            "author": "作者名",
            "feed_url": "RSS源地址"
        }
    }
}
```

### 2. 摘要生成事件

```python
# content.summarized
{
    "event_name": "content.summarized",
    "source_agent": "summarizer",
    "payload": {
        "content_id": "uuid-xxx",
        "summaries": {
            "one_line": "20-30字摘要",
            "paragraph": "100-150字摘要",
            "detailed": "300-500字摘要"
        },
        "key_points": [
            "关键要点1",
            "关键要点2",
            "关键要点3"
        ],
        "key_quotes": [
            "重要引用1",
            "重要引用2"
        ]
    }
}
```

### 3. 标签生成事件

```python
# content.tagged
{
    "event_name": "content.tagged",
    "source_agent": "tagger",
    "payload": {
        "content_id": "uuid-xxx",
        "tags": {
            "topics": ["AI", "编程"],
            "technologies": ["Python", "GPT-4"],
            "scenarios": ["教程", "最佳实践"]
        },
        "category": "技术教程",
        "sentiment": "positive",  # positive/neutral/negative
        "relevance_score": 0.85
    }
}
```

### 4. 大纲生成事件

```python
# content.outline_generated
{
    "event_name": "content.outline_generated",
    "source_agent": "outline-generator",
    "payload": {
        "outline_id": "uuid-xxx",
        "topic": "AI编程助手发展趋势",
        "outlines": [
            {
                "id": "outline-a",
                "title": "方案A：技术演进视角",
                "content": "# 大纲内容...",
                "related_materials": ["content-id-1", "content-id-2"]
            },
            {
                "id": "outline-b",
                "title": "方案B：实战应用视角",
                "content": "# 大纲内容..."
            }
        ]
    }
}
```

### 5. 草稿完成事件

```python
# content.draft_ready
{
    "event_name": "content.draft_ready",
    "source_agent": "writer",
    "payload": {
        "draft_id": "uuid-xxx",
        "outline_id": "uuid-xxx",
        "title": "文章标题",
        "content": "完整文章内容（Markdown格式）",
        "statistics": {
            "word_count": 2156,
            "paragraph_count": 6,
            "reference_count": 5,
            "estimated_reading_time": 8
        },
        "references": [
            {
                "title": "参考资料1",
                "url": "https://..."
            }
        ]
    }
}
```

---

## 🤖 Agent 实现框架

### Agent 基类模板

```python
from openagents.agents.worker_agent import WorkerAgent, on_event
from typing import Dict, Any
import logging

class BaseContentAgent(WorkerAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def on_startup(self):
        """Agent 启动时执行"""
        await self.workspace().channel("general").post(
            f"🤖 {self.config['agent_name']} 已上线"
        )
        self.logger.info(f"{self.config['agent_id']} started")
    
    async def on_shutdown(self):
        """Agent 关闭时执行"""
        await self.workspace().channel("general").post(
            f"👋 {self.config['agent_name']} 下线"
        )
    
    def handle_error(self, error: Exception, context: str):
        """统一错误处理"""
        self.logger.error(f"Error in {context}: {str(error)}")
        # 可以发送错误通知到频道
```

---

## 🛠️ 核心工具模块

### LLM 客户端封装

```python
# tools/llm_client.py
from typing import Dict, List, Optional
import openai
import json

class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False
    ) -> str:
        """生成文本"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if json_mode else None
        )
        
        return response.choices[0].message.content
    
    async def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """带重试的生成"""
        for attempt in range(max_retries):
            try:
                return await self.generate(system_prompt, user_prompt)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避
```

---

## 📝 提示词模板

### 摘要生成提示词

```python
# config/prompts/summarize.txt
SYSTEM_PROMPT = """
你是一个专业的内容摘要助手。你的任务是为文章生成不同长度的摘要。

要求：
1. 准确把握文章核心内容
2. 提取关键信息和要点
3. 保持客观中立的语气
4. 避免主观评价
"""

USER_PROMPT_TEMPLATE = """
请为以下文章生成摘要：

标题：{title}
来源：{source}
内容：
{content}

请输出 JSON 格式，包含以下字段：
{{
    "one_line": "20-30字的一句话摘要",
    "paragraph": "100-150字的段落摘要",
    "detailed": "300-500字的详细摘要",
    "key_points": ["要点1", "要点2", "要点3"],
    "key_quotes": ["重要引用1", "重要引用2"]
}}
"""
```

### 标签生成提示词

```python
# config/prompts/tag.txt
SYSTEM_PROMPT = """
你是一个专业的内容分类和标签生成助手。

分类体系：
- 技术教程
- 行业动态
- 产品评测
- 最佳实践
- 思考总结

标签层级：
- 主题标签：AI、编程、创业、设计等
- 技术标签：Python、React、机器学习等
- 场景标签：教程、案例、评测等
"""

USER_PROMPT_TEMPLATE = """
请为以下内容生成标签和分类：

标题：{title}
摘要：{summary}

请输出 JSON 格式：
{{
    "category": "主分类",
    "tags": {{
        "topics": ["主题标签1", "主题标签2"],
        "technologies": ["技术标签1", "技术标签2"],
        "scenarios": ["场景标签1"]
    }},
    "sentiment": "positive/neutral/negative",
    "relevance_score": 0.85
}}
"""
```

---

## 🚀 启动脚本

### 启动网络

```bash
# start_network.sh
#!/bin/bash

echo "🚀 启动 KnowledgeFlow 网络..."

# 启动 OpenAgents Network
openagents network start --config network.yaml

echo "✅ 网络启动成功！"
echo "📱 Studio 地址: http://localhost:8700"
echo "🔌 gRPC 端口: 8600"
```

### 启动所有 Agent

```bash
# start_agents.sh
#!/bin/bash

echo "🤖 启动所有 Agent..."

# 启动采集层
python agents/rss_reader.py &
python agents/web_scraper.py &

# 启动处理层
python agents/summarizer.py &
python agents/tagger.py &

# 启动创作层
python agents/outline_generator.py &
python agents/writer.py &

echo "✅ 所有 Agent 已启动"
```

---

## 📦 依赖清单

```txt
# requirements.txt

# OpenAgents 框架
openagents>=0.6.4

# LLM API
openai>=1.0.0
anthropic>=0.7.0  # 可选

# 灵感捕手
feedparser>=6.0.10
playwright>=1.40.0
trafilatura>=1.6.0
beautifulsoup4>=4.12.0
requests>=2.31.0

# 数据处理
tiktoken>=0.5.0
pydantic>=2.0.0

# 向量搜索（可选）
chromadb>=0.4.0
sentence-transformers>=2.2.0

# 工具库
pyyaml>=6.0
python-dotenv>=1.0.0
aiohttp>=3.9.0

# 开发工具
pytest>=7.4.0
black>=23.0.0
mypy>=1.7.0
```

---

## 🎮 快速开始指南

### 1. 环境准备

```bash
# 克隆项目
cd knowledge-flow

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件，添加 API Key
nano .env
```

```.env
# .env.example
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# 可选
ANTHROPIC_API_KEY=your-anthropic-key
```

### 3. 启动系统

```bash
# 1. 启动网络
bash start_network.sh

# 2. 新开终端，启动 Agent
bash start_agents.sh

# 3. 打开浏览器访问 Studio
open http://localhost:8700
```

### 4. 测试流程

1. 访问 Studio Web 界面
2. 查看 #content-feed 频道，应该看到自动采集的内容
3. 查看 #knowledge-base 频道，查看处理后的内容
4. 在 #creation 频道发送：`@outline-generator 请生成关于「AI编程」的文章大纲`
5. 等待大纲生成后，回复：`@writer-agent 使用方案A创作`
6. 在 