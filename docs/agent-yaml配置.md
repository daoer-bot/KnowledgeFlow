深入探索
Agent YAML 配置
报告问题
6 分钟
等级: 进阶
Agent YAML 配置为在 OpenAgents 中定义 agent 行为、模型设置和网络连接提供了一种声明式方法。该配置系统使开发者无需编写代码即可创建具有不同 AI 提供商、自定义行为和特定协议集成的 agent。

配置结构
YAML 配置采用分层结构，包含三个主要部分：

YAML
type: "agent_type"           config:                      # 核心 agent 配置
  # Agent 特定参数
connection:                  # 网络连接设置（可选）
  # 连接参数
mods:                        # Mod 配置（可选）
  # Mod 特定设置
这种结构将关注点分离为 agent 定义、行为配置和网络连接，使管理不同的部署场景变得容易 minimal_agent_config.yaml。

Agent 类型规范
type 字段决定将实例化哪个 agent 类。OpenAgents 支持两种方法：

预定义 Agent 类型
使用简单标识符表示内置 agent 类型：

YAML
type: "simple"  # 使用 SimpleAutoAgent 进行对话式 AI
自定义 Agent 类
为自定义实现指定完全限定类路径：

YAML
type: "my_package.agents.custom_agent.MyCustomAgent"
这种灵活性允许你使用自定义 agent 行为扩展框架，同时保持一致的配置模式 custom_agent_config.yaml。

核心配置参数
config 部分包含定义 agent 行为的基本参数：

必填字段
agent_id：网络中 agent 的唯一标识符
model_name：要使用的 AI 模型名称
instruction：定义 agent 行为和能力的系统提示词
YAML
config:
  agent_id: "claude-assistant-001"
  model_name: "claude-3-5-sonnet-20241022"
  instruction: |
    你是 Claude，一个由 Anthropic 开发的 AI 助手，在 OpenAgents 网络中运行。
    你可以与其他 agent 通信并帮助用户处理各种任务。
    在你的回答中要有帮助、无害和诚实。
提供商配置
OpenAgents 支持多个 AI 提供商并具有自动检测功能：

Provider	Model Examples	Environment Variables
OpenAI	gpt-4o-mini, gpt-4	OPENAI_API_KEY
Claude	claude-3-5-sonnet-20241022	ANTHROPIC_API_KEY
Azure OpenAI	gpt-4, gpt-35-turbo	AZURE_OPENAI_API_KEY
Gemini	gemini-1.5-pro	GOOGLE_API_KEY
DeepSeek	deepseek-chat	DEEPSEEK_API_KEY
你可以显式指定提供商，或让系统根据模型名称或 API 基础 URL 自动检测 claude_agent_config.yaml：

YAML
config:
  provider: "claude"  # 显式提供商规范
  # 或让自动检测处理它
  model_name: "gpt-4o-mini"  # 将检测为 "openai"
API 配置
对于自定义端点或特定提供商配置：

YAML
config:
  api_base: "https://your-resource.openai.azure.com/"  # 自定义端点
  api_key: "your-api-key-here"  # 覆盖环境变量
协议集成
Agent 通过定义其能力和交互模式的协议进行通信：

YAML
config:
  protocol_names:
    - "openagents.mods.communication.simple_messaging"
    - "openagents.mods.discovery.agent_discovery"
常见协议包括：

simple_messaging：agent 之间的基本消息交换
agent_discovery：网络发现和存在公告
workspace_messaging：协作工作区交互
高级配置选项
消息处理控制
微调 agent 对消息的响应方式：

YAML
config:
  react_to_all_messages: false  # 仅响应指定的消息
  ignored_sender_ids:           # 过滤掉特定的 agent
    - "spam-bot"
    - "noisy-agent"
  interval: 1                   # 消息检查间隔（秒）
基于触发器的响应
配置 agent 以响应特定事件：

YAML
config:
  triggers:
    - event: "thread.channel_message.notification"
      instruction: "在被提及时帮助完成 Web 自动化任务"
    - event: "thread.direct_message.notification"
      instruction: "通过直接消息提供帮助"
MCP 服务器集成
连接到模型上下文协议服务器以增强功能：

YAML
config:
  mcps:
    - name: "openmcp_browser"
      type: "streamable_http"
      url: "http://localhost:9000/mcp"
      api_key_env: "OPENMCP_API_KEY"
      timeout: 60
      retry_attempts: 3
连接配置
connection 部分定义网络连接参数：

YAML
connection:
  host: "localhost"
  port: 8570
  network_id: "openagents-network"
这些设置可以在运行时通过命令行参数覆盖，为不同的部署环境提供灵活性 openai_agent_config.yaml。

Mod 配置
对于高级 agent 功能，配置特定的 mods：

YAML
mods:
  - name: "openagents.mods.workspace.messaging"
    enabled: true
    config:
      max_message_history: 1000
      message_retention_days: 30
  - name: "openagents.mods.discovery.agent_discovery"
    enabled: true
    config:
      announce_interval: 60
提供商特定示例
Azure OpenAI 配置
YAML
type: "simple"
config:
  agent_id: "azure-gpt-agent"
  model_name: "gpt-4"  # Azure 部署名称
  provider: "azure"
  api_base: "https://your-resource.openai.azure.com/"
最小配置
最简单的配置只需要三个字段：

YAML
type: "openai"
config:
  agent_id: "minimal-agent"
  model_name: "gpt-3.5-turbo"
  instruction: "你是一个有帮助的 AI 助手。"
配置验证
AgentConfig 类使用 Pydantic 模型提供全面验证 agent_config.py：

模型名称验证：确保非空字符串
API 基础 URL 验证：要求有效的 HTTP/HTTPS URL
模板验证：验证提示词模板格式正确
提供商自动检测：从模型名称和端点智能确定提供商
加载和保存配置
配置系统支持程序化操作：

PYTHON
from openagents.models.agent_config import AgentConfig
 
# 从 YAML 加载
config = AgentConfig.from_yaml("agent_config.yaml")
 
# 保存为 YAML
config.to_yaml("new_config.yaml", include_type=True)
提供常见提供商的工厂函数：

PYTHON
from openagents.models.agent_config import create_openai_config, create_claude_config
 
# 快速配置创建
config = create_openai_config(
    model_name="gpt-4o-mini",
    instruction="你是一个有帮助的助手。"
)
此配置系统为跨不同提供商和用例部署多样化 AI agent 提供了基础，同时在整个 OpenAgents 生态系统中保持一致性和验证。