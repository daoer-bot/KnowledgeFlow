#!/usr/bin/env python3
"""
AI味审查员 Agent - 检测AI生成痕迹，提升内容人味

功能：
- 监听 content.tagged 事件自动审查
- 支持 @ 触发：在「创作工坊」频道 @AI味审查 审查最近文章
- 检测AI生成痕迹、语言自然度、情感真实性等
- 给出人性化改写建议
"""

import asyncio
import re
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
from config.prompts import critic_business
import logging

logger = logging.getLogger(__name__)


class AIFlavorReviewerAgent(WorkerAgent):
    """AI味审查员 Agent - 检测AI痕迹提升人味"""

    default_agent_id = "AI味审查"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_llm_client()
        self.db = get_database()
    
    async def on_startup(self):
        """Agent 启动时执行"""
        logger.info("AI Flavor Reviewer Agent started")

        await self._send_channel_message(
            "通用频道",
            "🤖 AI味审查员已上线！\n"
            "📝 在「创作工坊」频道 @AI味审查 即可检测内容的AI痕迹"
        )

    async def on_shutdown(self):
        """Agent 关闭时执行"""
        logger.info("AI Flavor Reviewer Agent stopped")

    # ========== @ 触发功能 ==========

    @on_event("thread.channel_message.notification")
    async def handle_mention(self, context):
        """
        处理 @ 消息
        当用户在创作工坊 @AI味审查 时触发
        """
        try:
            # 获取消息数据
            payload = context.incoming_event.payload
            channel = payload.get('channel', '')
            text = payload.get('content', {}).get('text', '').strip()
            user_id = payload.get('source_id', '')

            # 只处理创作工坊频道
            if channel != '创作工坊':
                return

            # 忽略自己的消息
            if user_id == 'AI味审查':
                return

            # 检查是否 @ 了AI味审查
            if not self._is_mentioned(text):
                return

            logger.info(f"📨 收到 @ 消息: user={user_id}, text={text[:50]}...")

            # 获取最近的文章
            draft = await self._get_latest_draft()

            if not draft:
                await self._send_channel_message(
                    "创作工坊",
                    "📭 暂时没有找到最近的文章哦~\n"
                    "💡 先创作一篇文章，然后再来找我审查吧！"
                )
                return

            # 通知用户正在审查
            await self._send_channel_message(
                "创作工坊",
                f"🤖 正在进行AI味审查「{draft.get('title', '未命名')}」...\n"
                f"⏱️ 请稍候，马上给出审查结果~"
            )

            # 生成审查结果
            review_data = await self._generate_draft_review(draft)

            if review_data:
                # 发送审查结果
                await self._post_draft_review(draft, review_data)
                logger.info(f"✅ AI味审查完成: {draft.get('title', 'N/A')}")
            else:
                await self._send_channel_message(
                    "创作工坊",
                    "❌ AI味审查失败，请稍后再试"
                )

        except Exception as e:
            logger.error(f"❌ 处理 @ 消息失败: {e}", exc_info=True)
            await self._send_channel_message("创作工坊", f"❌ 审查失败: {str(e)}")

    def _is_mentioned(self, text: str) -> bool:
        """检查是否被 @ 了"""
        patterns = [
            r'@AI味审查',
            r'@AI味',
            r'@人味',
            r'@原创',
        ]
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    async def _get_latest_draft(self) -> dict:
        """获取最近完成的文章"""
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM drafts
                WHERE status = 'completed'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            conn.close()
            if row:
                return self.db._row_to_dict(row)
            return None
        except Exception as e:
            logger.error(f"获取最近文章失败: {e}")
            return None

    async def _generate_draft_review(self, draft: dict) -> dict:
        """为文章草稿生成AI味审查"""
        try:
            title = draft.get('title', '未命名')
            content = draft.get('content', '')
            word_count = draft.get('word_count', 0)

            # 构建审查提示词
            system_prompt = critic_business.SYSTEM_PROMPT
            user_prompt = f"""请对以下自媒体文章进行AI味审查：

**标题**: {title}
**字数**: {word_count}

**文章内容**:
{content[:3000]}

{'...(内容已截取)' if len(content) > 3000 else ''}

请检测文章的AI生成痕迹，并给出人性化改写建议。"""

            # 调用 LLM
            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=8000
            )

            return result

        except Exception as e:
            logger.error(f"生成AI味审查失败: {e}")
            return None

    async def _post_draft_review(self, draft: dict, review_data: dict):
        """发布文章草稿的AI味审查报告"""
        try:
            title = draft.get('title', '未命名')
            scores = review_data.get('scores', {})
            overall = review_data.get('overall_score', 0)
            strengths = review_data.get('strengths', [])
            weaknesses = review_data.get('weaknesses', [])
            ai_indicators = review_data.get('ai_indicators', [])
            humanization_tips = review_data.get('humanization_tips', [])
            rewrite_suggestions = review_data.get('rewrite_suggestions', [])
            verdict = review_data.get('verdict', '')

            # 构建审查报告
            review_text = f"# 🤖 AI味审查报告\n\n"
            review_text += f"**文章**: 《{title}》\n\n"
            review_text += f"## 📊 人味评分\n\n"
            review_text += f"- **原创性**: {scores.get('originality', 0)}/10\n"
            review_text += f"- **自然度**: {scores.get('naturalness', 0)}/10\n"
            review_text += f"- **情感度**: {scores.get('emotionality', 0)}/10\n"
            review_text += f"- **口语化**: {scores.get('colloquialism', 0)}/10\n\n"
            review_text += f"**综合评分**: {overall}/10\n\n"

            if strengths:
                review_text += f"## ✅ 人味亮点\n\n"
                for s in strengths:
                    review_text += f"- {s}\n"
                review_text += "\n"

            if ai_indicators:
                review_text += f"## 🚨 AI痕迹检测\n\n"
                for ai in ai_indicators[:5]:
                    indicator = ai.get('indicator', '')
                    examples = ai.get('examples', [])
                    severity = ai.get('severity', '')
                    review_text += f"- **{indicator}** (严重度:{severity})\n"
                    if examples:
                        review_text += f"  示例: {', '.join(examples[:2])}\n"
                review_text += "\n"

            if rewrite_suggestions:
                review_text += f"## ✍️ 改写建议\n\n"
                for rw in rewrite_suggestions[:3]:
                    original = rw.get('original', '')
                    suggested = rw.get('suggested', '')
                    review_text += f"- 原文: 「{original}」\n"
                    review_text += f"  改为: 「{suggested}」\n"
                review_text += "\n"

            if humanization_tips:
                review_text += f"## 💡 人性化技巧\n\n"
                for tip in humanization_tips[:5]:
                    review_text += f"- {tip}\n"
                review_text += "\n"

            review_text += f"## 📝 审查结论\n\n{verdict}\n"
            review_text += f"\n---\n*🤖 AI味审查员*"

            await self._send_channel_message("创作工坊", review_text)

        except Exception as e:
            logger.error(f"发布AI味审查报告失败: {e}")

    # ========== 创作工坊文章自动审查 ==========

    @on_event("creation.draft_ready")
    async def handle_draft_ready(self, context):
        """
        自动审查创作工坊完成的文章
        当 Writer 完成文章后自动触发
        """
        try:
            event_data = context.incoming_event.payload
            draft = event_data.get('draft', {})
            session_id = event_data.get('session_id')
            draft_id = event_data.get('draft_id')

            if not draft:
                logger.warning("收到 creation.draft_ready 但没有 draft 数据")
                return

            title = draft.get('title', '未命名')
            logger.info(f"🤖 自动审查创作文章: {title}")

            # 生成审查
            review_data = await self._generate_draft_review(draft)

            if review_data:
                # 不直接发送详细报告，而是通过事件传递完整数据
                # 由 creation_coordinator 统一控制输出

                # 发送审查完成事件（包含完整审查数据用于汇总和按需展示）
                await self.send_event(Event(
                    event_name="creation.review_completed",
                    source_id=self.agent_id,
                    payload={
                        "session_id": session_id,
                        "draft_id": draft_id,
                        "review_type": "ai_flavor",
                        "overall_score": review_data.get('overall_score', 0),
                        "verdict": review_data.get('verdict', ''),
                        "suggestions": review_data.get('humanization_tips', []),
                        # 传递完整审查数据用于按需展示详细报告
                        "full_review": review_data,
                        "draft_title": title
                    }
                ))

                logger.info(f"✅ AI味自动审查完成: {title}")
            else:
                logger.error(f"❌ AI味自动审查失败: {title}")

        except Exception as e:
            logger.error(f"❌ 处理 creation.draft_ready 失败: {e}", exc_info=True)

    # ========== RSS 内容自动评审功能 ==========

    @on_event("content.tagged")
    async def handle_content_tagged(self, event):
        """处理 content.tagged 事件"""
        try:
            payload = event.get("payload", {})
            content_id = payload.get("content_id")
            
            if not content_id:
                logger.warning("Received event without content_id")
                return
            
            logger.info(f"Reviewing content from business perspective: {content_id}")
            
            # 获取内容
            content_data = self.db.get_content(content_id)
            if not content_data:
                logger.error(f"Content not found: {content_id}")
                return
            
            # 生成商业评审
            review_data = await self._generate_review(content_data)
            
            if review_data:
                # 发送到 Forum
                await self._post_review_to_forum(content_data, review_data)
                
                # 发送事件通知其他 Agent
                await self._emit_review_completed(content_id, "business", review_data)
                
                logger.info(f"Business review completed for: {content_id}")
            else:
                logger.error(f"Failed to generate business review for: {content_id}")
        
        except Exception as e:
            logger.error(f"Error handling content.tagged: {str(e)}")
    
    async def _generate_review(self, content_data: dict) -> dict:
        """生成商业评审"""
        try:
            title = content_data['title']
            source = content_data.get('source', 'Unknown')
            category = content_data.get('category', 'tech')
            summary = content_data.get('summary_paragraph', '')
            key_points = content_data.get('key_points', [])
            
            if not summary:
                logger.warning(f"No summary available for business review: {title}")
                return None
            
            # 格式化提示词
            system_prompt, user_prompt = critic_business.format_prompt(
                title=title,
                source=source,
                category=category,
                summary=summary,
                key_points=key_points
            )
            
            # 调用 LLM
            logger.info(f"Calling LLM for business review: {title}")
            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=8000
            )
            
            if not result:
                logger.error("LLM returned empty result")
                return None
            
            logger.info(f"Business review completed with score: {result.get('overall_score', 0)}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating business review: {str(e)}")
            return None
    
    async def _post_review_to_forum(self, content_data: dict, review_data: dict):
        """将评审发布到 Forum"""
        try:
            title = content_data['title']
            scores = review_data.get('scores', {})
            overall = review_data.get('overall_score', 0)
            strengths = review_data.get('strengths', [])
            weaknesses = review_data.get('weaknesses', [])
            market_analysis = review_data.get('market_analysis', {})
            concerns = review_data.get('business_concerns', [])
            recommendations = review_data.get('recommendations', [])
            verdict = review_data.get('verdict', '')
            
            # 构建评审内容
            review_text = f"# 💼 商业分析报告\n\n"
            review_text += f"**内容**: {title}\n\n"
            review_text += f"## 📊 商业评分\n\n"
            review_text += f"- **商业潜力**: {scores.get('business_potential', 0)}/10\n"
            review_text += f"- **竞争力**: {scores.get('competitiveness', 0)}/10\n"
            review_text += f"- **变现能力**: {scores.get('monetization', 0)}/10\n"
            review_text += f"- **市场时机**: {scores.get('market_timing', 0)}/10\n\n"
            review_text += f"**综合评分**: {overall}/10\n\n"
            
            if market_analysis:
                review_text += f"## 🎯 市场分析\n\n"
                review_text += f"- **目标市场**: {market_analysis.get('target_market', 'N/A')}\n"
                review_text += f"- **市场规模**: {market_analysis.get('market_size', 'N/A')}\n"
                review_text += f"- **竞争程度**: {market_analysis.get('competition', 'N/A')}\n\n"
            
            if strengths:
                review_text += f"## ✅ 商业优势\n\n"
                for s in strengths:
                    review_text += f"- {s}\n"
                review_text += "\n"
            
            if weaknesses:
                review_text += f"## ⚠️ 商业挑战\n\n"
                for w in weaknesses:
                    review_text += f"- {w}\n"
                review_text += "\n"
            
            if concerns:
                review_text += f"## 🚨 关键问题\n\n"
                for c in concerns:
                    review_text += f"- {c}\n"
                review_text += "\n"
            
            if recommendations:
                review_text += f"## 💡 战略建议\n\n"
                for r in recommendations:
                    review_text += f"- {r}\n"
                review_text += "\n"
            
            review_text += f"## 📝 总结\n\n{verdict}\n"
            
            await self._send_channel_message("创作工坊", review_text)
            
        except Exception as e:
            logger.error(f"Error posting review to forum: {str(e)}")
    
    async def _emit_review_completed(self, content_id: str, review_type: str, review_data: dict):
        """发送评审完成事件"""
        try:
            event = Event(
                event_name="content.reviewed",
                source_id=self.agent_id,
                payload={
                    "content_id": content_id,
                    "review_type": review_type,
                    "overall_score": review_data.get('overall_score'),
                    "verdict": review_data.get('verdict')
                }
            )
            await self.send_event(event)
            logger.info(f"Emitted content.reviewed event for: {content_id}")
        except Exception as e:
            logger.error(f"Failed to emit content.reviewed event: {str(e)}")
    
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
    """运行 AI Flavor Reviewer Agent"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Flavor Reviewer Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    args = parser.parse_args()

    # 配置日志
    log_file = Path(__file__).parent.parent / 'logs' / 'agents' / 'critic_ai_flavor.log'
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

    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    agent = AIFlavorReviewerAgent()

    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )

        logger.info(f"AI Flavor Reviewer Agent running. Press Ctrl+C to stop.")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())