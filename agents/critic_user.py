#!/usr/bin/env python3
"""
舆情风险审查员 Agent - 评估内容可能引发的舆论风险

功能：
- 监听 content.tagged 事件自动审查
- 支持 @ 触发：在「创作工坊」频道 @舆情审查 审查最近文章
- 评估争议性话题、群体冒犯、舆论风险等
- 给出风险规避建议
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
from config.prompts import critic_user
import logging

logger = logging.getLogger(__name__)


class PublicOpinionReviewerAgent(WorkerAgent):
    """舆情风险审查员 Agent - 舆论风险评估"""

    default_agent_id = "舆情审查"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_llm_client()
        self.db = get_database()
    
    async def on_startup(self):
        """Agent 启动时执行"""
        logger.info("Public Opinion Reviewer Agent started")

        await self._send_channel_message(
            "通用频道",
            "🔥 舆情风险审查员已上线！\n"
            "📝 在「创作工坊」频道 @舆情审查 即可评估内容的舆论风险"
        )

    async def on_shutdown(self):
        """Agent 关闭时执行"""
        logger.info("Public Opinion Reviewer Agent stopped")

    # ========== @ 触发功能 ==========

    @on_event("thread.channel_message.notification")
    async def handle_mention(self, context):
        """
        处理 @ 消息
        当用户在创作工坊 @舆情审查 时触发
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
            if user_id == '舆情审查':
                return

            # 检查是否 @ 了舆情审查
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
                f"🔥 正在进行舆情风险评估「{draft.get('title', '未命名')}」...\n"
                f"⏱️ 请稍候，马上给出审查结果~"
            )

            # 生成审查结果
            review_data = await self._generate_draft_review(draft)

            if review_data:
                # 发送审查结果
                await self._post_draft_review(draft, review_data)
                logger.info(f"✅ 舆情审查完成: {draft.get('title', 'N/A')}")
            else:
                await self._send_channel_message(
                    "创作工坊",
                    "❌ 舆情审查失败，请稍后再试"
                )

        except Exception as e:
            logger.error(f"❌ 处理 @ 消息失败: {e}", exc_info=True)
            await self._send_channel_message("创作工坊", f"❌ 审查失败: {str(e)}")

    def _is_mentioned(self, text: str) -> bool:
        """检查是否被 @ 了"""
        patterns = [
            r'@舆情审查',
            r'@舆情',
            r'@风险',
            r'@争议',
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
        """为文章草稿生成舆情风险审查"""
        try:
            title = draft.get('title', '未命名')
            content = draft.get('content', '')
            word_count = draft.get('word_count', 0)

            # 构建审查提示词
            system_prompt = critic_user.SYSTEM_PROMPT
            user_prompt = f"""请对以下自媒体文章进行舆情风险评估：

**标题**: {title}
**字数**: {word_count}

**文章内容**:
{content[:3000]}

{'...(内容已截取)' if len(content) > 3000 else ''}

请评估文章发布后可能引发的舆论风险，并给出风险规避建议。"""

            # 调用 LLM
            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=8000
            )

            return result

        except Exception as e:
            logger.error(f"生成舆情风险审查失败: {e}")
            return None

    async def _post_draft_review(self, draft: dict, review_data: dict):
        """发布文章草稿的舆情风险审查报告"""
        try:
            title = draft.get('title', '未命名')
            scores = review_data.get('scores', {})
            overall = review_data.get('overall_score', 0)
            strengths = review_data.get('strengths', [])
            weaknesses = review_data.get('weaknesses', [])
            risk_assessment = review_data.get('risk_assessment', {})
            predicted_comments = review_data.get('predicted_comments', [])
            risk_points = review_data.get('risk_points', [])
            mitigation_suggestions = review_data.get('mitigation_suggestions', [])
            verdict = review_data.get('verdict', '')

            # 构建审查报告
            review_text = f"# 🔥 舆情风险审查报告\n\n"
            review_text += f"**文章**: 《{title}》\n\n"
            review_text += f"## 📊 风险评分\n\n"
            review_text += f"- **话题安全**: {scores.get('topic_safety', 0)}/10\n"
            review_text += f"- **表述中立**: {scores.get('expression_neutrality', 0)}/10\n"
            review_text += f"- **群体友好**: {scores.get('group_friendliness', 0)}/10\n"
            review_text += f"- **舆论预判**: {scores.get('public_opinion_risk', 0)}/10\n\n"
            review_text += f"**综合评分**: {overall}/10\n\n"

            if risk_assessment:
                review_text += f"## 🎯 风险评估\n\n"
                review_text += f"- **风险等级**: {risk_assessment.get('risk_level', 'N/A')}\n"
                controversy = risk_assessment.get('potential_controversy', [])
                if controversy:
                    review_text += f"- **潜在争议**: {', '.join(controversy[:3])}\n"
                affected = risk_assessment.get('affected_groups', [])
                if affected:
                    review_text += f"- **影响群体**: {', '.join(affected[:3])}\n"
                review_text += "\n"

            if predicted_comments:
                review_text += f"## 💬 评论区预判\n\n"
                for pc in predicted_comments[:3]:
                    pc_type = pc.get('type', '')
                    content = pc.get('content', '')
                    prob = pc.get('probability', '')
                    review_text += f"- [{pc_type}] {content} (概率:{prob})\n"
                review_text += "\n"

            if risk_points:
                review_text += f"## 🚨 风险点\n\n"
                for rp in risk_points[:3]:
                    content = rp.get('content', '')
                    risk = rp.get('risk', '')
                    suggestion = rp.get('suggestion', '')
                    review_text += f"- **{content}**\n"
                    review_text += f"  风险: {risk} | 建议: {suggestion}\n"
                review_text += "\n"

            if mitigation_suggestions:
                review_text += f"## 💡 风险规避建议\n\n"
                for ms in mitigation_suggestions[:5]:
                    review_text += f"- {ms}\n"
                review_text += "\n"

            review_text += f"## 📝 审查结论\n\n{verdict}\n"
            review_text += f"\n---\n*🔥 舆情风险审查员*"

            await self._send_channel_message("创作工坊", review_text)

        except Exception as e:
            logger.error(f"发布舆情风险审查报告失败: {e}")

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
            logger.info(f"🔥 自动审查创作文章: {title}")

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
                        "review_type": "public_opinion",
                        "overall_score": review_data.get('overall_score', 0),
                        "verdict": review_data.get('verdict', ''),
                        "suggestions": review_data.get('mitigation_suggestions', []),
                        # 传递完整审查数据用于按需展示详细报告
                        "full_review": review_data,
                        "draft_title": title
                    }
                ))

                logger.info(f"✅ 舆情自动审查完成: {title}")
            else:
                logger.error(f"❌ 舆情自动审查失败: {title}")

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
            
            logger.info(f"Reviewing content from UX perspective: {content_id}")
            
            # 获取内容
            content_data = self.db.get_content(content_id)
            if not content_data:
                logger.error(f"Content not found: {content_id}")
                return
            
            # 生成 UX 评审
            review_data = await self._generate_review(content_data)
            
            if review_data:
                # 发送到 Forum
                await self._post_review_to_forum(content_data, review_data)
                
                # 发送事件通知其他 Agent
                await self._emit_review_completed(content_id, "user_experience", review_data)
                
                logger.info(f"UX review completed for: {content_id}")
            else:
                logger.error(f"Failed to generate UX review for: {content_id}")
        
        except Exception as e:
            logger.error(f"Error handling content.tagged: {str(e)}")
    
    async def _generate_review(self, content_data: dict) -> dict:
        """生成用户体验评审"""
        try:
            title = content_data['title']
            source = content_data.get('source', 'Unknown')
            category = content_data.get('category', 'tech')
            summary = content_data.get('summary_paragraph', '')
            key_points = content_data.get('key_points', [])
            
            if not summary:
                logger.warning(f"No summary available for UX review: {title}")
                return None
            
            # 格式化提示词
            system_prompt, user_prompt = critic_user.format_prompt(
                title=title,
                source=source,
                category=category,
                summary=summary,
                key_points=key_points
            )
            
            # 调用 LLM
            logger.info(f"Calling LLM for UX review: {title}")
            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=8000
            )
            
            if not result:
                logger.error("LLM returned empty result")
                return None
            
            logger.info(f"UX review completed with score: {result.get('overall_score', 0)}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating UX review: {str(e)}")
            return None
    
    async def _post_review_to_forum(self, content_data: dict, review_data: dict):
        """将评审发布到 Forum"""
        try:
            title = content_data['title']
            scores = review_data.get('scores', {})
            overall = review_data.get('overall_score', 0)
            strengths = review_data.get('strengths', [])
            weaknesses = review_data.get('weaknesses', [])
            ux_info = review_data.get('user_experience', {})
            concerns = review_data.get('ux_concerns', [])
            recommendations = review_data.get('recommendations', [])
            verdict = review_data.get('verdict', '')
            
            # 构建评审内容
            review_text = f"# 👥 用户体验评审报告\n\n"
            review_text += f"**内容**: {title}\n\n"
            review_text += f"## 📊 体验评分\n\n"
            review_text += f"- **可读性**: {scores.get('readability', 0)}/10\n"
            review_text += f"- **实用价值**: {scores.get('practical_value', 0)}/10\n"
            review_text += f"- **内容组织**: {scores.get('content_organization', 0)}/10\n"
            review_text += f"- **示例质量**: {scores.get('example_quality', 0)}/10\n\n"
            review_text += f"**综合评分**: {overall}/10\n\n"
            
            if ux_info:
                review_text += f"## 🎯 用户画像\n\n"
                review_text += f"- **目标受众**: {ux_info.get('target_audience', 'N/A')}\n"
                review_text += f"- **难度等级**: {ux_info.get('difficulty_level', 'N/A')}\n"
                review_text += f"- **学习曲线**: {ux_info.get('learning_curve', 'N/A')}\n\n"
            
            if strengths:
                review_text += f"## ✅ 体验优势\n\n"
                for s in strengths:
                    review_text += f"- {s}\n"
                review_text += "\n"
            
            if weaknesses:
                review_text += f"## ⚠️ 体验不足\n\n"
                for w in weaknesses:
                    review_text += f"- {w}\n"
                review_text += "\n"
            
            if concerns:
                review_text += f"## 🚨 用户痛点\n\n"
                for c in concerns:
                    review_text += f"- {c}\n"
                review_text += "\n"
            
            if recommendations:
                review_text += f"## 💡 优化建议\n\n"
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
    """运行 Public Opinion Reviewer Agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Public Opinion Reviewer Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    args = parser.parse_args()

    # 配置日志
    log_file = Path(__file__).parent.parent / 'logs' / 'agents' / 'critic_public_opinion.log'
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

    agent = PublicOpinionReviewerAgent()

    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )

        logger.info(f"Public Opinion Reviewer Agent running. Press Ctrl+C to stop.")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())