# AI 驱动的知识管理与内容创作助手 - MVP 产品需求文档

## 📋 项目概述

**项目名称**: KnowledgeFlow - AI 知识流动与内容创作系统  
**版本**: MVP v1.0  
**目标**: 构建一个基于 OpenAgents 框架的智能系统，实现从信息采集到内容创作的完整闭环，展示多 Agent 协作和人机共创能力。

---

## 🎯 MVP 核心目标

### 主要目标
1. ✅ 验证 OpenAgents 框架的多 Agent 协作能力
2. ✅ 实现信息采集 → 处理 → 创作的完整流程
3. ✅ 展示事件驱动架构和人机协作模式
4. ✅ 提供实际可用的内容创作辅助工具

### 成功指标
- 6 个 Agent 协同工作无阻塞
- 完整事件流可追溯
- 用户能通过 Studio 界面完成全流程操作
- 从采集到生成文章草稿 < 5 分钟

---

## 🏗️ 系统架构

### 三层 Agent 网络

```
┌─────────────────────────────────────────┐
│         采集层 (Collection Layer)        │
├─────────────────────────────────────────┤
│  RSS Reader Agent  │  Web Scraper Agent │
└──────────┬──────────────────────────────┘
           │ event: content.discovered
           ▼
┌─────────────────────────────────────────┐
│         处理层 (Processing Layer)        │
├─────────────────────────────────────────┤
│ Summarizer Agent  │   Tagger Agent      │
└──────────┬──────────────────────────────┘
           │ event: content.processed
           ▼
┌─────────────────────────────────────────┐
│         创作层 (Creation Layer)          │
├─────────────────────────────────────────┤
│ Outline Generator │   Writer Agent      │
└─────────────────────────────────────────┘
           │ event: content.ready
           ▼
    OpenAgents Studio (人机协作界面)
```

---

## 🤖 Agent 详细设计

### 1. RSS Reader Agent (采集层)

**职责**: 定期读取配置的 RSS 订阅源，采集新文章

**配置**:
```yaml
agent_id: rss-reader
role: collector
capabilities:
  - rss_parsing
  - content_extraction
schedule: "*/30 * * * *"  # 每30分钟执行一次
```

**订阅源示例**:
- HackerNews RSS
- Medium Tech RSS
- 阮一峰的周刊
- TechCrunch RSS

**输出事件**:
```python
Event(
    event_name="content.discovered",
    payload={
        "source": "rss",
        "feed_name": "HackerNews",
        "title": "文章标题",
        "url": "https://...",
        "content": "文章正文",
        "published_at": "2025-01-01T12:00:00Z",
        "raw_data": {...}
    }
)
```

**技术实现**:
- 使用 `feedparser` 库解析 RSS
- 使用 `requests` + `BeautifulSoup` 提取全文
- 去重逻辑：检查 URL 是否已处理

---

### 2. Web Scraper Agent (采集层)

**职责**: 根据用户指定的 URL 列表，抓取网页内容

**配置**:
```yaml
agent_id: web-scraper
role: collector
capabilities:
  - web_scraping
  - content_cleaning
trigger: on_demand  # 用户手动触发
```

**触发方式**:
用户在 `#scraper-requests` 频道发送消息：
```
@web-scraper 请抓取 https://example.com/article
```

**输出事件**: 同 RSS Reader Agent

**技术实现**:
- 使用 `playwright` 或 `selenium` 处理动态内容
- 使用 `trafilatura` 提取干净的正文
- 支持常见网站的特殊处理（Medium、知乎等）

---

### 3. Summarizer Agent (处理层)

**职责**: 为采集到的内容生成摘要

**监听事件**: `content.discovered`

**处理流程**:
1. 接收原始内容
2. 调用 LLM API 生成三种长度的摘要：
   - **一句话摘要** (20-30字)
   - **段落摘要** (100-150字)
   - **详细摘要** (300-500字)
3. 提取关键引用和数据点

**输出事件**:
```python
Event(
    event_name="content.summarized",
    payload={
        "content_id": "原始内容ID",
        "summaries": {
            "one_line": "一句话摘要",
            "paragraph": "段落摘要",
            "detailed": "详细摘要"
        },
        "key_points": ["要点1", "要点2", "要点3"],
        "key_quotes": ["引用1", "引用2"]
    }
)
```

**LLM Prompt 示例**:
```
请为以下文章生成摘要：

文章标题：{title}
文章内容：{content}

要求：
1. 一句话摘要（20-30字）
2. 段落摘要（100-150字）
3. 详细摘要（300-500字）
4. 提取3-5个关键要点
5. 提取1-3个重要引用

输出JSON格式。
```

**技术实现**:
- 使用 OpenAI API (gpt-4o-mini)
- 添加重试机制和错误处理
- Token 优化：超长文本先分段再合并

---

### 4. Tagger Agent (处理层)

**职责**: 为内容自动打标签和分类

**监听事件**: `content.summarized`

**处理流程**:
1. 分析内容主题
2. 生成多层级标签：
   - **主题标签**: AI、编程、创业、设计等
   - **技术标签**: Python、React、机器学习等
   - **场景标签**: 教程、案例、评测等
3. 情感分析：正面/中性/负面

**输出事件**:
```python
Event(
    event_name="content.tagged",
    payload={
        "content_id": "内容ID",
        "tags": {
            "topics": ["AI", "编程"],
            "technologies": ["Python", "LangChain"],
            "scenarios": ["教程", "最佳实践"]
        },
        "category": "技术教程",
        "sentiment": "positive",
        "relevance_score": 0.85
    }
)
```

**分类体系**:
- 技术教程
- 行业动态
- 产品评测
- 最佳实践
- 思考总结

**技术实现**:
- 使用 LLM 进行分类
- 维护标签词典进行标准化
- 支持用户自定义标签规则

---

### 5. Outline Generator Agent (创作层)

**职责**: 根据知识库生成文章大纲

**触发方式**:
用户在 `#creation` 频道发送：
```
@outline-generator 请生成关于「AI编程助手发展趋势」的文章大纲
```

**处理流程**:
1. 解析用户主题
2. 从知识库检索相关内容（已采集和处理的内容）
3. 生成 2-3 个不同角度的大纲方案
4. 发布到频道供用户选择

**输出格式**:
```markdown
## 大纲方案 A：技术演进视角

### 1. 引言
   - AI编程助手的兴起背景
   - 为什么值得关注

### 2. 技术发展历程
   - 2.1 早期的代码补全工具
   - 2.2 GPT模型带来的突破
   - 2.3 当前主流产品对比

### 3. 核心技术解析
   - 3.1 大语言模型的应用
   - 3.2 上下文理解技术
   - 3.3 代码生成与优化

### 4. 用户体验革命
   - 4.1 从工具到助手的转变
   - 4.2 实际使用场景
   - 4.3 效率提升数据

### 5. 未来趋势展望
   - 5.1 技术发展方向
   - 5.2 潜在挑战
   - 5.3 对程序员的影响

### 6. 结语

---
💡 使用素材：
- HackerNews: "GitHub Copilot的技术原理" (2025-01-15)
- Medium: "我如何用Cursor提升50%编程效率" (2025-01-20)
- 阮一峰周刊: "AI编程工具的演进" (2025-01-10)
```

**技术实现**:
- 语义搜索知识库（使用 embedding）
- LLM 生成多角度大纲
- 自动关联相关素材

---

### 6. Writer Agent (创作层)

**职责**: 根据大纲生成文章草稿

**触发方式**:
用户选择大纲后，回复消息：
```
@writer-agent 请使用大纲方案A进行创作
```

**处理流程**:
1. 接收用户选定的大纲
2. 加载相关素材
3. 逐段生成内容
4. 整合成完整文章
5. 添加引用来源

**输出格式**:
```markdown
# AI编程助手的技术演进与未来展望

## 引言

近年来，AI编程助手正在改变程序员的工作方式...

[根据大纲逐段生成]

---

## 参考资料

1. [HackerNews] GitHub Copilot的技术原理
   https://news.ycombinator.com/...
   
2. [Medium] 我如何用Cursor提升50%编程效率
   https://medium.com/...
```

**写作风格配置**:
- 技术深度：入门/中级/深度
- 语言风格：严谨/轻松/口语化
- 文章长度：1000字/2000字/3000字

**技术实现**:
- 使用 LLM 分段生成（减少token消耗）
- 保持上下文一致性
- 自动插入引用链接

---

## 📡 事件流设计

### 完整事件链

```
用户添加RSS源 / 请求抓取网页
           ↓
[RSS Reader / Web Scraper]
    发布: content.discovered
           ↓
[Summarizer Agent] 监听
    发布: content.summarized
           ↓
[Tagger Agent] 监听
    发布: content.tagged
           ↓
    保存到知识库
    发布到 #knowledge-base 频道
           ↓
用户查看知识库，选择主题
    发送: @outline-generator 生成大纲
           ↓
[Outline Generator] 监听
    发布: content.outline_generated
    发送到 #creation 频道
           ↓
用户选择大纲
    发送: @writer-agent 开始创作
           ↓
[Writer Agent] 监听
    发布: content.draft_ready
    发送到 #drafts 频道
           ↓
用户审核和编辑草稿
```

### 事件数据结构

```python
# 基础事件格式
class ContentEvent:
    event_name: str          # 事件名称
    content_id: str          # 内容唯一标识
    timestamp: datetime      # 时间戳
    source_agent: str        # 来源 Agent
    payload: dict           # 事件数据
    metadata: dict          # 元数据（如重试次数等）

# 存储在 SQLite
CREATE TABLE content_items (
    id TEXT PRIMARY KEY,
    title TEXT,
    url TEXT UNIQUE,
    raw_content TEXT,
    source TEXT,
    collected_at DATETIME,
    
    -- 处理后的数据
    summary_one_line TEXT,
    summary_paragraph TEXT,
    summary_detailed TEXT,
    tags JSON,
    category TEXT,
    
    -- 状态
    status TEXT,  -- 