"""
RSS Manager Mod - RSS 源管理
集成到 OpenAgents 框架的网络级 Mod
"""

import sqlite3
import yaml
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


class RSSManagerMod(BaseMod):
    """RSS 源管理 Mod - 提供 RSS 订阅源的管理和状态监控功能"""

    def __init__(self, mod_name: str = "rss_manager"):
        super().__init__(mod_name)
        self.db_path = None
        self.feeds_config_path = None
        self._feeds_cache = None
        self._feeds_cache_time = None

    def initialize(self) -> bool:
        """初始化 mod"""
        self.db_path = self.config.get('db_path', 'data/knowledge-flow/content.db')
        self.feeds_config_path = self.config.get('feeds_config', 'config/rss_feeds.yaml')
        logger.info(f"RSSManagerMod initialized")
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
                name="list_rss_feeds",
                description="列出所有 RSS 订阅源及其状态",
                parameters={"type": "object", "properties": {}, "required": []},
                handler=self._tool_list_feeds
            ),
            AgentTool(
                name="add_rss_feed",
                description="添加新的 RSS 订阅源",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "订阅源名称"},
                        "url": {"type": "string", "description": "RSS URL"},
                        "category": {"type": "string", "description": "分类"},
                        "enabled": {"type": "boolean", "description": "是否启用"}
                    },
                    "required": ["name", "url"]
                },
                handler=self._tool_add_feed
            ),
            AgentTool(
                name="toggle_rss_feed",
                description="启用或禁用 RSS 订阅源",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "订阅源名称"}
                    },
                    "required": ["name"]
                },
                handler=self._tool_toggle_feed
            ),
            AgentTool(
                name="get_rss_dashboard",
                description="获取 RSS 源管理看板",
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

    async def _tool_list_feeds(self, **kwargs) -> List[Dict[str, Any]]:
        return self.get_all_feeds()

    async def _tool_add_feed(self, name: str, url: str, category: str = "tech-news", enabled: bool = True, **kwargs) -> Dict[str, Any]:
        success = self.add_feed({'name': name, 'url': url, 'category': category, 'enabled': enabled})
        return {'success': success, 'message': f"Feed '{name}' added" if success else f"Failed to add feed '{name}'"}

    async def _tool_toggle_feed(self, name: str, **kwargs) -> Dict[str, Any]:
        new_state = self.toggle_feed(name)
        if new_state is not None:
            return {'success': True, 'name': name, 'enabled': new_state}
        return {'success': False, 'message': f"Feed '{name}' not found"}

    async def _tool_get_dashboard(self, format: str = "json", **kwargs) -> Any:
        if format == "text":
            return self.format_dashboard_text()
        return self.get_feed_stats()

    @mod_event_handler("rss.feeds.request")
    async def handle_feeds_request(self, event: Event) -> Optional[EventResponse]:
        """处理 RSS 源请求事件"""
        feeds = self.get_all_feeds()
        return EventResponse(success=True, data={'feeds': feeds})

    @mod_event_handler("rss_manager.feeds.list")
    async def handle_feeds_list(self, event: Event) -> Optional[EventResponse]:
        """列出所有 RSS 源"""
        feeds = self.get_all_feeds()
        return EventResponse(success=True, data={'feeds': feeds, 'total': len(feeds)})

    @mod_event_handler("rss_manager.feeds.add")
    async def handle_feeds_add(self, event: Event) -> Optional[EventResponse]:
        """添加新的 RSS 源"""
        payload = event.payload or {}
        name = payload.get('name')
        url = payload.get('url')
        category = payload.get('category', 'tech-news')
        enabled = payload.get('enabled', True)

        if not name or not url:
            return EventResponse(success=False, data={'error': 'name and url are required'})

        success = self.add_feed({'name': name, 'url': url, 'category': category, 'enabled': enabled})
        return EventResponse(
            success=success,
            data={'message': f"Feed '{name}' added" if success else f"Failed to add feed '{name}'"}
        )

    @mod_event_handler("rss_manager.feeds.toggle")
    async def handle_feeds_toggle(self, event: Event) -> Optional[EventResponse]:
        """切换 RSS 源状态"""
        payload = event.payload or {}
        name = payload.get('name')

        if not name:
            return EventResponse(success=False, data={'error': 'name is required'})

        new_state = self.toggle_feed(name)
        if new_state is not None:
            return EventResponse(success=True, data={'name': name, 'enabled': new_state})
        return EventResponse(success=False, data={'error': f"Feed '{name}' not found"})

    @mod_event_handler("rss_manager.feeds.delete")
    async def handle_feeds_delete(self, event: Event) -> Optional[EventResponse]:
        """删除 RSS 源"""
        payload = event.payload or {}
        name = payload.get('name')

        if not name:
            return EventResponse(success=False, data={'error': 'name is required'})

        success = self.delete_feed(name)
        return EventResponse(
            success=success,
            data={'message': f"Feed '{name}' deleted" if success else f"Feed '{name}' not found"}
        )

    @mod_event_handler("rss_manager.dashboard.get")
    async def handle_dashboard_get(self, event: Event) -> Optional[EventResponse]:
        """获取 RSS 看板"""
        payload = event.payload or {}
        format_type = payload.get('format', 'json')

        if format_type == 'text':
            return EventResponse(success=True, data={'text': self.format_dashboard_text()})
        return EventResponse(success=True, data=self.get_feed_stats())

    @mod_event_handler("rss_manager.stats.get")
    async def handle_stats_get(self, event: Event) -> Optional[EventResponse]:
        """获取 RSS 统计"""
        stats = self.get_feed_stats()
        return EventResponse(success=True, data=stats)

    def _load_feeds_config(self) -> Dict[str, Any]:
        """加载 RSS 配置文件"""
        if self._feeds_cache and self._feeds_cache_time:
            if datetime.now() - self._feeds_cache_time < timedelta(minutes=5):
                return self._feeds_cache

        try:
            config_path = Path(self.feeds_config_path)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._feeds_cache = yaml.safe_load(f)
                    self._feeds_cache_time = datetime.now()
                    return self._feeds_cache
        except Exception as e:
            logger.error(f"Error loading feeds config: {e}")

        return {'feeds': [], 'collection': {}}

    def _save_feeds_config(self, config: Dict[str, Any]) -> bool:
        """保存 RSS 配置文件"""
        try:
            config_path = Path(self.feeds_config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            self._feeds_cache = None
            self._feeds_cache_time = None
            return True
        except Exception as e:
            logger.error(f"Error saving feeds config: {e}")
            return False

    def get_all_feeds(self) -> List[Dict[str, Any]]:
        """获取所有 RSS 源配置"""
        config = self._load_feeds_config()
        feeds = config.get('feeds', [])

        conn = self._get_connection()
        cursor = conn.cursor()

        for feed in feeds:
            feed_name = feed.get('name', '')
            try:
                cursor.execute("SELECT COUNT(*) FROM content_items WHERE source = ?", (feed_name,))
                feed['article_count'] = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT collected_at FROM content_items
                    WHERE source = ? ORDER BY collected_at DESC LIMIT 1
                """, (feed_name,))
                row = cursor.fetchone()
                feed['last_fetch'] = row['collected_at'] if row else None
            except Exception as e:
                logger.error(f"Error getting stats for feed {feed_name}: {e}")
                feed['article_count'] = 0
                feed['last_fetch'] = None

        conn.close()
        return feeds

    def get_feed_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取 RSS 源"""
        feeds = self.get_all_feeds()
        for feed in feeds:
            if feed.get('name') == name:
                return feed
        return None

    def add_feed(self, feed_data: Dict[str, Any]) -> bool:
        """添加新的 RSS 源"""
        config = self._load_feeds_config()
        feeds = config.get('feeds', [])

        for feed in feeds:
            if feed.get('name') == feed_data.get('name'):
                logger.warning(f"Feed already exists: {feed_data.get('name')}")
                return False
            if feed.get('url') == feed_data.get('url'):
                logger.warning(f"Feed URL already exists: {feed_data.get('url')}")
                return False

        new_feed = {
            'name': feed_data.get('name'),
            'url': feed_data.get('url'),
            'category': feed_data.get('category', 'tech-news'),
            'enabled': feed_data.get('enabled', True)
        }
        if feed_data.get('type'):
            new_feed['type'] = feed_data['type']

        feeds.append(new_feed)
        config['feeds'] = feeds
        return self._save_feeds_config(config)

    def update_feed(self, name: str, updates: Dict[str, Any]) -> bool:
        """更新 RSS 源配置"""
        config = self._load_feeds_config()
        feeds = config.get('feeds', [])

        for i, feed in enumerate(feeds):
            if feed.get('name') == name:
                for key, value in updates.items():
                    if key != 'name':
                        feeds[i][key] = value
                config['feeds'] = feeds
                return self._save_feeds_config(config)

        logger.warning(f"Feed not found: {name}")
        return False

    def delete_feed(self, name: str) -> bool:
        """删除 RSS 源"""
        config = self._load_feeds_config()
        feeds = config.get('feeds', [])
        original_count = len(feeds)
        feeds = [f for f in feeds if f.get('name') != name]

        if len(feeds) == original_count:
            logger.warning(f"Feed not found: {name}")
            return False

        config['feeds'] = feeds
        return self._save_feeds_config(config)

    def toggle_feed(self, name: str) -> Optional[bool]:
        """切换 RSS 源启用状态"""
        config = self._load_feeds_config()
        feeds = config.get('feeds', [])

        for i, feed in enumerate(feeds):
            if feed.get('name') == name:
                new_state = not feed.get('enabled', True)
                feeds[i]['enabled'] = new_state
                config['feeds'] = feeds
                if self._save_feeds_config(config):
                    return new_state
                return None
        return None

    def get_collection_config(self) -> Dict[str, Any]:
        """获取采集配置"""
        config = self._load_feeds_config()
        return config.get('collection', {
            'interval': 30, 'max_items_per_feed': 10,
            'content_timeout': 30, 'min_content_length': 200
        })

    def get_feed_stats(self) -> Dict[str, Any]:
        """获取 RSS 源统计信息"""
        feeds = self.get_all_feeds()
        collection_config = self.get_collection_config()

        stats = {
            'total_feeds': len(feeds),
            'enabled_feeds': sum(1 for f in feeds if f.get('enabled', True)),
            'disabled_feeds': sum(1 for f in feeds if not f.get('enabled', True)),
            'by_category': {},
            'total_articles': 0,
            'collection_interval': collection_config.get('interval', 30),
            'feeds': []
        }

        for feed in feeds:
            category = feed.get('category', 'unknown')
            if category not in stats['by_category']:
                stats['by_category'][category] = {'count': 0, 'articles': 0}
            stats['by_category'][category]['count'] += 1
            stats['by_category'][category]['articles'] += feed.get('article_count', 0)
            stats['total_articles'] += feed.get('article_count', 0)

            stats['feeds'].append({
                'name': feed.get('name'),
                'enabled': feed.get('enabled', True),
                'category': category,
                'article_count': feed.get('article_count', 0),
                'last_fetch': feed.get('last_fetch')
            })

        return stats

    def format_dashboard_text(self) -> str:
        """格式化看板为文本输出"""
        stats = self.get_feed_stats()

        lines = [
            "=" * 50, "📡 RSS 源管理看板", "=" * 50, "",
            "📊 总览",
            f"  总订阅源: {stats['total_feeds']}",
            f"  已启用: {stats['enabled_feeds']}",
            f"  已禁用: {stats['disabled_feeds']}",
            f"  总文章数: {stats['total_articles']}",
            f"  采集间隔: {stats['collection_interval']} 分钟",
            "", "📁 按分类",
        ]

        for category, data in stats['by_category'].items():
            lines.append(f"  {category}: {data['count']} 源, {data['articles']} 篇")

        lines.extend(["", "📰 订阅源列表"])

        for feed in stats['feeds']:
            status = "✅" if feed['enabled'] else "❌"
            last_fetch = feed['last_fetch'][:10] if feed['last_fetch'] else "从未"
            lines.append(
                f"  {status} {feed['name'][:25]:<25} | "
                f"{feed['category']:<12} | "
                f"{feed['article_count']:>4} 篇 | "
                f"最近: {last_fetch}"
            )

        lines.extend(["", "=" * 50, f"生成时间: {datetime.now().isoformat()}"])
        return "\n".join(lines)
