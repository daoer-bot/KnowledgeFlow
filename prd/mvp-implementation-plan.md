# KnowledgeFlow MVP - 实施计划

## 📅 开发时间线

**总时长**: 3 周  
**团队规模**: 1-2 名开发者  
**目标**: 完成可演示的 MVP 版本

---

## 🗓️ Week 1: 基础设施搭建

### Day 1-2: 项目初始化

**任务清单**:
- [x] 创建项目目录结构
- [ ] 初始化 Git 仓库
- [ ] 配置 Python 虚拟环境
- [ ] 安装 OpenAgents 和依赖
- [ ] 创建 network.yaml 配置文件
- [ ] 启动并测试网络连接
- [ ] 配置 Messaging Mod 和频道

**验收标准**:
```bash
✅ openagents network start 成功运行
✅ 访问 http://localhost:8700 能看到 Studio 界面
✅ 能在 Studio 中看到配置的频道
```

**预计时间**: 4-6 小时

---

### Day 3-4: RSS Reader Agent

**任务清单**:
- [ ] 创建 `agents/rss_reader.py`
- [ ] 实现 RSS 解析功能（使用 feedparser）
- [ ] 实现全文提取（使用 trafilatura）
- [ ] 实现去重逻辑（检查 URL）
- [ ] 配置定时任务（每 30 分钟）
- [ ] 发送 `content.discovered` 事件
- [ ] 发送消息到 #content-feed 频道

**核心代码结构**:
```python
class RSSReaderAgent(WorkerAgent):
    async def on_startup(self):
        # 启动定时任务
        asyncio.create_task(self.schedule_fetch())
    
    async def schedule_fetch(self):
        while True:
            await self.fetch_all_feeds()
            await asyncio.sleep(30 * 60)
    
    async def fetch_all_feeds(self):
        # 读取配置的 RSS 源
        # 解析每个源
        # 提取全文
        # 去重
        # 发送事件
```

**验收标准**:
```bash
✅ Agent 能自动采集 RSS 内容
✅ #content-feed 频道能看到新内容通知
✅ 内容保存到数据库
✅ 去重功能正常工作
```

**预计时间**: 8-10 小时

---

### Day 5: Web Scraper Agent

**任务清单**:
- [ ] 创建 `agents/web_scraper.py`
- [ ] 监听 #scraper-requests 频道
- [ ] 解析用户发送的 URL
- [ ] 使用 playwright 抓取网页
- [ ] 使用 trafilatura 提取正文
- [ ] 发送 `content.discovered` 事件
- [ ] 回复用户抓取结果

**交互示例**:
```
用户: @web-scraper https://example.com/article
Agent: 🔍 开始抓取...
Agent: ✅ 抓取成功！已添加到内容库
       📄 标题：文章标题
       📊 字数：2,345 字
       [查看详情]
```

**验收标准**:
```bash
✅ 用户能通过 @ 提及触发抓取
✅ 支持常见网站（Medium、知乎等）
✅ 错误处理完善（404、超时等）
✅ 抓取结果发送到 #content-feed
```

**预计时间**: 6-8 小时

---

### Day 6-7: 数据库和工具函数

**任务清单**:
- [ ] 设计并创建数据库表
- [ ] 实现 `tools/database.py`（数据库操作）
- [ ] 实现 `tools/llm_client.py`（LLM 客户端封装）
- [ ] 创建提示词模板文件
- [ ] 编写单元测试
- [ ] 完善日志系统

**验收标准**:
```bash
✅ 数据库 CRUD 操作正常
✅ LLM 客户端能正常调用 API
✅ 有完善的错误处理和重试机制
✅ 日志记录完整
```

**预计时间**: 6-8 小时

---

## 🗓️ Week 2: 处理能力和创作能力

### Day 8-9: Summarizer Agent

**任务清单**:
- [ ] 创建 `agents/summarizer.py`
- [ ] 监听 `content.discovered` 事件
- [ ] 调用 LLM 生成三种长度的摘要
- [ ] 提取关键要点和引用
- [ ] 发送 `content.summarized` 事件
- [ ] 更新数据库
- [ ] 优化提示词

**LLM 提示词**:
```python
SYSTEM = """你是专业的内容摘要助手..."""

USER = """
标题：{title}
内容：{content}

请生成：
1. 一句话摘要（20-30字）
2. 段落摘要（100-150字）
3. 详细摘要（300-500字）
4. 3-5个关键要点
5. 1-3个重要引用

输出 JSON 格式。
"""
```

**验收标准**:
```bash
✅ 能自动处理新采集的内容
✅ 摘要质量良好（人工评估）
✅ 处理时间 < 30 秒
✅ 错误率 < 5%
```

**预计时间**: 8-10 小时

---

### Day 10: Tagger Agent

**任务清单**:
- [ ] 创建 `agents/tagger.py`
- [ ] 监听 `content.summarized` 事件
- [ ] 调用 LLM 生成标签和分类
- [ ] 发送 `content.tagged` 事件
- [ ] 发送到 #knowledge-base 频道
- [ ] 展示美观的内容卡片

**频道消息格式**:
```markdown
✅ 内容已处理
━━━━━━━━━━━━━━━━
📌 {title}

📝 {summary_paragraph}

🔑 关键要点：
• {point_1}
• {point_2}
• {point_3}

🏷️ {category} | {tags}

[查看详情] [用于创作]
```

**验收标准**:
```bash
✅ 标签准确率 > 80%
✅ 分类合理
✅ #knowledge-base 频道展示美观
✅ 完整流程：采集→摘要→标签 < 2分钟
```

**预计时间**: 6-8 小时

---

### Day 11-12: Outline Generator Agent

**任务清单**:
- [ ] 创建 `agents/outline_generator.py`
- [ ] 监听 #creation 频道的 @ 提及
- [ ] 解析用户主题
- [ ] 从数据库检索相关内容
- [ ] 实现简单的相关性匹配（关键词或语义）
- [ ] 调用 LLM 生成 2-3 个大纲方案
- [ ] 展示大纲和关联素材
- [ ] 等待用户选择

**交互流程**:
```
用户: @outline-generator 生成关于「AI编程」的大纲

Agent: 🔍 正在搜索相关素材...
       找到 5 篇相关内容

Agent: 📋 已生成 3 个大纲方案

       【方案 A：技术演进视角】
       1. 引言：从代码补全到智能助手
       2. 技术发展历程
       3. 核心技术解析
       ...
       
       【方案 B：实战应用视角】
       ...
       
       💡 基于以下素材：
       • GitHub Copilot 技术原理（HackerNews）
       • Cursor 使用体验（Medium）
       ...
       
       请回复选择方案（A/B/C）
```

**验收标准**:
```bash
✅ 能根据主题检索相关素材
✅ 生成的大纲结构合理
✅ 多个方案有明显差异
✅ 交互流程顺畅
```

**预计时间**: 10-12 小时

---

### Day 13-14: Writer Agent

**任务清单**:
- [ ] 创建 `agents/writer.py`
- [ ] 监听用户选择大纲的消息
- [ ] 加载选定的大纲和素材
- [ ] 调用 LLM 分段生成文章
- [ ] 整合成完整文章
- [ ] 添加引用来源
- [ ] 发送到 #drafts 频道
- [ ] 统计字数等信息

**生成策略**:
```python
# 分段生成，避免 token 超限
for section in outline.sections:
    section_content = await self.generate_section(
        section=section,
        materials=related_materials,
        previous_context=previous_sections
    )
    full_article += section_content
```

**输出格式**:
```markdown
# 文章标题

## 引言
...

## 第一部分
...

## 第二部分
...

## 结语
...

---
## 参考资料
1. [来源1标题](url1)
2. [来源2标题](url2)
```

**验收标准**:
```bash
✅ 文章结构完整、逻辑清晰
✅ 字数符合要求（2000±200字）
✅ 包含引用来源
✅ 生成时间 < 3 分钟
✅ 内容质量良好（人工评估）
```

**预计时间**: 10-12 小时

---

## 🗓️ Week 3: 优化和完善

### Day 15-16: 端到端测试

**任务清单**:
- [ ] 编写端到端测试脚本
- [ ] 测试完整流程：
  - RSS 自动采集
  - Web 手动抓取
  - 自动摘要和标签
  - 大纲生成
  - 文章创作
- [ ] 修复发现的 bug
- [ ] 优化性能瓶颈
- [ ] 完善错误处理

**测试场景**:
```python
# test_e2e.py
async def test_full_workflow():
    # 1. 触发灵感捕手
    # 2. 等待处理完成
    # 3. 请求生成大纲
    # 4. 选择大纲
    # 5. 请求创作
    # 6. 验证草稿质量
```

**预计时间**: 8-10 小时

---

### Day 17: 文档编写

**任务清单**:
- [ ] 编写 README.md
- [ ] 编写用户手册
- [ ] 编写开发者文档
- [ ] 记录 API 接口
- [ ] 添加代码注释
- [ ] 创建演示视频脚本

**文档清单**:
```
docs/
├── README.md              # 项目介绍
├── INSTALL.md            # 安装指南
├── USER_GUIDE.md         # 用户手册
├── DEVELOPER_GUIDE.md    # 开发指南
├── API.md                # API 文档
└── DEMO.md               # 演示脚本
```

**预计时间**: 6-8 小时

---

### Day 18: UI/UX 优化

**任务清单**:
- [ ] 优化频道消息格式
- [ ] 添加 emoji 和视觉元素
- [ ] 改进交互反馈
- [ ] 添加进度提示
- [ ] 优化错误消息

**消息格式示例**:
```markdown
✅ 成功消息用绿色勾
⚠️ 警告消息用黄色感叹号
❌ 错误消息用红色叉
🔄 进度消息用蓝色圆圈
📊 统计信息用图表
🎯 重要提示用靶心
```

**预计时间**: 4-6 小时

---

### Day 19-21: 性能优化和收尾

**任务清单**:
- [ ] 性能优化
  - LLM 调用缓存
  - 数据库查询优化
  - 异步任务优化
- [ ] 代码重构和清理
- [ ] 添加更多错误处理
- [ ] 完善日志系统
- [ ] 