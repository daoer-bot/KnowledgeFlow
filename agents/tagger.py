#!/usr/bin/env python3
"""
Tagger Agent - 为内容生成标签和分类

功能：
- 监听 content.summarized 事件
- 调用 LLM 生成标签和分类
- 发送 content.tagged 事件
- 发送美观的内容卡片到 knowledge-base 频道
- 更新数据库
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from openagents.agents.worker_agent import WorkerAgent, on_event
from openagents.models.event import Event
from tools.llm_client import get_llm_client
from tools.database import get_database
from tools.content_tools import ContentProcessor
from config.prompts import tag
import logging

logger = logging.getLogger(__name__)


class TaggerAgent(WorkerAgent):
    """Tagger Agent - 生成标签和分类"""
    
    default_agent_id = "标签生成器"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_llm_client()
        self.db = get_database()
    
    async def on_startup(self):
        """Agent 启动时执行"""
        logger.info("Tagger Agent started")
        
        await self._send_channel_message(
            "通用频道",
            "🤖 Tagger 已上线，开始处理内容分类和标签..."
        )
    
    async def on_shutdown(self):
        """Agent 关闭时执行"""
        logger.info("Tagger Agent stopped")
    
    @on_event("content.summarized")
    async def handle_content_summarized(self, event):
        """处理 content.summarized 事件"""
        try:
            # event 是 EventContext 对象，通过属性访问
            payload = getattr(event, 'payload', {}) or {}
            content_id = payload.get("content_id") if isinstance(payload, dict) else getattr(payload, 'content_id', None)
            
            if not content_id:
                logger.warning("Received event without content_id")
                return
            
            logger.info(f"Tagging content: {content_id}")
            
            # 获取内容
            content_data = self.db.get_content(content_id)
            if not content_data:
                logger.error(f"Content not found: {content_id}")
                return
            
            # 生成标签
            tag_data = await self._generate_tags(content_data)
            
            if tag_data:
                # 更新数据库
                self.db.update_content_tags(content_id, tag_data)
                
                # 发送事件
                await self._emit_content_tagged(content_id, tag_data)
                
                # 保存到 Wiki 知识库
                await self._save_to_wiki(content_id, content_data, tag_data)
                
                # 发送内容卡片到 knowledge-base 频道
                await self._send_content_card(content_data, tag_data)
                
                logger.info(f"Tagging completed for: {content_id}")
            else:
                logger.error(f"Failed to generate tags for: {content_id}")
        
        except Exception as e:
            logger.error(f"Error handling content.summarized: {str(e)}")
    
    async def _generate_tags(self, content_data: dict) -> dict:
        """
        生成标签和分类
        
        Returns:
            标签数据字典，失败返回 None
        """
        try:
            title = content_data['title']
            source = content_data.get('source', 'Unknown')
            summary = content_data.get('summary_paragraph', '')
            
            if not summary:
                logger.warning(f"No summary available for: {title}")
                return None
            
            # 格式化提示词
            system_prompt, user_prompt = tag.format_prompt(
                title=title,
                source=source,
                summary=summary
            )
            
            # 调用 LLM
            logger.info(f"Calling LLM to generate tags for: {title}")
            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=10000
            )
            
            if not result:
                logger.error("LLM returned empty result")
                return None
            
            # 验证返回的字段
            required_fields = ['category', 'tags', 'sentiment', 'relevance_score']
            if not all(field in result for field in required_fields):
                logger.error(f"Missing required fields in LLM response: {result.keys()}")
                return None
            
            logger.info(f"Successfully generated tags: {result['category']}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating tags: {str(e)}")
            return None
    
    async def _emit_content_tagged(self, content_id: str, tag_data: dict):
        """发送 content.tagged 事件"""
        try:
            # 发送事件通知其他 Agent
            event = Event(
                event_name="content.tagged",
                source_id=self.agent_id,
                payload={
                    "content_id": content_id,
                    "category": tag_data.get('category'),
                    "tags": tag_data.get('tags', {}),
                    "sentiment": tag_data.get('sentiment'),
                    "relevance_score": tag_data.get('relevance_score')
                }
            )
            await self.send_event(event)
            logger.info(f"Emitted content.tagged event for: {content_id}")
        except Exception as e:
            logger.error(f"Failed to emit content.tagged event: {str(e)}")
    
    async def _save_to_wiki(self, content_id: str, content_data: dict, tag_data: dict):
        """保存内容到 Wiki 知识库 - 使用事件方式"""
        try:
            title = content_data['title']
            url = content_data.get('url', '')
            source = content_data.get('source', 'Unknown')
            summary = content_data.get('summary_paragraph', '')
            detailed = content_data.get('summary_detailed', '')
            key_points = content_data.get('key_points', [])
            key_quotes = content_data.get('key_quotes', [])
            category = tag_data.get('category', 'tech-news')
            tags = tag_data.get('tags', {})
            
            # 构建 Wiki 页面内容
            wiki_content = f"# {title}\n\n"
            wiki_content += f"**来源**: {source}\n"
            if url:
                wiki_content += f"**链接**: {url}\n"
            wiki_content += f"**分类**: {category}\n\n"
            
            # 标签
            tag_list = []
            for tag_type, tag_values in tags.items():
                if isinstance(tag_values, list):
                    tag_list.extend(tag_values)
            if tag_list:
                wiki_content += f"**标签**: {', '.join(tag_list)}\n\n"
            
            wiki_content += "---\n\n"
            
            # 摘要
            if summary:
                wiki_content += f"## 摘要\n\n{summary}\n\n"
            
            # 关键要点
            if key_points:
                wiki_content += "## 关键要点\n\n"
                for point in key_points:
                    wiki_content += f"- {point}\n"
                wiki_content += "\n"
            
            # 关键引用
            if key_quotes:
                wiki_content += "## 关键引用\n\n"
                for quote in key_quotes:
                    wiki_content += f"> {quote}\n\n"
            
            # 详细摘要
            if detailed:
                wiki_content += f"## 详细内容\n\n{detailed}\n"
            
            # 使用安全的 page_path（移除特殊字符）
            import re
            page_path = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', title)[:100]
            
            # 通过事件发送到 Wiki mod
            wiki_event = Event(
                event_name="wiki.page.create",
                source_id=self.agent_id,
                target_agent_id="mod:openagents.mods.workspace.wiki",
                payload={
                    "page_path": f"{category}/{page_path}",
                    "title": title,
                    "wiki_content": wiki_content
                },
                visibility="network"
            )
            
            await self.send_event(wiki_event)
            logger.info(f"📚 已发送 Wiki 保存事件: {title}")
            
        except Exception as e:
            logger.error(f"❌ Wiki 保存失败: {str(e)}")
    
    async def _send_content_card(self, content_data: dict, tag_data: dict):
        """发送内容卡片到 knowledge-base 频道"""
        try:
            title = content_data['title']
            url = content_data.get('url', '')
            source = content_data.get('source', 'Unknown')
            summary = content_data.get('summary_paragraph', '')
            key_points = content_data.get('key_points', [])
            category = tag_data.get('category', '')
            tags = tag_data.get('tags', {})
            
            # 构建卡片
            card = "✅ **内容已处理**\n"
            card += "━━━━━━━━━━━━━━━━\n\n"
            card += f"📌 **{title}**\n\n"
            
            if summary:
                card += f"📝 {summary}\n\n"
            
            if key_points:
                card += "🔑 **关键要点：**\n"
                for point in key_points[:3]:  # 最多显示3个
                    card += f"• {point}\n"
                card += "\n"
            
            # 标签
            tag_list = []
            for tag_type, tag_values in tags.items():
                if isinstance(tag_values, list):
                    tag_list.extend(tag_values)
            
            if tag_list:
                tag_str = " ".join([f"#{t}" for t in tag_list[:5]])
                card += f"🏷️ {tag_str}\n\n"
            
            # 来源和分类
            card += f"📚 {source}"
            if category:
                card += f" | {category}"
            card += "\n"
            
            if url:
                card += f"🔗 {url}\n"
            
            await self._send_channel_message("灵感捕手", card)
            
        except Exception as e:
            logger.error(f"Error sending content card: {str(e)}")
    
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
    """运行 Tagger Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tagger Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    args = parser.parse_args()
    
    # 配置日志 - 同时输出到文件和终端
    log_file = Path(__file__).parent.parent / 'logs' / 'agents' / 'tagger.log'
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
    
    agent = TaggerAgent()
    
    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )
        
        logger.info(f"Tagger Agent running. Press Ctrl+C to stop.")
        
        # 保持运行
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())