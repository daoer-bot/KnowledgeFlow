"""
Content Stats Mod - 文章统计看板
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


class ContentStatsMod(BaseMod):
    """文章统计 Mod - 提供文章收集和处理的统计信息"""

    def __init__(self, mod_name: str = "content_stats"):
        super().__init__(mod_name)
        self.db_path = None

    def initialize(self) -> bool:
        """初始化 mod"""
        self.db_path = self.config.get('db_path', 'data/knowledge-flow/content.db')
        logger.info(f"ContentStatsMod initialized with db: {self.db_path}")
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
                name="get_content_stats",
                description="获取文章统计信息，包括总数、分类、来源等",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                handler=self._tool_get_stats
            ),
            AgentTool(
                name="get_content_dashboard",
                description="获取完整的文章统计看板数据",
                parameters={
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["json", "text"],
                            "description": "输出格式，json 或 text"
                        }
                    },
                    "required": []
                },
                handler=self._tool_get_dashboard
            )
        ]

    async def _tool_get_stats(self, **kwargs) -> Dict[str, Any]:
        """工具：获取统计信息"""
        return self.get_overview_stats()

    async def _tool_get_dashboard(self, format: str = "json", **kwargs) -> Any:
        """工具：获取看板数据"""
        if format == "text":
            return self.format_dashboard_text()
        return self.get_dashboard_data()

    @mod_event_handler("content.stats.request")
    async def handle_stats_request(self, event: Event) -> Optional[EventResponse]:
        """处理统计请求事件"""
        stats = self.get_overview_stats()
        return EventResponse(
            success=True,
            data=stats
        )

    @mod_event_handler("content_stats.overview.get")
    async def handle_overview_get(self, event: Event) -> Optional[EventResponse]:
        """获取总览统计"""
        stats = self.get_overview_stats()
        return EventResponse(
            success=True,
            data={"overview": stats}
        )

    @mod_event_handler("content_stats.dashboard.get")
    async def handle_dashboard_get(self, event: Event) -> Optional[EventResponse]:
        """获取完整看板数据"""
        format_type = event.payload.get("format", "json") if event.payload else "json"
        if format_type == "text":
            return EventResponse(
                success=True,
                data={"text": self.format_dashboard_text()}
            )
        return EventResponse(
            success=True,
            data=self.get_dashboard_data()
        )

    @mod_event_handler("content_stats.daily.get")
    async def handle_daily_get(self, event: Event) -> Optional[EventResponse]:
        """获取每日统计"""
        days = event.payload.get("days", 7) if event.payload else 7
        daily = self.get_daily_stats(days)
        return EventResponse(
            success=True,
            data={"daily": daily}
        )

    @mod_event_handler("content_stats.tags.get")
    async def handle_tags_get(self, event: Event) -> Optional[EventResponse]:
        """获取热门标签"""
        limit = event.payload.get("limit", 20) if event.payload else 20
        tags = self.get_top_tags(limit)
        return EventResponse(
            success=True,
            data={"tags": tags}
        )

    @mod_event_handler("content_stats.articles.recent")
    async def handle_articles_recent(self, event: Event) -> Optional[EventResponse]:
        """获取最近文章"""
        limit = event.payload.get("limit", 10) if event.payload else 10
        articles = self.get_recent_articles(limit)
        return EventResponse(
            success=True,
            data={"articles": articles}
        )

    @mod_event_handler("content_stats.pipeline.get")
    async def handle_pipeline_get(self, event: Event) -> Optional[EventResponse]:
        """获取处理流水线统计"""
        pipeline = self.get_processing_pipeline_stats()
        return EventResponse(
            success=True,
            data={"pipeline": pipeline}
        )

    def get_overview_stats(self) -> Dict[str, Any]:
        """获取总览统计"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {
            'total_articles': 0,
            'by_status': {},
            'by_source': {},
            'by_category': {},
            'by_sentiment': {},
            'recent_24h': 0,
            'recent_7d': 0,
            'avg_relevance_score': 0,
            'last_updated': datetime.now().isoformat()
        }

        try:
            cursor.execute("SELECT COUNT(*) FROM content_items")
            stats['total_articles'] = cursor.fetchone()[0]

            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM content_items GROUP BY status
            """)
            stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM content_items GROUP BY source
                ORDER BY count DESC LIMIT 10
            """)
            stats['by_source'] = {row['source'] or 'Unknown': row['count'] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM content_items WHERE category IS NOT NULL
                GROUP BY category ORDER BY count DESC
            """)
            stats['by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT sentiment, COUNT(*) as count
                FROM content_items WHERE sentiment IS NOT NULL
                GROUP BY sentiment
            """)
            stats['by_sentiment'] = {row['sentiment']: row['count'] for row in cursor.fetchall()}

            yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM content_items WHERE collected_at >= ?", (yesterday,))
            stats['recent_24h'] = cursor.fetchone()[0]

            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM content_items WHERE collected_at >= ?", (week_ago,))
            stats['recent_7d'] = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(relevance_score) FROM content_items WHERE relevance_score IS NOT NULL")
            avg_score = cursor.fetchone()[0]
            stats['avg_relevance_score'] = round(avg_score, 2) if avg_score else 0

        except Exception as e:
            logger.error(f"Error getting overview stats: {e}")
        finally:
            conn.close()

        return stats

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取每日统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        daily_stats = []

        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT DATE(collected_at) as date, COUNT(*) as count,
                    COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed,
                    COUNT(CASE WHEN status = 'summarized' THEN 1 END) as summarized,
                    COUNT(CASE WHEN status = 'discovered' THEN 1 END) as discovered
                FROM content_items WHERE collected_at >= ?
                GROUP BY DATE(collected_at) ORDER BY date DESC
            """, (start_date,))

            for row in cursor.fetchall():
                daily_stats.append({
                    'date': row['date'],
                    'total': row['count'],
                    'processed': row['processed'],
                    'summarized': row['summarized'],
                    'discovered': row['discovered']
                })
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
        finally:
            conn.close()

        return daily_stats

    def get_top_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门标签"""
        conn = self._get_connection()
        cursor = conn.cursor()
        tag_counts = {}

        try:
            cursor.execute("SELECT tags FROM content_items WHERE tags IS NOT NULL AND tags != ''")
            for row in cursor.fetchall():
                try:
                    tags_data = json.loads(row['tags']) if row['tags'] else {}
                    if isinstance(tags_data, dict):
                        for tag_type, tags in tags_data.items():
                            if isinstance(tags, list):
                                for tag in tags:
                                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    elif isinstance(tags_data, list):
                        for tag in tags_data:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except:
                    pass
        except Exception as e:
            logger.error(f"Error getting top tags: {e}")
        finally:
            conn.close()

        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{'tag': tag, 'count': count} for tag, count in sorted_tags]

    def get_recent_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的文章"""
        conn = self._get_connection()
        cursor = conn.cursor()
        articles = []

        try:
            cursor.execute("""
                SELECT id, title, source, category, status,
                    summary_one_line, relevance_score, collected_at
                FROM content_items ORDER BY collected_at DESC LIMIT ?
            """, (limit,))

            for row in cursor.fetchall():
                articles.append({
                    'id': row['id'],
                    'title': row['title'],
                    'source': row['source'],
                    'category': row['category'],
                    'status': row['status'],
                    'summary': row['summary_one_line'],
                    'relevance_score': row['relevance_score'],
                    'collected_at': row['collected_at']
                })
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
        finally:
            conn.close()

        return articles

    def get_processing_pipeline_stats(self) -> Dict[str, Any]:
        """获取处理流水线统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        pipeline_stats = {'discovered': 0, 'summarized': 0, 'processed': 0, 'pending_summary': 0, 'pending_tags': 0}

        try:
            cursor.execute("SELECT status, COUNT(*) as count FROM content_items GROUP BY status")
            for row in cursor.fetchall():
                if row['status'] in pipeline_stats:
                    pipeline_stats[row['status']] = row['count']
            pipeline_stats['pending_summary'] = pipeline_stats.get('discovered', 0)
            pipeline_stats['pending_tags'] = pipeline_stats.get('summarized', 0)
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
        finally:
            conn.close()

        return pipeline_stats

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取完整的看板数据"""
        return {
            'overview': self.get_overview_stats(),
            'daily': self.get_daily_stats(7),
            'top_tags': self.get_top_tags(15),
            'recent_articles': self.get_recent_articles(10),
            'pipeline': self.get_processing_pipeline_stats(),
            'generated_at': datetime.now().isoformat()
        }

    def format_dashboard_text(self) -> str:
        """格式化看板为文本输出"""
        data = self.get_dashboard_data()
        overview = data['overview']
        pipeline = data['pipeline']

        lines = [
            "=" * 50, "📊 文章统计看板", "=" * 50, "",
            "📈 总览",
            f"  总文章数: {overview['total_articles']}",
            f"  最近24小时: {overview['recent_24h']}",
            f"  最近7天: {overview['recent_7d']}",
            f"  平均相关性: {overview['avg_relevance_score']}",
            "",
            "🔄 处理流水线",
            f"  已发现: {pipeline['discovered']}",
            f"  已摘要: {pipeline['summarized']}",
            f"  已处理: {pipeline['processed']}",
            f"  待摘要: {pipeline['pending_summary']}",
            f"  待标签: {pipeline['pending_tags']}",
            "",
        ]

        if overview['by_source']:
            lines.append("📰 按来源")
            for source, count in list(overview['by_source'].items())[:5]:
                lines.append(f"  {source}: {count}")
            lines.append("")

        if overview['by_category']:
            lines.append("📁 按分类")
            for category, count in list(overview['by_category'].items())[:5]:
                lines.append(f"  {category}: {count}")
            lines.append("")

        if data['top_tags']:
            lines.append("🏷️ 热门标签")
            tags_str = ", ".join([f"{t['tag']}({t['count']})" for t in data['top_tags'][:10]])
            lines.append(f"  {tags_str}")
            lines.append("")

        if data['recent_articles']:
            lines.append("📄 最近文章")
            for article in data['recent_articles'][:5]:
                status_icon = {'discovered': '🔍', 'summarized': '📝', 'processed': '✅'}.get(article['status'], '❓')
                lines.append(f"  {status_icon} {article['title'][:40]}...")
            lines.append("")

        lines.extend(["=" * 50, f"生成时间: {data['generated_at']}"])
        return "\n".join(lines)
