# KnowledgeFlow - AI 知识管理与内容创作助手 MVP

> 一个基于 OpenAgents 的智能内容创作系统  
> 从信息采集 → 智能处理 → AI 创作的完整闭环

---

## 一、项目概述

### 这是什么？

一个智能助手，帮你：
1. **自动收集**感兴趣的文章（RSS订阅）
2. **智能整理**成摘要和标签
3. **AI 帮写**文章（提供素材和大纲）

### 核心价值

- 📚 **自动建立知识库** - 不再需要手动收藏和整理
- 🧠 **AI 理解内容** - 自动提取要点和分类
- ✍️ **辅助创作** - 从素材到成文，AI 全程协助

---

## 二、系统设计（超简化版）

### 工作流程

```
1. 📥 采集内容
   ↓
2. 🧠 AI 理解（摘要+标签）
   ↓
3. 💾 保存到知识库
   ↓
4. ✍️ 用户：我想写关于 XX 的文章
   ↓
5. 🤖 AI：生成 3 个大纲方案
   ↓
6. 👤 用户：选方案 A
   ↓
7. ✅ AI：生成完整文章
```

### 需要的 Agent（6个）

| Agent | 作用 | 触发方式 |
|-------|------|----------|
| **RSS Reader** | 自动采集 RSS 订阅 | 每30分钟自动 |
| **Web Scraper** | 抓取指定网页 | 用户 @提及 |
| **Summarizer** | 生成摘要 | 自动处理新内容 |
| **Tagger** | 打标签分类 | 自动处理 |
| **Outline Generator** | 生成文章大纲 | 用户 @提及 |
| **Writer** | 写文章 | 用户 @提及 |

---

## 三、用户怎么用？

### 场景 1: 日常使用（全自动）

```
早上打开 OpenAgents Studio
  ↓
查看 #content-feed 频道
  ↓
看到系统自动采集的 10 篇新文章
  ↓
查看 #knowledge-base 频道
  ↓
浏览 AI 整理好的摘要和标签
```

### 场景 2: 手动抓取网页

```
在频道发送：
@web-scraper https://example.com/article

系统回复：
✅ 抓取成功！
📄 标题：GitHub Copilot 技术解析
📊 2,345 字
```

### 场景 3: 创作文章

```
发送：
@outline-generator 生成关于「AI编程助手」的文章大纲

系统回复：
📋 生成了 3 个大纲：
  A. 技术演进视角
  B. 实战应用视角
  C. 深度思考视角

你回复：
使用方案 A

发送：
@writer-agent 使用方案 A 创作，2000字

系统回复：
✅ 文章完成！
📄 从代码补全到智能助手：AI编程的进化之路
📊 2,156字 | 5个引用
```

---

## 四、技术实现

### 技术栈

- **框架**: OpenAgents 0.6.4
- **LLM**: OpenAI GPT-4o-mini
- **数据库**: SQLite（内置）
- **Python 库**: feedparser, playwright, trafilatura

### 项目结构

```
knowledge-flow/
├── network.yaml           # 网络配置
├── agents/               # 6个Agent的实现
│   ├── rss_reader.py
│   ├── web_scraper.py
│   ├── summarizer.py
│   ├── tagger.py
│   ├── outline_generator.py
│   └── writer.py
├── config/
│   ├── rss_feeds.yaml    # RSS订阅源
│   └── prompts/          # LLM提示词
├── tools/                # 工具函数
└── data/                 # 数据存储
```

### 快速启动

```bash
# 1. 安装
pip install openagents feedparser playwright trafilatura

# 2. 配置
export OPENAI_API_KEY="your-key"

# 3. 启动网络
openagents network start --config network.yaml

# 4. 启动所有 Agent
python agents/rss_reader.py &
python agents/web_scraper.py &
python agents/summarizer.py &
python agents/tagger.py &
python agents/outline_generator.py &
python agents/writer.py &

# 5. 访问界面
open http://localhost:8700
```

---

## 五、开发计划（3周）

### Week 1: 搭建基础
- Day 1-2: 配置 OpenAgents 网络
- Day 3-4: 实现 RSS Reader 和 Web Scraper
- Day 5-7: 数据库和工具函数

### Week 2: 核心功能
- Day 8-9: 实现 Summarizer
- Day 10: 实现 Tagger
- Day 11-12: 实现 Outline Generator
- Day 13-14: 实现 Writer

### Week 3: 测试优化
- Day 15-16: 端到端测试
- Day 17: 文档
- Day 18-21: 优化和收尾

---

## 六、为什么这个方案好？

### ✅ 发挥 OpenAgents 极致特性

1. **多 Agent 协作** - 6个专业化 Agent 协同工作
2. **事件驱动** - 完整的事件链路
3. **人机共创** - 透明的协作过程
4. **模块化** - 易于扩展新功能

### ✅ 实际价值高

- 不是玩具项目，真正有用
- 解决内容创作者的实际痛点
- 可以持续使用和改进

### ✅ 3周可完成

- 技术栈成熟
- 功能范围明确
- 没有复杂依赖

---

## 七、MVP vs 完整版

### MVP 包含（3周完成）
✅ RSS 自动采集  
✅ 网页手动抓取  
✅ AI 摘要和标签  
✅ 大纲生成  
✅ 文章创作  
✅ Web 界面交互  

### 未来扩展（v2.0）
⏳ 知识图谱可视化  
⏳ 多平台适配（小红书、知乎）  
⏳ 协作编辑  
⏳ 播客/视频素材  
⏳ 移动端  

---

## 八、关键数据

| 指标 | 目标 |
|------|------|
| Agent 数量 | 6 个 |
| 开发时间 | 3 周 |
| 核心功能 | 采集→处理→创作 |
| 用户界面 | OpenAgents Studio |
| 从采集到成文 | < 5 分钟 |
| LLM 成本 | 约 $0.1/篇文章 |

---

## 总结

这是一个**简单但完整**的 MVP：
- 🎯 **目标明确**：帮助内容创作
- 🚀 **快速实现**：3周可完成
- 💎 **价值清晰**：真正解决问题
- 🔧 **技术合理**：充分利用 OpenAgents

**下一步**：开始实施 Week 1 的任务！