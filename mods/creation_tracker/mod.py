"""
Creation Tracker Mod - 创作追踪器
集成到 OpenAgents 框架的网络级 Mod
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from openagents.core.base_mod import BaseMod, mod_event_handler
from openagents.models.messages import Event
from openagents.models.event_response import EventResponse
from openagents.models.tool import AgentTool

logger = logging.getLogger(__name__)


class CreationTrackerMod(BaseMod):
    """创作追踪 Mod - 追踪大纲和草稿的创作进度"""

    def __init__(self, mod_name: str = "creation_tracker"):
        super().__init__(mod_name)
        self.db_path = None

    def initialize(self) -> bool:
        """初始化 mod"""
        self.db_path = self.config.get('db_path', 'data/knowledge-flow/content.db')
        logger.info(f"CreationTrackerMod initialized with db: {self.db_path}")
        return True

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_tools(self) -> List[AgentTool]:
        """提供 MCP 工具"""
        return [
            AgentTool(
                name="get_creation_stats",
                description="获取创作统计信息，包括大纲和草稿数量",
                parameters={"type": "object", "properties": {}, "required": []},
                handler=self._tool_get_stats
            ),
            AgentTool(
                name="list_recent_outlines",
                description="列出最近的大纲",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "返回数量", "default": 10}
                    },
                    "required": []
                },
                handler=self._tool_list_outlines
            ),
            AgentTool(
                name="list_recent_drafts",
                description="列出最近的草稿",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "返回数量", "default": 10}
                    },
                    "required": []
                },
                handler=self._tool_list_drafts
            ),
            AgentTool(
                name="get_creation_dashboard",
                description="获取创作追踪看板",
                parameters={
                    "type": "object",
                    "properties": {
                        "format": {"type": "string", "enum": ["json", "text"]}
                    },
                    "required": []
                },
                handler=self._tool_get_dashboard
            )
        ]

    async def _tool_get_stats(self, **kwargs) -> Dict[str, Any]:
        return self.get_creation_pipeline()

    async def _tool_list_outlines(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        return self.get_recent_outlines(limit)

    async def _tool_list_drafts(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        return self.get_recent_drafts(limit)

    async def _tool_get_dashboard(self, format: str = "json", **kwargs) -> Any:
        if format == "text":
            return self.format_dashboard_text()
        return self.get_dashboard_data()

    @mod_event_handler("creation.stats.request")
    async def handle_stats_request(self, event: Event) -> Optional[EventResponse]:
        """处理创作统计请求事件"""
        stats = self.get_creation_pipeline()
        return EventResponse(success=True, data=stats)

    @mod_event_handler("creation_tracker.pipeline.get")
    async def handle_pipeline_get(self, event: Event) -> Optional[EventResponse]:
        """获取创作流水线状态"""
        pipeline = self.get_creation_pipeline()
        return EventResponse(success=True, data=pipeline)

    @mod_event_handler("creation_tracker.outlines.list")
    async def handle_outlines_list(self, event: Event) -> Optional[EventResponse]:
        """列出最近大纲"""
        payload = event.payload or {}
        limit = payload.get('limit', 10)
        outlines = self.get_recent_outlines(limit)
        return EventResponse(success=True, data={'outlines': outlines, 'total': len(outlines)})

    @mod_event_handler("creation_tracker.outlines.stats")
    async def handle_outlines_stats(self, event: Event) -> Optional[EventResponse]:
        """获取大纲统计"""
        stats = self.get_outlines_stats()
        return EventResponse(success=True, data=stats)

    @mod_event_handler("creation_tracker.drafts.list")
    async def handle_drafts_list(self, event: Event) -> Optional[EventResponse]:
        """列出最近草稿"""
        payload = event.payload or {}
        limit = payload.get('limit', 10)
        drafts = self.get_recent_drafts(limit)
        return EventResponse(success=True, data={'drafts': drafts, 'total': len(drafts)})

    @mod_event_handler("creation_tracker.drafts.stats")
    async def handle_drafts_stats(self, event: Event) -> Optional[EventResponse]:
        """获取草稿统计"""
        stats = self.get_drafts_stats()
        return EventResponse(success=True, data=stats)

    @mod_event_handler("creation_tracker.dashboard.get")
    async def handle_dashboard_get(self, event: Event) -> Optional[EventResponse]:
        """获取创作看板"""
        payload = event.payload or {}
        format_type = payload.get('format', 'json')

        if format_type == 'text':
            return EventResponse(success=True, data={'text': self.format_dashboard_text()})
        return EventResponse(success=True, data=self.get_dashboard_data())

    @mod_event_handler("creation_tracker.daily.get")
    async def handle_daily_get(self, event: Event) -> Optional[EventResponse]:
        """获取每日创作统计"""
        payload = event.payload or {}
        days = payload.get('days', 7)
        daily = self.get_daily_creation_stats(days)
        return EventResponse(success=True, data={'daily': daily})

    def get_outlines_stats(self) -> Dict[str, Any]:
        """获取大纲统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        stats = {'total': 0, 'selected': 0, 'pending': 0, 'by_style': {}, 'recent_7d': 0}

        try:
            cursor.execute("SELECT COUNT(*) FROM outlines")
            stats['total'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM outlines WHERE selected = 1")
            stats['selected'] = cursor.fetchone()[0]
            stats['pending'] = stats['total'] - stats['selected']

            cursor.execute("""
                SELECT style, COUNT(*) as count FROM outlines
                WHERE style IS NOT NULL GROUP BY style
            """)
            stats['by_style'] = {row['style']: row['count'] for row in cursor.fetchall()}

            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM outlines WHERE created_at >= ?", (week_ago,))
            stats['recent_7d'] = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting outlines stats: {e}")
        finally:
            conn.close()

        return stats

    def get_drafts_stats(self) -> Dict[str, Any]:
        """获取草稿统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        stats = {'total': 0, 'by_status': {}, 'total_words': 0, 'avg_words': 0, 'recent_7d': 0}

        try:
            cursor.execute("SELECT COUNT(*) FROM drafts")
            stats['total'] = cursor.fetchone()[0]

            cursor.execute("SELECT status, COUNT(*) as count FROM drafts GROUP BY status")
            stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

            cursor.execute("SELECT SUM(word_count), AVG(word_count) FROM drafts")
            row = cursor.fetchone()
            stats['total_words'] = row[0] or 0
            stats['avg_words'] = round(row[1] or 0)

            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM drafts WHERE created_at >= ?", (week_ago,))
            stats['recent_7d'] = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting drafts stats: {e}")
        finally:
            conn.close()

        return stats

    def get_recent_outlines(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的大纲"""
        conn = self._get_connection()
        cursor = conn.cursor()
        outlines = []

        try:
            cursor.execute("""
                SELECT id, topic, style, selected, created_at
                FROM outlines ORDER BY created_at DESC LIMIT ?
            """, (limit,))

            for row in cursor.fetchall():
                outlines.append({
                    'id': row['id'],
                    'topic': row['topic'],
                    'style': row['style'],
                    'selected': bool(row['selected']),
                    'created_at': row['created_at']
                })
        except Exception as e:
            logger.error(f"Error getting recent outlines: {e}")
        finally:
            conn.close()

        return outlines

    def get_recent_drafts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的草稿"""
        conn = self._get_connection()
        cursor = conn.cursor()
        drafts = []

        try:
            cursor.execute("""
                SELECT d.id, d.title, d.word_count, d.status, d.created_at, d.updated_at,
                       o.topic as outline_topic
                FROM drafts d LEFT JOIN outlines o ON d.outline_id = o.id
                ORDER BY d.updated_at DESC LIMIT ?
            """, (limit,))

            for row in cursor.fetchall():
                drafts.append({
                    'id': row['id'],
                    'title': row['title'],
                    'word_count': row['word_count'],
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'outline_topic': row['outline_topic']
                })
        except Exception as e:
            logger.error(f"Error getting recent drafts: {e}")
        finally:
            conn.close()

        return drafts

    def get_outline_detail(self, outline_id: str) -> Optional[Dict[str, Any]]:
        """获取大纲详情"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM outlines WHERE id = ?", (outline_id,))
            row = cursor.fetchone()

            if row:
                outline = dict(row)
                if outline.get('content'):
                    try:
                        outline['content'] = json.loads(outline['content'])
                    except:
                        pass
                if outline.get('related_content_ids'):
                    try:
                        outline['related_content_ids'] = json.loads(outline['related_content_ids'])
                    except:
                        pass

                cursor.execute("""
                    SELECT id, title, status, word_count, created_at
                    FROM drafts WHERE outline_id = ?
                """, (outline_id,))
                outline['drafts'] = [dict(r) for r in cursor.fetchall()]
                return outline
        except Exception as e:
            logger.error(f"Error getting outline detail: {e}")
        finally:
            conn.close()

        return None

    def get_draft_detail(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """获取草稿详情"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT d.*, o.topic as outline_topic, o.style as outline_style
                FROM drafts d LEFT JOIN outlines o ON d.outline_id = o.id
                WHERE d.id = ?
            """, (draft_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        except Exception as e:
            logger.error(f"Error getting draft detail: {e}")
        finally:
            conn.close()

        return None

    def get_creation_pipeline(self) -> Dict[str, Any]:
        """获取创作流水线状态"""
        outlines_stats = self.get_outlines_stats()
        drafts_stats = self.get_drafts_stats()

        return {
            'outlines': {
                'total': outlines_stats['total'],
                'pending_selection': outlines_stats['pending'],
                'selected': outlines_stats['selected']
            },
            'drafts': {
                'total': drafts_stats['total'],
                'draft': drafts_stats['by_status'].get('draft', 0),
                'reviewed': drafts_stats['by_status'].get('reviewed', 0),
                'published': drafts_stats['by_status'].get('published', 0)
            },
            'productivity': {
                'outlines_7d': outlines_stats['recent_7d'],
                'drafts_7d': drafts_stats['recent_7d'],
                'total_words': drafts_stats['total_words'],
                'avg_words_per_draft': drafts_stats['avg_words']
            }
        }

    def get_daily_creation_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取每日创作统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        daily_stats = []
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM outlines WHERE created_at >= ?
                GROUP BY DATE(created_at)
            """, (start_date,))
            outlines_by_date = {row['date']: row['count'] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count, SUM(word_count) as words
                FROM drafts WHERE created_at >= ?
                GROUP BY DATE(created_at)
            """, (start_date,))
            drafts_by_date = {row['date']: {'count': row['count'], 'words': row['words'] or 0}
                             for row in cursor.fetchall()}

            all_dates = set(outlines_by_date.keys()) | set(drafts_by_date.keys())
            for date in sorted(all_dates, reverse=True):
                daily_stats.append({
                    'date': date,
                    'outlines': outlines_by_date.get(date, 0),
                    'drafts': drafts_by_date.get(date, {}).get('count', 0),
                    'words': drafts_by_date.get(date, {}).get('words', 0)
                })
        except Exception as e:
            logger.error(f"Error getting daily creation stats: {e}")
        finally:
            conn.close()

        return daily_stats

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取完整的看板数据"""
        return {
            'outlines': self.get_outlines_stats(),
            'drafts': self.get_drafts_stats(),
            'pipeline': self.get_creation_pipeline(),
            'daily': self.get_daily_creation_stats(7),
            'recent_outlines': self.get_recent_outlines(5),
            'recent_drafts': self.get_recent_drafts(5),
            'generated_at': datetime.now().isoformat()
        }

    def format_dashboard_text(self) -> str:
        """格式化看板为文本输出"""
        data = self.get_dashboard_data()
        outlines = data['outlines']
        drafts = data['drafts']
        pipeline = data['pipeline']

        lines = [
            "=" * 50, "✍️ 创作追踪看板", "=" * 50, "",
            "📝 大纲统计",
            f"  总数: {outlines['total']}",
            f"  已选择: {outlines['selected']}",
            f"  待选择: {outlines['pending']}",
            f"  近7天: {outlines['recent_7d']}",
            "",
            "📄 草稿统计",
            f"  总数: {drafts['total']}",
            f"  草稿中: {drafts['by_status'].get('draft', 0)}",
            f"  已审核: {drafts['by_status'].get('reviewed', 0)}",
            f"  已发布: {drafts['by_status'].get('published', 0)}",
            f"  近7天: {drafts['recent_7d']}",
            "",
            "📊 生产力",
            f"  总字数: {pipeline['productivity']['total_words']:,}",
            f"  平均字数: {pipeline['productivity']['avg_words_per_draft']}",
            "",
        ]

        if data['recent_outlines']:
            lines.append("📋 最近大纲")
            for outline in data['recent_outlines'][:3]:
                status = "✅" if outline['selected'] else "⏳"
                lines.append(f"  {status} {outline['topic'][:35]}...")

        lines.append("")

        if data['recent_drafts']:
            lines.append("📝 最近草稿")
            for draft in data['recent_drafts'][:3]:
                status_icon = {'draft': '📝', 'reviewed': '✔️', 'published': '🎉'}.get(draft['status'], '❓')
                lines.append(f"  {status_icon} {draft['title'][:30]}... ({draft['word_count']} 字)")

        lines.extend(["", "=" * 50, f"生成时间: {data['generated_at']}"])
        return "\n".join(lines)
