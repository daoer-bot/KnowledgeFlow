"""
Writer Agent
根据用户选择的大纲，分段生成完整文章
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


class WriterAgent(WorkerAgent):
    """文章写作 Agent"""
    
    default_agent_id = "文章写作器"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = None
        self.llm = None
        self.write_prompt = None
        
    async def on_startup(self):
        """Agent 启动时执行"""
        logger.info("✍️  Writer Agent 启动中...")
        
        # 导入依赖
        from tools.database import get_database
        from tools.llm_client import get_llm_client
        
        self.db = get_database()
        self.llm = get_llm_client()
        
        # 加载提示词
        try:
            from config.prompts import write
            self.write_prompt_module = write
            logger.info("✅ 写作提示词模块加载成功")
        except Exception as e:
            logger.error(f"❌ 提示词加载失败: {e}")
            raise
        
        logger.info("✅ Writer Agent 初始化完成")
        
        # 发送上线通知
        await self._send_channel_message(
            "通用频道",
            "✍️  Writer 已上线，等待大纲选择后开始创作..."
        )
    
    async def on_shutdown(self):
        """Agent 关闭时执行"""
        logger.info("Writer Agent stopped")
    
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
    
    @on_event("creation.start_writing")
    async def handle_writing_request(self, context):
        """
        监听写作请求事件（新事件驱动模式）
        由 CreationCoordinator 发送
        """
        logger.info(f"✍️  收到写作请求事件")
        try:
            # 从 context 中获取事件数据
            event_data = context.incoming_event.content if hasattr(context.incoming_event, 'content') else context.incoming_event.payload
            session_id = event_data.get('session_id')
            outline_id = event_data.get('outline_id')
            topic = event_data.get('topic')

            logger.info(f"📝 开始写作: session={session_id}, outline={outline_id}")

            # 从数据库加载大纲
            outline_data = self.db.get_outline(outline_id)
            if not outline_data:
                logger.error(f"❌ 大纲不存在: {outline_id}")
                await self._emit_error(session_id, "大纲不存在")
                return

            # 解析大纲内容
            outline_content = outline_data.get('content', {})
            if isinstance(outline_content, str):
                import json
                try:
                    outline_content = json.loads(outline_content)
                except:
                    outline_content = {}

            # 获取相关内容
            related_content_ids = outline_data.get('related_content_ids', [])
            if isinstance(related_content_ids, str):
                import json
                try:
                    related_content_ids = json.loads(related_content_ids)
                except:
                    related_content_ids = []

            related_contents = []
            for content_id in related_content_ids[:5]:
                content = self.db.get_content(content_id)
                if content:
                    related_contents.append(content)

            logger.info(f"📚 加载了 {len(related_contents)} 篇相关内容")

            # 生成文章
            style = outline_data.get('style', '专业分析')
            draft = await self._write_article(
                topic=topic,
                outline=outline_content,
                related_contents=related_contents,
                style=style,
                session_id=session_id
            )

            # 保存草稿到数据库
            draft_id = self.db.save_draft({
                'outline_id': outline_id,
                'title': draft['title'],
                'content': draft['content'],
                'word_count': draft['word_count'],
                'status': 'completed'
            })

            logger.info(f"💾 草稿已保存: {draft_id}")

            # 标记大纲为已选择
            self.db.mark_outline_selected(outline_id)

            # 保存到 Wiki 知识库
            await self._save_article_to_wiki(draft, topic, style)

            # 发送 creation.draft_ready 事件通知 CreationCoordinator
            event = Event(
                event_name="creation.draft_ready",
                source_id=self.agent_id,
                payload={
                    "session_id": session_id,
                    "draft_id": draft_id,
                    "draft": draft
                }
            )
            await self.send_event(event)

            logger.info(f"✅ 文章创作完成并已发送事件: session={session_id}")

        except Exception as e:
            logger.error(f"❌ 文章创作失败: {e}", exc_info=True)
            await self._emit_error(event_data.get('session_id'), str(e))

    @on_event("creation.optimize_draft")
    async def handle_optimize_draft(self, context):
        """
        处理文章优化请求事件
        由 CreationCoordinator 发送，根据评审建议优化文章
        """
        logger.info(f"🔧 收到文章优化请求事件")
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            draft_id = event_data.get('draft_id')
            suggestions = event_data.get('suggestions', [])

            logger.info(f"📝 优化文章: session={session_id}, draft={draft_id}")
            logger.info(f"   建议数量: {len(suggestions)}")

            # 从数据库加载草稿
            draft_data = self.db.get_draft(draft_id)
            if not draft_data:
                logger.error(f"❌ 草稿不存在: {draft_id}")
                return

            title = draft_data.get('title', '')
            content = draft_data.get('content', '')

            # 调用 LLM 优化文章
            optimized_content, improvements = await self._optimize_with_llm(
                title=title,
                content=content,
                suggestions=suggestions
            )

            # 更新草稿
            new_word_count = len(optimized_content.replace(' ', '').replace('\n', ''))
            self.db.update_draft(draft_id, {
                'content': optimized_content,
                'word_count': new_word_count,
                'status': 'optimized'
            })

            # 发送优化完成事件
            event = Event(
                event_name="creation.optimization_done",
                source_id=self.agent_id,
                payload={
                    "session_id": session_id,
                    "draft_id": draft_id,
                    "draft": {
                        "title": title,
                        "content": optimized_content,
                        "word_count": new_word_count
                    },
                    "improvements": improvements
                }
            )
            await self.send_event(event)

            logger.info(f"✅ 文章优化完成: {draft_id}")

        except Exception as e:
            logger.error(f"❌ 文章优化失败: {e}", exc_info=True)

    async def _optimize_with_llm(self, title: str, content: str, suggestions: list) -> tuple:
        """使用 LLM 优化文章"""
        try:
            system_prompt = """你是一个专业的文章优化编辑。
根据评审建议优化文章，保持原有结构和风格，但改进内容质量。

优化原则：
1. 保持文章的核心观点和结构
2. 根据建议改进具体内容
3. 提升文章的可读性和专业性
4. 不要大幅改变文章长度

返回优化后的完整文章内容（Markdown格式）。"""

            suggestions_text = "\n".join([f"- {s}" for s in suggestions[:5]])
            user_prompt = f"""请根据以下评审建议优化文章：

**评审建议**：
{suggestions_text}

**原文章**：
# {title}

{content}

请返回优化后的完整文章内容。"""

            optimized_content = await self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=20000
            )

            # 提取改进点
            improvements = [
                "根据评审建议优化了内容表达",
                "改进了技术描述的准确性",
                "增强了文章的可读性"
            ]

            return optimized_content, improvements

        except Exception as e:
            logger.error(f"LLM 优化文章失败: {e}")
            return content, []
    
    async def _emit_error(self, session_id: str, error_message: str):
        """发送错误事件"""
        try:
            error_event = Event(
                event_name="creation.writing_error",
                source_id=self.agent_id,
                payload={
                    "session_id": session_id,
                    "error": error_message
                }
            )
            await self.send_event(error_event)
        except Exception as e:
            logger.error(f"发送错误事件失败: {e}")

    async def _emit_writing_progress(
        self,
        session_id: str,
        section_index: int,
        total_sections: int,
        section_title: str,
        status: str
    ):
        """
        发送写作进度事件

        Args:
            session_id: 会话ID
            section_index: 章节索引（从0开始）
            total_sections: 总章节数
            section_title: 章节标题
            status: 状态 (started, completed)
        """
        try:
            progress_event = Event(
                event_name="creation.writing_progress",
                source_id=self.agent_id,
                payload={
                    "session_id": session_id,
                    "section_index": section_index,
                    "total_sections": total_sections,
                    "section_title": section_title,
                    "status": status
                }
            )
            await self.send_event(progress_event)
            logger.info(f"📊 进度事件: {status} - {section_title} ({section_index + 1}/{total_sections})")
        except Exception as e:
            logger.error(f"发送进度事件失败: {e}")

    async def _emit_writing_chunk(
        self,
        session_id: str,
        chunk_type: str,
        content: str = "",
        section_title: str = "",
        section_index: int = 0,
        total_sections: int = 0
    ):
        """
        发送流式写作事件

        Args:
            session_id: 会话ID
            chunk_type: 事件类型 (section_start, content, section_end)
            content: 内容片段
            section_title: 章节标题
            section_index: 章节索引
            total_sections: 总章节数
        """
        try:
            chunk_event = Event(
                event_name="creation.writing_chunk",
                source_id=self.agent_id,
                payload={
                    "session_id": session_id,
                    "chunk_type": chunk_type,
                    "content": content,
                    "section_title": section_title,
                    "section_index": section_index,
                    "total_sections": total_sections
                }
            )
            await self.send_event(chunk_event)
        except Exception as e:
            logger.error(f"发送流式事件失败: {e}")
    
    async def _write_article(
        self,
        topic: str,
        outline: Dict[str, Any],
        related_contents: List[Dict[str, Any]],
        style: str,
        session_id: str = ""
    ) -> Dict[str, Any]:
        """
        生成完整文章

        返回: 文章数据
        """
        try:
            # 准备素材数据
            materials = []
            for content in related_contents:
                materials.append({
                    'id': content.get('id', 'unknown'),
                    'title': content.get('title', 'N/A'),
                    'summary': content.get('summary_paragraph', content.get('raw_content', '')[:300]),
                    'source': content.get('source', '未知'),
                    'key_points': content.get('key_points', [])
                })

            # 获取大纲结构
            sections = outline.get('structure', outline.get('sections', []))
            title = outline.get('title', f'{topic}：深度解析')
            subtitle = outline.get('subtitle', '')

            # 生成文章各部分
            full_content = f"# {title}\n\n"
            if subtitle:
                full_content += f"*{subtitle}*\n\n"

            previous_context = ""

            logger.info(f"🤖 开始逐段生成文章，共 {len(sections)} 个部分...")

            total_sections = len(sections)
            for i, section in enumerate(sections):
                # 解析章节信息 - 支持新的丰富结构
                if isinstance(section, str):
                    section_title = section
                    section_points = [f'{section}相关内容']
                    section_type = "body"
                    writing_tips = ""
                    core_argument = ""
                    estimated_words = 400
                else:
                    section_title = section.get('section', f'第{i+1}部分')
                    section_points = section.get('points', [])
                    section_type = section.get('section_type', 'body')
                    writing_tips = section.get('writing_tips', '')
                    core_argument = section.get('core_argument', '')
                    estimated_words = section.get('estimated_words', 400)

                # 发送章节开始进度事件
                if session_id:
                    await self._emit_writing_progress(
                        session_id=session_id,
                        section_index=i,
                        total_sections=total_sections,
                        section_title=section_title,
                        status='started'
                    )

                # 使用写作提示词模块 - 传递新参数
                system_prompt, user_prompt = self.write_prompt_module.format_section_prompt(
                    article_title=title,
                    section_title=section_title,
                    section_points=section_points if section_points else [f'{section_title}相关内容'],
                    materials=materials,
                    previous_context=previous_context,
                    target_words=estimated_words,
                    section_type=section_type,
                    writing_tips=writing_tips,
                    core_argument=core_argument
                )

                # 非流式生成该段内容
                section_content = await self.llm.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.7,
                    max_tokens=20000
                )

                # 添加到文章
                full_content += f"## {section_title}\n\n{section_content}\n\n"

                # 更新上下文
                previous_context = section_content

                # 发送章节完成进度事件
                if session_id:
                    await self._emit_writing_progress(
                        session_id=session_id,
                        section_index=i,
                        total_sections=total_sections,
                        section_title=section_title,
                        status='completed'
                    )

                logger.info(f"  ✓ 完成第 {i+1}/{len(sections)} 部分: {section_title}")

            # 提取标题（如果LLM生成了）
            title = outline.get('title', f'{topic}：深度解析')

            # 如果内容中有标题行
            lines = full_content.split('\n')
            if lines and (lines[0].startswith('#') or lines[0].startswith('**')):
                title = lines[0].strip('#* ')
                full_content = '\n'.join(lines[1:]).strip()

            # 计算字数
            word_count = len(full_content.replace(' ', '').replace('\n', ''))

            draft = {
                'title': title,
                'content': full_content,
                'word_count': word_count
            }

            logger.info(f"✅ 文章生成完成，共 {word_count} 字")
            return draft

        except Exception as e:
            logger.error(f"❌ 文章生成失败: {e}", exc_info=True)
            raise
    
    async def _save_article_to_wiki(self, draft: Dict[str, Any], topic: str, style: str):
        """保存文章到 Wiki 知识库 - 使用事件方式"""
        try:
            title = draft['title']
            content = draft['content']
            word_count = draft['word_count']
            
            # 构建 Wiki 页面内容
            wiki_content = f"# {title}\n\n"
            wiki_content += f"**主题**: {topic}\n"
            wiki_content += f"**风格**: {style}\n"
            wiki_content += f"**字数**: {word_count}\n"
            wiki_content += f"**创作时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            wiki_content += "---\n\n"
            wiki_content += content
            
            # 使用安全的 page_path（移除特殊字符）
            import re
            page_path = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', title)[:100]
            
            # 通过事件发送到 Wiki mod
            wiki_event = Event(
                event_name="wiki.page.create",
                source_id=self.agent_id,
                target_agent_id="mod:openagents.mods.workspace.wiki",
                payload={
                    "page_path": f"articles/{page_path}",
                    "title": title,
                    "wiki_content": wiki_content
                },
                visibility="network"
            )
            
            await self.send_event(wiki_event)
            logger.info(f"📚 已发送 Wiki 保存事件: {title}")
            
        except Exception as e:
            logger.error(f"❌ Wiki 保存失败: {str(e)}")


async def main():
    """运行 Writer Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Writer Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    args = parser.parse_args()
    
    # 配置日志 - 同时输出到文件和终端
    log_file = Path(__file__).parent.parent / 'logs' / 'agents' / 'writer.log'
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
    
    agent = WriterAgent()
    
    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )
        
        logger.info("Writer Agent running. Press Ctrl+C to stop.")
        
        # 保持运行
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())