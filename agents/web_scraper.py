#!/usr/bin/env python3
"""
Web Scraper Agent - 响应用户请求抓取指定网页

功能：
- 监听 scraper-requests 频道
- 解析用户发送的 URL
- 抓取网页内容
- 发送 content.discovered 事件
- 回复用户抓取结果
"""

import asyncio
import sys
import re
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from openagents.agents.worker_agent import WorkerAgent, on_event
from tools.content_tools import WebScraper
from tools.database import get_database
import logging

logger = logging.getLogger(__name__)


class WebScraperAgent(WorkerAgent):
    """Web Scraper Agent - 按需抓取网页"""
    
    default_agent_id = "网页抓取代理"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scraper = WebScraper()
        self.db = get_database()
    
    async def on_startup(self):
        """Agent 启动时执行"""
        logger.info("Web Scraper Agent started")
        
        await self._send_channel_message(
            "通用频道",
            "🤖 Web Scraper 已上线\n\n使用方法：在 #scraper-requests 频道发送 URL 即可抓取"
        )
    
    async def on_shutdown(self):
        """Agent 关闭时执行"""
        logger.info("🌐 网页抓取器 已停止")
    
    @on_event("workspace.messaging.channel_message_created")
    async def handle_channel_message(self, event):
        """处理频道消息事件"""
        try:
            payload = event.get("payload", {})
            channel = payload.get("channel")
            message_text = payload.get("text", "")
            thread_id = payload.get("thread_id")
            
            # 只处理 scraper-requests 频道的消息
            if channel != "灵感采集":
                return
            
            # 忽略自己发送的消息
            if payload.get("agent_id") == self.agent_id:
                return
            
            logger.info(f"Received scrape request: {message_text[:100]}")
            
            # 提取 URL
            urls = self._extract_urls(message_text)
            
            if not urls:
                await self._send_channel_message(
                    "灵感采集",
                    "❌ 未检测到有效的 URL，请发送一个网页链接",
                    thread_id=thread_id
                )
                return
            
            # 处理第一个 URL
            url = urls[0]
            
            # 验证 URL
            if not self.scraper.validate_url(url):
                await self._send_channel_message(
                    "灵感采集",
                    f"❌ URL 格式无效：{url}",
                    thread_id=thread_id
                )
                return
            
            # 检查是否已存在
            if self.db.check_url_exists(url):
                await self._send_channel_message(
                    "灵感采集",
                    f"ℹ️ 该内容已存在于知识库中\n🔗 {url}",
                    thread_id=thread_id
                )
                return
            
            # 发送处理中消息
            await self._send_channel_message(
                "灵感采集",
                f"🔍 正在抓取...\n🔗 {url}",
                thread_id=thread_id
            )
            
            # 抓取内容
            result = await self._scrape_url(url)
            
            if result:
                await self._send_channel_message(
                    "灵感采集",
                    f"✅ 抓取成功！\n\n📄 **{result['title']}**\n📊 {result['word_count']} 字\n\n_已添加到内容库，等待 AI 处理..._",
                    thread_id=thread_id
                )
            else:
                await self._send_channel_message(
                    "灵感采集",
                    f"❌ 抓取失败，请检查 URL 是否可访问\n🔗 {url}",
                    thread_id=thread_id
                )
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    async def _scrape_url(self, url: str) -> dict:
        """
        抓取 URL 并保存
        
        Returns:
            抓取结果字典，失败返回 None
        """
        try:
            # 抓取内容（在线程池中执行以避免阻塞）
            loop = asyncio.get_event_loop()
            scraped_data = await loop.run_in_executor(
                None,
                self.scraper.scrape_url,
                url
            )
            
            if not scraped_data:
                return None
            
            # 保存到数据库
            content_data = {
                'title': scraped_data['title'],
                'url': scraped_data['url'],
                'raw_content': scraped_data['content'],
                'source': scraped_data.get('source', 'Web'),
                'source_type': 'web'
            }
            
            content_id = self.db.add_content(content_data)
            
            if content_id:
                # 发送事件
                await self._emit_content_discovered(content_id, content_data)
                
                # 发送到 content-feed 频道
                await self._notify_new_content(content_data)
                
                # 统计字数
                from tools.content_tools import ContentProcessor
                word_count = ContentProcessor.count_words(scraped_data['content'])
                
                return {
                    'title': scraped_data['title'],
                    'word_count': word_count,
                    'content_id': content_id
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return None
    
    def _extract_urls(self, text: str) -> list:
        """从文本中提取 URL"""
        # 匹配 http:// 或 https:// 开头的 URL
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(pattern, text)
        return urls
    
    async def _emit_content_discovered(self, content_id: str, content_data: dict):
        """发送 content.discovered 事件"""
        # 事件系统暂时禁用，使用频道消息通知
        logger.debug(f"Content discovered: {content_id}")
    
    async def _notify_new_content(self, content_data: dict):
        """发送新内容通知到频道"""
        title = content_data['title']
        url = content_data.get('url', '')
        source = content_data.get('source', 'Web')
        content = content_data.get('raw_content', '')
        
        # 截取内容预览
        preview = content[:200] + "..." if len(content) > 200 else content
        
        message = f"🌐 **{title}**\n\n"
        message += f"📝 {preview}\n\n"
        message += f"📚 来源：{source}\n"
        if url:
            message += f"🔗 {url}\n"
        message += f"\n_等待 AI 处理中..._"
        
        await self._send_channel_message("灵感捕手", message)
    
    async def _send_channel_message(self, channel: str, text: str, thread_id: str = None):
        """发送频道消息"""
        try:
            messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
            if messaging:
                await messaging.send_channel_message(
                    channel=channel,
                    text=text,
                    thread_id=thread_id
                )
        except Exception as e:
            logger.error(f"Failed to send channel message: {str(e)}")


async def main():
    """运行 Web Scraper Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Web Scraper Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    args = parser.parse_args()
    
    # 配置日志 - 同时输出到文件和终端
    log_file = Path(__file__).parent.parent / 'logs' / 'agents' / 'web_scraper.log'
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
    
    agent = WebScraperAgent()
    
    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )
        
        logger.info(f"Web Scraper Agent running. Press Ctrl+C to stop.")
        
        # 保持运行
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())