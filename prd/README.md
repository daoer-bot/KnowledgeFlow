# KnowledgeFlow MVP 产品需求文档

## 📚 文档导航

本目录包含 KnowledgeFlow 项目的完整 MVP 产品需求文档。

### 文档列表

1. **[mvp-knowledge-content-assistant.md](./mvp-knowledge-content-assistant.md)**
   - 产品概述和核心功能
   - Agent 详细设计
   - 事件流设计
   - 人机协作方案

2. **[mvp-architecture.md](./mvp-architecture.md)**
   - 系统架构设计
   - 数据库设计
   - 技术栈选型
   - 核心模块实现

3. **[mvp-implementation-plan.md](./mvp-implementation-plan.md)**
   - 3周开发计划
   - 详细任务清单
   - 验收标准
   - 时间估算

---

## 🎯 项目概述

**项目名称**: KnowledgeFlow - AI 知识流动与内容创作系统

**核心理念**: 构建一个基于 OpenAgents 框架的智能系统，实现从信息采集到内容创作的完整闭环，展示多 Agent 协作和人机共创能力。

---

## ✨ 核心特性

### 1. 自动信息采集 🔍
- **RSS Reader Agent**: 定时采集 RSS 订阅源
- **Web Scraper Agent**: 按需抓取指定网页
- 支持去重和全文提取

### 2. 智能内容处理 🧠
- **Summarizer Agent**: 生成多层次摘要（一句话/段落/详细）
- **Tagger Agent**: 自动打标签和分类
- 提取关键要点和引用

### 3. AI 辅助创作 ✍️
- **Outline Generator**: 根据主题生成多个大纲方案
- **Writer Agent**: 基于大纲和素材生成文章
- 自动添加引用来源

### 4. 人机协作界面 🤝
- 通过 OpenAgents Studio Web 界面交互
- 实时查看 Agent 工作进度
- 在任何环节介入指导

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────┐
│    用户 (OpenAgents Studio)         │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      OpenAgents Network             │
│  ┌─────────────────────────────┐   │
│  │     Event Gateway           │   │
│  └─────────────────────────────┘   │
└─────────────┬───────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────┐        ┌─────▼──┐
│ 采集层  │        │ 处理层  │
│────────│        │────────│
│RSS     │───────▶│Summary │
│Scraper │        │Tagger  │
└────────┘        └─────┬──┘
                        │
                  ┌─────▼──┐
                  │ 创作层  │
                  │────────│
                  │Outline │
                  │Writer  │
                  └────────┘
```

---

## 🚀 快速开始

### 环境要求
- Python 3.10+
- OpenAI API Key
- 8GB+ RAM

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd knowledge-flow

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加 OPENAI_API_KEY

# 5. 启动网络
bash start_network.sh

# 6. 启动 Agent
bash start_agents.sh

# 7. 访问 Studio
open http://localhost:8700
```

---

## 📊 MVP 功能范围

### ✅ 包含功能

1. **信息采集**
   - RSS 自动采集（每30分钟）
   - Web 手动抓取
   - 内容去重

2. **内容处理**
   - 三层次摘要生成
   - 自动标签和分类
   - 关键信息提取

3. **内容创作**
   - 主题检索相关素材
   - 生成多个大纲方案
   - 基于大纲生成文章

4. **人机协作**
   - Studio Web 界面
   - 频道实时通信
   - 简单的交互指令

### ❌ 不包含功能

1. **知识图谱可视化** - 留给 v2.0
2. **多平台内容适配** - 留给 v2.0
3. **协作编辑功能** - 留给 v2.0
4. **用户认证系统** - MVP 使用开放网络
5. **移动端应用** - 仅 Web 界面

---

## 📈 开发计划

### Week 1: 基础设施
- 搭建 OpenAgents 网络
- 实现采集层 Agent
- 完成数据库设计

### Week 2: 处理和创作
- 实现处理层 Agent
- 实现创作层 Agent
- 集成 LLM API

### Week 3: 测试和优化
- 端到端测试
- 性能优化
- 文档编写

**总时长**: 3 周  
**目标**: 完成可演示的 MVP

---

## 🎯 成功指标

### 技术指标
- [ ] 6 个 Agent 协同工作无阻塞
- [ ] 完整事件流可追溯
- [ ] 从采集到生成草稿 < 5 分钟
- [ ] 系统稳定性 > 95%

### 质量指标
- [ ] 摘要质量良好（人工评估）
- [ ] 标签准确率 > 80%
- [ ] 生成文章可读性良好
- [ ] 引用来源准确

### 用户体验指标
- [ ] 用户能独立完成全流程
- [ ] 交互响应及时
- [ ] 错误提示清晰
- [ ] 文档完善易懂

---

## 🛠️ 技术栈

### 核心框架
- **OpenAgents** 0.6.4+ - Agent 网络框架
- **Python** 3.10+ - 开发语言

### Agent 开发
- **OpenAI API** - LLM 服务
- **feedparser** - RSS 解析
- **playwright** - Web 抓取
- **trafilatura** - 内容提取

### 数据存储
- **SQLite** - 框架内置数据库
- **ChromaDB** - 向量搜索（可选）

---

## 📖 使用示例

### 场景 1: 自动采集和处理

```
1. 系统自动每30分钟采集 RSS
2. 用户打开 Studio，查看 #content-feed
3. 看到新文章通知
4. 系统自动生成摘要和标签
5. 内容出现在 #knowledge-base
```

### 场景 2: 手动抓取网页

```
用户: @web-scraper https://example.com/article
Agent: 🔍 开始抓取...
Agent: ✅ 抓取成功！
       📄 GitHub Copilot 技术解析
       📊 2,345 字
```

### 场景 3: 创作文章

```
用户: @outline-generator 生成关于「AI编程」的大纲

Agent: 📋 已生成 3 个方案
       [显示方案 A、B、C]
       
用户: 使用方案 A

用户: @writer-agent 使用方案 A 创作，2000字

Agent: ✍️ 开始创作...
Agent: ✅ 草稿完成！
       📄 从代码补全到智能助手
       📊 2,156 字 | 6 段落 | 5 引用
```

---

## 🔮 未来规划 (v2.0)

### 增强功能
- [ ] 知识图谱可视化
- [ ] 多平台内容适配（小红书、知乎、公众号）
- [ ] 协作编辑（基于 Documents Mod）
- [ ] 语音输入和播客转录
- [ ] 图片和视频素材管理

### 技术优化
- [ ] 本地 LLM 支持
- [ ] 向量数据库优化搜索
- [ ] 实时协作编辑
- [ ] 移动端适配
- [ ] 多用户权限管理

### 生态扩展
- [ ] 插件系统
- [ ] 自定义 Agent 市场
- [ ] 社区模板库
- [ ] API 开放平台

---

## 📝 贡献指南

### 开发流程
1. Fork 项目
2. 创建特性分支
3. 提交代码
4. 发起 Pull Request

### 代码规范
- 使用 Black 格式化
- 类型注解（mypy）
- 单元测试覆盖
- 文档字符串

---

## 📄 许可证

MIT License

---

## 🤝 联系方式

- **项目主页**: [GitHub Repository]
- **问题反馈**: [Issues]
- **讨论社区**: [Discussions]

---

## 🙏 致谢

- OpenAgents 框架团队
- 所有贡献者

---

**最后更新**: 2025-12-27  
**版本**: MVP v1.0