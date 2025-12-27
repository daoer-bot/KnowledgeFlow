#!/usr/bin/env python3
"""
Summarizer Agent - 为新内容生成摘要

功能：
- 监听 content.discovered 事件
- 调用 LLM 生成三种长度的摘要
- 提取关键要点和引用
- 发送 content.summarized 事件
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
from config.prompts import summarize
import logging

logger = logging.getLogger(__name__)


class SummarizerAgent(WorkerAgent):
    """Summarizer Agent - 生成内容摘要"""
    
    default_agent_id = "摘要生成器"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_llm_client()
        self.db = get_database()
    
    async def on_startup(self):
        """Agent 启动时执行"""
        logger.info("Summarizer Agent started")
        
        await self._send_channel_message(
            "通用频道",
            "🤖 Summarizer 已上线，开始处理内容摘要..."
        )
    
    async def on_shutdown(self):
        """Agent 关闭时执行"""
        logger.info("📝 摘要生成器 已停止")
    
    @on_event("content.discovered")
    async def handle_content_discovered(self, event):
        """处理 content.discovered 事件"""
        try:
            # event 是 EventContext 对象，通过属性访问
            payload = getattr(event, 'payload', {}) or {}
            content_id = payload.get("content_id") if isinstance(payload, dict) else getattr(payload, 'content_id', None)
            
            if not content_id:
                logger.warning("Received event without content_id")
                return
            
            logger.info(f"Processing content: {content_id}")
            
            # 获取内容
            content_data = self.db.get_content(content_id)
            if not content_data:
                logger.error(f"Content not found: {content_id}")
                return
            
            # 生成摘要
            summary_data = await self._generate_summary(content_data)
            
            if summary_data:
                # 更新数据库
                self.db.update_content_summary(content_id, summary_data)
                
                # 发送事件
                await self._emit_content_summarized(content_id, summary_data)
                
                logger.info(f"Summary completed for: {content_id}")
            else:
                logger.error(f"Failed to generate summary for: {content_id}")
        
        except Exception as e:
            logger.error(f"Error handling content.discovered: {str(e)}")
    
    async def _generate_summary(self, content_data: dict) -> dict:
        """
        生成摘要
        
        Returns:
            摘要数据字典，失败返回 None
        """
        try:
            title = content_data['title']
            source = content_data.get('source', 'Unknown')
            url = content_data.get('url', '')
            content = content_data.get('raw_content', '')
            
            if not content:
                logger.warning(f"No content to summarize for: {title}")
                return None
            
            # 格式化提示词
            system_prompt, user_prompt = summarize.format_prompt(
                title=title,
                source=source,
                url=url,
                content=content
            )
            
            # 调用 LLM
            logger.info(f"Calling LLM to generate summary for: {title}")
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
            required_fields = ['one_line', 'paragraph', 'detailed', 'key_points', 'key_quotes']
            if not all(field in result for field in required_fields):
                logger.error(f"Missing required fields in LLM response: {result.keys()}")
                return None
            
            logger.info(f"Successfully generated summary: {result['one_line'][:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return None
    
    async def _emit_content_summarized(self, content_id: str, summary_data: dict):
        """发送 content.summarized 事件"""
        try:
            # 发送事件通知其他 Agent (如 Tagger)
            event = Event(
                event_name="content.summarized",
                source_id=self.agent_id,
                payload={
                    "content_id": content_id,
                    "one_line": summary_data.get('one_line'),
                    "paragraph": summary_data.get('paragraph'),
                    "key_points": summary_data.get('key_points', [])
                }
            )
            await self.send_event(event)
            logger.info(f"Emitted content.summarized event for: {content_id}")
        except Exception as e:
            logger.error(f"Failed to emit content.summarized event: {str(e)}")
    
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
    """运行 Summarizer Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Summarizer Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    args = parser.parse_args()
    
    # 配置日志 - 同时输出到文件和终端
    log_file = Path(__file__).parent.parent / 'logs' / 'agents' / 'summarizer.log'
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
    
    agent = SummarizerAgent()
    
    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )
        
        logger.info(f"Summarizer Agent running. Press Ctrl+C to stop.")
        
        # 保持运行
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())