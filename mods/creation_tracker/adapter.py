"""
Creation Tracker Adapter - Agent 客户端适配器
提供给 Agent 使用的创作追踪工具
"""

import logging
from typing import Dict, Any, List

from openagents.core.base_mod_adapter import BaseModAdapter
from openagents.models.tool import AgentTool

logger = logging.getLogger(__name__)


class CreationTrackerAdapter(BaseModAdapter):
    """Creation Tracker Agent Adapter - 提供创作追踪工具"""

    def __init__(self):
        super().__init__(mod_name="mods.creation_tracker")

    def initialize(self) -> bool:
        logger.info(f"CreationTrackerAdapter initialized for agent {self.agent_id}")
        return True

    def get_tools(self) -> List[AgentTool]:
        """提供给 Agent 的工具"""
        return [
            AgentTool(
                name="get_creation_stats",
                description="获取创作统计信息，包括大纲和草稿数量、状态分布等",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                func=self._get_stats
            ),
            AgentTool(
                name="list_recent_outlines",
                description="列出最近的大纲",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "返回数量",
                            "default": 10
                        }
                    },
                    "required": []
                },
                func=self._list_outlines
            ),
            AgentTool(
                name="list_recent_drafts",
                description="列出最近的草稿",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "返回数量",
                            "default": 10
                        }
                    },
                    "required": []
                },
                func=self._list_drafts
            ),
            AgentTool(
                name="get_creation_dashboard",
                description="获取创作追踪看板，包括大纲、草稿统计和生产力数据",
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

    async def _get_stats(self, **kwargs) -> Dict[str, Any]:
        """获取创作统计"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="creation.stats.request",
            source_id=self.agent_id,
            relevant_mod="mods.creation_tracker",
            visibility=EventVisibility.MOD_ONLY,
            payload={"action": "get_pipeline"}
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": "创作统计请求已发送"}

    async def _list_outlines(self, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """列出最近大纲"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="creation.stats.request",
            source_id=self.agent_id,
            relevant_mod="mods.creation_tracker",
            visibility=EventVisibility.MOD_ONLY,
            payload={"action": "list_outlines", "limit": limit}
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": "大纲列表请求已发送"}

    async def _list_drafts(self, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """列出最近草稿"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="creation.stats.request",
            source_id=self.agent_id,
            relevant_mod="mods.creation_tracker",
            visibility=EventVisibility.MOD_ONLY,
            payload={"action": "list_drafts", "limit": limit}
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": "草稿列表请求已发送"}

    async def _get_dashboard(self, format: str = "json", **kwargs) -> Dict[str, Any]:
        """获取创作看板"""
        from openagents.models.event import Event, EventVisibility

        event = Event(
            event_name="creation.stats.request",
            source_id=self.agent_id,
            relevant_mod="mods.creation_tracker",
            visibility=EventVisibility.MOD_ONLY,
            payload={"action": "get_dashboard", "format": format}
        )

        await self.agent_client.send_event(event)
        return {"status": "request_sent", "message": "创作看板请求已发送"}
