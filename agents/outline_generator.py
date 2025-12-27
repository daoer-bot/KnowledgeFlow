"""
Outline Generator Agent
监听 creation 频道的用户请求，搜索相关内容，生成文章大纲
"""

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from openagents.agents.worker_agent import WorkerAgent, on_event
from openagents.models.event import Event

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OutlineGeneratorAgent(WorkerAgent):
    """大纲生成 Agent"""
    
    default_agent_id = "大纲生成器"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = None
        self.llm = None
        self.outline_prompt = None
        
    async def on_startup(self):
        """Agent 启动时执行"""
        logger.info("🎯 Outline Generator Agent 启动中...")
        
        # 导入依赖
        from tools.database import get_database
        from tools.llm_client import get_llm_client
        
        self.db = get_database()
        self.llm = get_llm_client()
        
        # 加载提示词
        try:
            from config.prompts import outline
            self.outline_prompt_module = outline
            logger.info("✅ 大纲提示词模块加载成功")
        except Exception as e:
            logger.error(f"❌ 提示词加载失败: {e}")
            raise
        
        logger.info("✅ Outline Generator Agent 初始化完成")
        
        # 发送上线通知
        await self._send_channel_message(
            "通用频道",
            "🎯 Outline Generator 已上线，可以在 创作工坊 频道发送创作请求..."
        )
    
    async def on_shutdown(self):
        """Agent 关闭时执行"""
        logger.info("Outline Generator Agent stopped")
    
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
    
    @on_event("creation.search_materials")
    async def handle_search_materials(self, context):
        """
        处理素材搜索请求事件
        由 CreationCoordinator 发送，搜索知识库中的相关素材
        """
        logger.info(f"🔍 收到素材搜索请求事件")
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            user_id = event_data.get('user_id')
            topic = event_data.get('topic')

            logger.info(f"📚 搜索素材: session={session_id}, topic={topic}")

            # 搜索相关内容
            related_contents = await self._search_related_content([topic])

            # 构建素材列表
            materials = []
            for content in related_contents[:10]:
                materials.append({
                    'id': content.get('id', ''),
                    'title': content.get('title', 'N/A'),
                    'summary': content.get('summary_paragraph', content.get('raw_content', '')[:200]),
                    'source': content.get('source', '未知'),
                    'tags': content.get('tags', [])
                })

            # 发送素材搜索结果事件
            event = Event(
                event_name="creation.materials_found",
                source_id=self.agent_id,
                payload={
                    "session_id": session_id,
                    "user_id": user_id,
                    "topic": topic,
                    "materials": materials
                }
            )
            await self.send_event(event)

            logger.info(f"✅ 素材搜索完成: 找到 {len(materials)} 篇相关内容")

        except Exception as e:
            logger.error(f"❌ 素材搜索失败: {e}", exc_info=True)
            # 发送空结果，让流程继续
            try:
                event = Event(
                    event_name="creation.materials_found",
                    source_id=self.agent_id,
                    payload={
                        "session_id": event_data.get('session_id'),
                        "materials": []
                    }
                )
                await self.send_event(event)
            except:
                pass

    @on_event("creation.modify_outline")
    async def handle_modify_outline(self, context):
        """
        处理大纲修改请求事件
        由 CreationCoordinator 发送，根据用户要求修改大纲
        """
        logger.info(f"📝 收到大纲修改请求事件")
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            outline_id = event_data.get('outline_id')
            modification = event_data.get('modification', '')

            logger.info(f"✏️ 修改大纲: session={session_id}, outline={outline_id}")
            logger.info(f"   修改要求: {modification[:50]}...")

            # 从数据库加载原大纲
            outline_data = self.db.get_outline(outline_id)
            if not outline_data:
                logger.error(f"❌ 大纲不存在: {outline_id}")
                return

            # 解析大纲内容
            import json
            outline_content = outline_data.get('content', {})
            if isinstance(outline_content, str):
                try:
                    outline_content = json.loads(outline_content)
                except:
                    outline_content = {}

            # 调用 LLM 修改大纲
            modified_outline = await self._modify_outline_with_llm(
                outline_content,
                modification
            )

            # 更新数据库中的大纲
            self.db.update_outline(outline_id, {'content': modified_outline})

            # 发送修改完成事件
            event = Event(
                event_name="creation.outline_modified",
                source_id=self.agent_id,
                payload={
                    "session_id": session_id,
                    "outline_id": outline_id,
                    "outline": modified_outline
                }
            )
            await self.send_event(event)

            logger.info(f"✅ 大纲修改完成: {outline_id}")

        except Exception as e:
            logger.error(f"❌ 大纲修改失败: {e}", exc_info=True)

    async def _modify_outline_with_llm(self, outline: dict, modification: str) -> dict:
        """使用 LLM 修改大纲"""
        try:
            system_prompt = """你是一个专业的文章大纲编辑助手。
用户会提供一个现有的大纲和修改要求，请根据要求修改大纲。

返回修改后的完整大纲，保持 JSON 格式：
{
    "title": "文章标题",
    "subtitle": "副标题（可选）",
    "style": "写作风格",
    "target_audience": "目标读者",
    "structure": [
        {
            "section": "章节标题",
            "section_type": "intro/body/conclusion",
            "points": ["要点1", "要点2"],
            "estimated_words": 400
        }
    ],
    "total_estimated_words": 2000
}"""

            import json
            user_prompt = f"""现有大纲：
{json.dumps(outline, ensure_ascii=False, indent=2)}

修改要求：{modification}

请根据要求修改大纲，返回完整的修改后大纲（JSON格式）。"""

            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000
            )

            if result:
                return result
            return outline  # 修改失败则返回原大纲

        except Exception as e:
            logger.error(f"LLM 修改大纲失败: {e}")
            return outline

    @on_event("creation.request_outlines")
    async def handle_outline_request(self, context):
        """
        监听大纲生成请求事件（新事件驱动模式）
        由 CreationCoordinator 发送
        """
        logger.info(f"🎯 收到大纲生成请求事件")
        try:
            # 从 context 中获取事件数据
            event_data = context.incoming_event.content if hasattr(context.incoming_event, 'content') else context.incoming_event.payload
            if isinstance(event_data, dict):
                session_id = event_data.get('session_id')
                user_id = event_data.get('user_id')
                topic = event_data.get('topic')
            else:
                logger.error(f"❌ 事件数据格式错误: {type(event_data)}")
                return
            
            logger.info(f"📝 开始生成大纲: session={session_id}, topic={topic}")
            
            # 搜索相关内容
            related_contents = await self._search_related_content([topic])
            
            if not related_contents:
                logger.warning(f"⚠️  未找到相关内容: {topic}")
                # 使用空列表继续生成（会使用默认大纲）
                related_contents = []
            
            # 生成大纲
            style = "专业分析"  # 默认风格
            outlines = await self._generate_outlines(
                topic=topic,
                related_contents=related_contents,
                style=style
            )
            
            # 保存大纲到数据库
            outline_ids = []
            related_content_ids = [c['id'] for c in related_contents] if related_contents else []
            
            for i, outline in enumerate(outlines):
                outline_id = self.db.save_outline({
                    'topic': topic,
                    'content': outline,
                    'style': style,
                    'related_content_ids': related_content_ids
                })
                outline_ids.append(outline_id)
                logger.info(f"💾 大纲 {i+1} 已保存: {outline_id}")
            
            # 发送 creation.outlines_ready 事件通知 CreationCoordinator
            event = Event(
                event_name="creation.outlines_ready",
                source_id=self.agent_id,
                payload={
                    "session_id": session_id,
                    "outline_ids": outline_ids,
                    "outlines": outlines,
                    "style": style,
                    "related_content_ids": related_content_ids
                }
            )
            await self.send_event(event)
            
            logger.info(f"✅ 大纲生成完成并已发送事件: session={session_id}, 数量={len(outlines)}")
            
        except Exception as e:
            logger.error(f"❌ 大纲生成失败: {e}", exc_info=True)
            # 发送错误事件
            try:
                error_event = Event(
                    event_name="creation.outlines_error",
                    source_id=self.agent_id,
                    payload={
                        "session_id": event_data.get('session_id'),
                        "error": str(e)
                    }
                )
                await self.send_event(error_event)
            except:
                pass
    
    async def _search_related_content(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """搜索相关内容 - 优先从 Wiki 搜索，回退到数据库"""
        results = []
        
        # 1. 首先尝试从 Wiki 搜索（使用事件方式）
        try:
            # 发送 Wiki 搜索事件
            search_event = Event(
                event_name="wiki.search",
                source_id=self.agent_id,
                target_agent_id="mod:openagents.mods.workspace.wiki",
                payload={
                    "query": " ".join(keywords),
                    "content_types": ["pages"],
                    "limit": 10
                },
                visibility="network"
            )
            
            # 注意：由于事件是异步的，Wiki 搜索结果无法立即获取
            # 这里我们直接使用数据库搜索作为主要方式
            logger.info(f"⚠️ Wiki 搜索需要事件响应机制，当前使用数据库搜索")
            
        except Exception as e:
            logger.info(f"⚠️ Wiki 搜索准备失败: {e}，使用数据库搜索")
        
        # 2. 从数据库搜索（主要方式）
        try:
            db_results = self.db.search_content(keywords=keywords, limit=10)
            
            if not db_results:
                # 如果没有结果，尝试获取最近的内容
                db_results = self.db.get_recent_content(limit=5)
            
            for item in db_results:
                results.append(item)
            
            logger.info(f"🔍 从数据库找到 {len(results)} 篇相关内容")
        except Exception as e:
            logger.error(f"❌ 数据库搜索失败: {e}")
        
        return results
    
    async def _generate_outlines(
        self,
        topic: str,
        related_contents: List[Dict[str, Any]],
        style: str
    ) -> List[Dict[str, Any]]:
        """
        生成多个大纲方案
        
        返回: 大纲列表
        """
        try:
            # 准备参考内容摘要
            content_summaries = []
            for content in related_contents[:5]:  # 最多使用5篇
                summary = {
                    'title': content.get('title', 'N/A'),
                    'summary': content.get('summary_paragraph', 'N/A'),
                    'key_points': content.get('key_points', [])
                }
                content_summaries.append(summary)
            
            # 准备素材数据
            materials = []
            for content in related_contents[:5]:
                materials.append({
                    'id': content.get('id', 'unknown'),
                    'title': content.get('title', 'N/A'),
                    'summary': content.get('summary_paragraph', content.get('raw_content', 'N/A')[:300]),
                    'source': content.get('source', '未知')
                })
            
            # 构建提示词
            system_prompt, user_prompt = self.outline_prompt_module.format_prompt(
                topic=topic,
                materials=materials,
                word_count=2000
            )
            
            logger.info("🤖 调用 LLM 生成大纲...")

            # 调用 LLM（JSON 模式）
            # 注意：生成 3 个详细大纲需要较多 token，设置为 6000 避免输出被截断
            response = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,  # 提高创造性
                max_tokens=10000
            )
            
            # 解析响应 - 处理 None 的情况
            if response is None:
                logger.warning("⚠️  LLM 返回 None，使用默认结构")
                outlines = self._create_default_outline(topic)
            else:
                outlines = response.get('outlines', [])
                if not outlines:
                    logger.warning("⚠️  LLM 未返回大纲，使用默认结构")
                    outlines = self._create_default_outline(topic)
            
            logger.info(f"✅ 生成了 {len(outlines)} 个大纲方案")
            return outlines
            
        except Exception as e:
            logger.error(f"❌ 大纲生成失败: {e}", exc_info=True)
            # 返回默认大纲
            return self._create_default_outline(topic)
    
    def _create_default_outline(self, topic: str) -> List[Dict[str, Any]]:
        """创建默认大纲结构"""
        return [{
            'title': f'{topic}：全面解析',
            'sections': ['引言', '核心概念', '应用场景', '未来展望', '总结'],
            'estimated_words': 2000,
            'key_points': [
                '介绍主题背景和重要性',
                '详细解释核心概念',
                '分析实际应用场景',
                '展望未来发展趋势',
                '总结要点'
            ]
        }]
    


async def main():
    """运行 Outline Generator Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Outline Generator Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    args = parser.parse_args()
    
    # 配置日志 - 同时输出到文件和终端
    log_file = Path(__file__).parent.parent / 'logs' / 'agents' / 'outline_generator.log'
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
    
    agent = OutlineGeneratorAgent()
    
    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )
        
        logger.info("Outline Generator Agent running. Press Ctrl+C to stop.")
        
        # 保持运行
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())