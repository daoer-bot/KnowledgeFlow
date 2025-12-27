"""
RSS Manager Adapter - Agent 客户端适配器
提供给 Agent 使用的 RSS 管理工具
"""

import logging
from typing import Dict, Any, List, Optional

from openagents.core.base_mod_adapter import BaseModAdapter
from openagents.models.tool import AgentTool

logger = logging.getLogger(__name__)


class RSSManagerAdapter(BaseModAdapter):
    """RSS Manager Agent Adapter - 提供 RSS 源管理工具"""

    def __init__(self):
        super().__init__(mod_name="mods.rss_manager")

    def initialize(self) -> bool:
        logger.info(f"RSSManagerAdapter initialized for agent {self.agent_id}")
        return True

    def get_tools(self) -> List[AgentTool]:
        """提供给 Agent 的工具"""
        return [
            AgentTool(
                name="list_rss_feeds",
                description="列出所有 RSS 订阅源及其状态（文章数、最后抓取时间等）",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                func=self._list_feeds
            ),
            AgentTool(
                name="add_rss_feed",
                description="添加新的 RSS 订阅源",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "订阅源名称"
                        },
                        "url": {
                            "type": "string",
                            "description": "RSS URL"
                        },
                        "category": {
                            "type": "string",
                            "description": "分类",
                            "default": "tech-news"
                        },
                        "enabled": {
                            "type": "boolean",
                            "description": "是否启用",
                            "default": True
                        }
                    },
                    "required": ["name", "url"]
                },
                func=self._add_feed
            ),
            AgentTool(
                name="toggle_rss_feed",
                description="启用或禁用 RSS 订阅源",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "订阅源名称"
                        }
                    },
                    "required": ["name"]
                },
                func=self._toggle_feed
            ),
            AgentTool(
                name="get_rss_dashboard",
                description="获取 RSS 源管理看板，包括统计信息和源列表",
                input_schema={
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["json", "text"],
                            "description": "输出格式",
                            "default": "json"
                        }
                    },
                    "required": []
                },
                func=self._get_dashboard
            )
        ]

    async def _list_feeds(self, **kwargs) -> Dict[str, Any]:
        """列出所有 RSS 源"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="rss.feeds.request",
            source_id=self.agent_id,
            relevant_mod="mods.rss_manager",
            visibility=EventVisibility.MOD_ONLY,
            payload={"action": "list"}
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": "RSS 源列表请求已发送"}

    async def _add_feed(self, name: str, url: str, category: str = "tech-news", enabled: bool = True, **kwargs) -> Dict[str, Any]:
        """添加新的 RSS 源"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="rss.feeds.request",
            source_id=self.agent_id,
            relevant_mod="mods.rss_manager",
            visibility=EventVisibility.MOD_ONLY,
            payload={
                "action": "add",
                "name": name,
                "url": url,
                "category": category,
                "enabled": enabled
            }
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": f"添加 RSS 源 '{name}' 请求已发送"}

    async def _toggle_feed(self, name: str, **kwargs) -> Dict[str, Any]:
        """切换 RSS 源状态"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="rss.feeds.request",
            source_id=self.agent_id,
            relevant_mod="mods.rss_manager",
            visibility=EventVisibility.MOD_ONLY,
            payload={"action": "toggle", "name": name}
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": f"切换 RSS 源 '{name}' 状态请求已发送"}

    async def _get_dashboard(self, format: str = "json", **kwargs) -> Dict[str, Any]:
        """获取 RSS 看板"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="rss.feeds.request",
            source_id=self.agent_id,
            relevant_mod="mods.rss_manager",
            visibility=EventVisibility.MOD_ONLY,
            payload={"action": "dashboard", "format": format}
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": "RSS 看板请求已发送"}
