"""
内容同步工具 - 将 content_items 同步到 Wiki
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ContentSyncTool:
    """将 content_items 数据库内容同步到 Wiki"""

    def __init__(self, db, workspace_client=None):
        """
        初始化同步工具

        Args:
            db: Database 实例
            workspace_client: Workspace 客户端（用于发送 Wiki 事件）
        """
        self.db = db
        self.workspace_client = workspace_client

    async def sync_all_to_wiki(self, limit: int = 100) -> Dict[str, Any]:
        """
        同步所有已处理的内容到 Wiki

        Args:
            limit: 最大同步数量

        Returns:
            同步结果统计
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # 获取已处理但未同步的内容
        cursor.execute("""
            SELECT * FROM content_items
            WHERE status = 'processed'
            ORDER BY collected_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        results = {
            'total': len(rows),
            'synced': 0,
            'failed': 0,
            'skipped': 0
        }

        for row in rows:
            content = self.db._row_to_dict(row)
            try:
                success = await self._sync_content_to_wiki(content)
                if success:
                    results['synced'] += 1
                else:
                    results['skipped'] += 1
            except Exception as e:
                logger.error(f"同步失败: {content.get('title', 'N/A')} - {e}")
                results['failed'] += 1

        logger.info(f"同步完成: {results}")
        return results

    async def _sync_content_to_wiki(self, content: Dict[str, Any]) -> bool:
        """
        同步单条内容到 Wiki

        Args:
            content: 内容数据

        Returns:
            是否成功
        """
        try:
            content_id = content.get('id', '')
            title = content.get('title', 'N/A')
            source = content.get('source', '未知')
            category = content.get('category', 'tech')
            summary = content.get('summary_paragraph', '')
            key_points = content.get('key_points', [])
            tags = content.get('tags', [])
            url = content.get('url', '')
            collected_at = content.get('collected_at', '')

            # 构建 Wiki 页面内容
            wiki_content = f"# {title}\n\n"
            wiki_content += f"**来源**: {source}\n"
            wiki_content += f"**分类**: {category}\n"
            wiki_content += f"**收集时间**: {collected_at}\n"
            if url:
                wiki_content += f"**原文链接**: [{url}]({url})\n"
            wiki_content += "\n---\n\n"

            if summary:
                wiki_content += f"## 摘要\n\n{summary}\n\n"

            if key_points:
                wiki_content += "## 要点\n\n"
                if isinstance(key_points, str):
                    import json
                    try:
                        key_points = json.loads(key_points)
                    except:
                        key_points = [key_points]
                for point in key_points:
                    wiki_content += f"- {point}\n"
                wiki_content += "\n"

            if tags:
                if isinstance(tags, str):
                    import json
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = [tags]
                wiki_content += f"**标签**: {', '.join(tags)}\n"

            # 生成安全的页面路径
            import re
            safe_title = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', title)[:80]
            page_path = f"materials/{category}/{safe_title}"

            # 如果有 workspace_client，通过事件发送
            if self.workspace_client:
                from openagents.models.event import Event
                wiki_event = Event(
                    event_name="wiki.page.create",
                    source_id="content_sync",
                    target_agent_id="mod:openagents.mods.workspace.wiki",
                    payload={
                        "page_path": page_path,
                        "title": title,
                        "wiki_content": wiki_content,
                        "metadata": {
                            "content_id": content_id,
                            "source": source,
                            "category": category
                        }
                    },
                    visibility="network"
                )
                await self.workspace_client.send_event(wiki_event)
                logger.info(f"✅ 已发送 Wiki 同步事件: {title}")
                return True
            else:
                # 直接写入数据库（如果 Wiki mod 不可用）
                logger.warning(f"⚠️ 无 workspace_client，跳过: {title}")
                return False

        except Exception as e:
            logger.error(f"同步内容失败: {e}")
            return False

    def get_sync_status(self) -> Dict[str, int]:
        """获取同步状态统计"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM content_items
            GROUP BY status
        """)

        rows = cursor.fetchall()
        conn.close()

        return {row['status']: row['count'] for row in rows}


async def sync_content_to_wiki_cli():
    """命令行同步工具"""
    import argparse
    from tools.database import get_database

    parser = argparse.ArgumentParser(description="同步 content_items 到 Wiki")
    parser.add_argument("--limit", type=int, default=50, help="最大同步数量")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将要同步的内容")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    db = get_database()
    sync_tool = ContentSyncTool(db)

    if args.dry_run:
        # 仅显示状态
        status = sync_tool.get_sync_status()
        print("\n📊 内容状态统计:")
        for s, count in status.items():
            print(f"  - {s}: {count}")

        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, source, category FROM content_items
            WHERE status = 'processed'
            ORDER BY collected_at DESC
            LIMIT ?
        """, (args.limit,))
        rows = cursor.fetchall()
        conn.close()

        print(f"\n📝 将要同步的内容 (前 {args.limit} 条):")
        for i, row in enumerate(rows, 1):
            print(f"  {i}. [{row['category']}] {row['title'][:50]}... ({row['source']})")
    else:
        print("⚠️ 需要在 Agent 环境中运行才能同步到 Wiki")
        print("💡 请使用 --dry-run 查看将要同步的内容")


if __name__ == "__main__":
    asyncio.run(sync_content_to_wiki_cli())
