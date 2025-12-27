#!/usr/bin/env python3
"""
RSS Reader Agent - 自动采集 RSS 订阅源的内容

功能：
- 定时从配置的 RSS 源采集文章
- 提取全文内容
- 去重检查
- 发送 content.discovered 事件
- 发送消息到 content-feed 频道
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from openagents.agents.worker_agent import WorkerAgent
from openagents.models.event import Event
from tools.content_tools import get_rss_reader
from tools.database import get_database
import logging

logger = logging.getLogger(__name__)


class RSSReaderAgent(WorkerAgent):
    """RSS Reader Agent - 自动采集内容"""
    
    default_agent_id = "RSS阅读器"
    
    def __init__(self, fetch_interval: int = 10, **kwargs):
        """
        初始化 RSS Reader Agent
        
        Args:
            fetch_interval: 采集间隔（秒，默认30分钟）
        """
        super().__init__(**kwargs)
        self.fetch_interval = fetch_interval
        self.rss_reader = get_rss_reader()
        self.db = get_database()
        self._fetch_task = None
    
    async def on_startup(self):
        """Agent 启动时执行"""
        logger.info(f"📰 RSS采集器 启动 (采集间隔: {self.fetch_interval}秒)")
        
        # 发送上线通知
        await self._send_channel_message(
            "通用频道",
            "🤖 RSS采集器 已上线，开始自动采集内容..."
        )
        
        # 启动定时采集任务
        self._fetch_task = asyncio.create_task(self._fetch_loop())
    
    async def on_shutdown(self):
        """Agent 关闭时执行"""
        if self._fetch_task:
            self._fetch_task.cancel()
            try:
                await self._fetch_task
            except asyncio.CancelledError:
                pass
        
        logger.info("📰 RSS采集器 已停止")
    
    async def _fetch_loop(self):
        """定时采集循环"""
        # 等待初始化完成
        await asyncio.sleep(5)
        
        while True:
            try:
                await self._fetch_and_process()
            except Exception as e:
                logger.error(f"Error in fetch loop: {str(e)}")
            
            # 等待下一次采集
            await asyncio.sleep(self.fetch_interval)
    
    async def _fetch_and_process(self):
        """采集并处理内容"""
        logger.info("Starting RSS feed collection...")
        
        # 采集所有RSS源
        items = self.rss_reader.fetch_all_feeds()
        
        if not items:
            logger.info("No new items fetched")
            return
        
        # 处理每个条目
        new_count = 0
        for item in items:
            # 检查是否已存在
            if item.get('url') and self.db.check_url_exists(item['url']):
                continue
            
            # 检查内容长度
            content = item.get('content', item.get('summary', ''))
            if len(content) < 200:
                logger.debug(f"Skipping short content: {item.get('title')}")
                continue
            
            # 保存到数据库
            content_data = {
                'title': item['title'],
                'url': item.get('url'),
                'raw_content': content,
                'source': item.get('source'),
                'source_type': 'rss'
            }
            
            content_id = self.db.add_content(content_data)
            
            if content_id:
                new_count += 1
                
                # 发送事件
                await self._emit_content_discovered(content_id, content_data)
                
                # 发送频道消息
                await self._notify_new_content(content_data)
                
                # 小延迟避免过快
                await asyncio.sleep(1)
        
        logger.info(f"RSS collection completed: {new_count} new items added")
        
        if new_count > 0:
            await self._send_channel_message(
                "通用频道",
                f"📥 RSS 采集完成：新增 {new_count} 篇内容"
            )
    
    async def _emit_content_discovered(self, content_id: str, content_data: dict):
        """发送 content.discovered 事件"""
        try:
            # 发送事件通知其他 Agent
            event = Event(
                event_name="content.discovered",
                source_id=self.agent_id,
                payload={
                    "content_id": content_id,
                    "title": content_data.get('title'),
                    "url": content_data.get('url'),
                    "source": content_data.get('source'),
                    "source_type": content_data.get('source_type')
                }
            )
            await self.send_event(event)
            logger.info(f"Emitted content.discovered event for: {content_id}")
        except Exception as e:
            logger.error(f"Failed to emit content.discovered event: {str(e)}")
    
    async def _notify_new_content(self, content_data: dict):
        """发送新内容通知到频道"""
        title = content_data['title']
        url = content_data.get('url', '')
        source = content_data.get('source', 'Unknown')
        content = content_data.get('raw_content', '')
        
        # 截取内容预览
        preview = content[:200] + "..." if len(content) > 200 else content
        
        message = f"📰 **{title}**\n\n"
        message += f"📝 {preview}\n\n"
        message += f"📚 来源：{source}\n"
        if url:
            message += f"🔗 {url}\n"
        message += f"\n_等待 AI 处理中..._"
        
        await self._send_channel_message("灵感捕手", message)
    
    async def _send_channel_message(self, channel: str, text: str):
        """发送频道消息"""
        try:
            messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
            if messaging:
                await messaging.send_channel_message(
                    channel=channel,
                    text=text
                )
        except Exception as e:
            logger.error(f"Failed to send channel message: {str(e)}")


async def main():
    """运行 RSS Reader Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RSS Reader Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument("--interval", type=int, default=10, help="Fetch interval in seconds (default: 10)")
    args = parser.parse_args()
    
    # 配置日志 - 同时输出到文件和终端
    log_file = Path(__file__).parent.parent / 'logs' / 'agents' / 'rss_reader.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    
    # 强制刷新输出
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    agent = RSSReaderAgent(fetch_interval=args.interval)
    
    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )
        
        logger.info(f"RSS Reader Agent running. Press Ctrl+C to stop.")
        
        # 保持运行
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())