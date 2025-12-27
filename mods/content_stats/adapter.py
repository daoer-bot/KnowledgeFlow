"""
Content Stats Adapter - Agent 客户端适配器
提供给 Agent 使用的统计工具
"""

import logging
from typing import Dict, Any, List

from openagents.core.base_mod_adapter import BaseModAdapter
from openagents.models.tool import AgentTool

logger = logging.getLogger(__name__)


class ContentStatsAdapter(BaseModAdapter):
    """Content Stats Agent Adapter - 提供文章统计工具"""

    def __init__(self):
        super().__init__(mod_name="mods.content_stats")

    def initialize(self) -> bool:
        logger.info(f"ContentStatsAdapter initialized for agent {self.agent_id}")
        return True

    def get_tools(self) -> List[AgentTool]:
        """提供给 Agent 的工具"""
        return [
            AgentTool(
                name="get_content_stats",
                description="获取文章统计信息，包括总数、分类、来源、处理状态等",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                func=self._get_stats
            ),
            AgentTool(
                name="get_content_dashboard",
                description="获取完整的文章统计看板，包括每日统计、热门标签、最近文章等",
                input_schema={
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["json", "text"],
                            "description": "输出格式，json 或 text",
                            "default": "json"
                        }
                    },
                    "required": []
                },
                func=self._get_dashboard
            )
        ]

    async def _get_stats(self, **kwargs) -> Dict[str, Any]:
        """获取统计信息 - 通过事件请求网络 mod"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="content.stats.request",
            source_id=self.agent_id,
            relevant_mod="mods.content_stats",
            visibility=EventVisibility.MOD_ONLY,
            payload={"action": "get_overview"}
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": "统计请求已发送，等待响应"}

    async def _get_dashboard(self, format: str = "json", **kwargs) -> Dict[str, Any]:
        """获取看板数据 - 通过事件请求网络 mod"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="content.stats.request",
            source_id=self.agent_id,
            relevant_mod="mods.content_stats",
            visibility=EventVisibility.MOD_ONLY,
            payload={"action": "get_dashboard", "format": format}
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": "看板请求已发送，等待响应"}
