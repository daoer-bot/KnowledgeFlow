"""
Creation Coordinator Agent (v3)
创作协调器 - 统一处理用户创作请求的核心组件

v3 改进：
- 使用 LLM 进行意图识别，替代硬编码的正则规则
- 更灵活地理解用户自然语言输入

状态流转：
  idle → confirming_materials → generating_outlines → waiting_selection
       → editing_outline (可选) → confirming_start → writing
       → reviewing → waiting_optimization → optimizing (可选) → completed
"""

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from openagents.agents.worker_agent import WorkerAgent, on_event
from openagents.models.event import Event
from tools.session_manager import SessionState

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CreationCoordinator(WorkerAgent):
    """创作协调器 v3 - 使用 LLM 意图识别"""

    default_agent_id = "创作协调器"

    # Agent ID 列表（用于过滤）
    AGENT_IDS = [
        '创作协调器', '大纲生成器', '文章写作器',
        '敏感词审查', 'AI味审查', '舆情审查',
        'RSS阅读器', '网页抓取器', '摘要生成器', '标签生成器'
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = None
        self.session_manager = None
        self.llm = None
        self.intent_detector = None
        # 评审追踪：session_id -> {technical: {score, suggestions}, ...}
        self.pending_reviews = {}

    async def on_startup(self):
        """Agent 启动时执行"""
        logger.info("🎨 Creation Coordinator v3 启动中...")

        # 导入依赖
        from tools.database import get_database
        from tools.session_manager import SessionManager
        from tools.llm_client import get_llm_client
        from tools.intent_detector import IntentDetector

        self.db = get_database()
        self.session_manager = SessionManager(self.db)
        self.llm = get_llm_client()
        self.intent_detector = IntentDetector(self.llm)

        # 启动定期清理任务
        asyncio.create_task(self._cleanup_loop())

        logger.info("✅ Creation Coordinator v3 初始化完成")

        # 发送上线通知
        await self._send_message(
            "🎨 **创作协调器 v3 已上线！**\n\n"
            "💡 在「创作工坊」频道发送创作请求开始吧~\n\n"
            "📝 示例：写一篇关于AI编程助手的文章\n\n"
            "✨ 新功能：智能意图识别、自然语言交互"
        )

    async def on_shutdown(self):
        """Agent 关闭时执行"""
        logger.info("Creation Coordinator stopped")

    # ==================== 工具方法 ====================

    async def _send_message(self, text: str):
        """发送消息到创作工坊频道"""
        try:
            ws = self.workspace()
            await ws.channel('创作工坊').post(text)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")

    async def _cleanup_loop(self):
        """定期清理过期会话"""
        while True:
            try:
                await asyncio.sleep(3600)
                await self.session_manager.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"清理会话失败: {e}")

    def _is_agent_message(self, user_id: str) -> bool:
        """检查是否是 Agent 消息"""
        return user_id in self.AGENT_IDS

    def _is_mention_critic(self, text: str) -> bool:
        """检查是否是 @ 评论员的消息"""
        critic_patterns = [
            r'@敏感词审查', r'@技术', r'@technical',
            r'@AI味审查', r'@商业', r'@business',
            r'@舆情审查', r'@用户体验', r'@体验', r'@UX', r'@ux',
        ]
        for pattern in critic_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _parse_topic(self, text: str) -> Optional[str]:
        """解析创作主题"""
        # 模式1: "写一篇关于 XXX 的文章"
        pattern1 = r'写.*?关于[《【\s]*(.+?)[》】\s]*的'
        match = re.search(pattern1, text)
        if match:
            return match.group(1).strip()

        # 模式2: "创作主题：XXX"
        pattern2 = r'(?:创作)?主题[：:]\s*(.+?)(?:[，,\n]|$)'
        match = re.search(pattern2, text)
        if match:
            return match.group(1).strip()

        # 模式3: 直接是主题（简短文本，不包含问号和特殊指令）
        if len(text) < 100 and '?' not in text and '？' not in text:
            # 排除各种指令
            excluded = ['选择', '确认', '开始', '继续', '修改', '优化', '是', '否', '好', '不']
            if not re.match(r'^\d+$', text) and not any(e in text for e in excluded):
                return text.strip()

        return None

    def _parse_number(self, text: str) -> Optional[int]:
        """解析数字选择"""
        text = text.strip()
        if text.isdigit():
            return int(text)
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
        return None

    def _parse_yes_no(self, text: str) -> Optional[bool]:
        """解析是/否回答"""
        text = text.strip().lower()
        yes_patterns = ['是', '好', '确认', '开始', '继续', 'yes', 'y', 'ok', '可以', '行']
        no_patterns = ['否', '不', '取消', '重新', 'no', 'n', '算了']

        for p in yes_patterns:
            if p in text:
                return True
        for p in no_patterns:
            if p in text:
                return False
        return None
    
    @on_event("thread.channel_message.notification")
    async def handle_user_message(self, context):
        """
        统一处理所有用户消息 - 使用 LLM 意图识别
        """
        try:
            payload = context.incoming_event.payload
            channel = payload.get('channel', '')
            text = payload.get('content', {}).get('text', '').strip()
            user_id = payload.get('source_id', '')

            # 只处理创作工坊频道
            if channel != '创作工坊':
                return

            # 忽略 Agent 消息和空消息
            if self._is_agent_message(user_id) or not text:
                return

            # 忽略 @ 评论员的消息
            if self._is_mention_critic(text):
                return

            # 获取或创建会话
            session = await self.session_manager.get_or_create_session(user_id)
            logger.info(f"📨 收到用户消息: user={user_id}, state={session.state}, text={text[:50]}...")

            # 使用 LLM 识别意图
            from tools.intent_detector import UserIntent

            intent_context = {
                "topic": session.topic,
                "outline_count": len(session.outline_ids) if session.outline_ids else 0
            }

            intent_result = await self.intent_detector.detect_intent(
                user_input=text,
                current_state=session.state,
                context=intent_context
            )

            logger.info(f"🧠 意图识别: {intent_result.intent.value} (置信度: {intent_result.confidence:.2f})")
            logger.info(f"   推理: {intent_result.reasoning}")
            logger.info(f"   提取数据: {intent_result.extracted_data}")

            # 根据意图和状态路由处理
            await self._route_by_intent(session, text, intent_result)

        except Exception as e:
            logger.error(f"❌ 处理用户消息失败: {e}", exc_info=True)
            await self._send_message(f"❌ 处理失败: {str(e)}")

    async def _route_by_intent(self, session, text: str, intent_result):
        """根据意图和状态路由到对应处理器"""
        from tools.intent_detector import UserIntent

        intent = intent_result.intent
        data = intent_result.extracted_data
        state = session.state

        # 取消操作 - 任何状态都可以
        if intent == UserIntent.CANCEL:
            await self.session_manager.reset_session(session)
            await self._send_message("❌ 已取消当前任务\n💡 输入新主题开始创作")
            return

        # 新主题 - 只在 idle/completed 状态，或者明确是新主题时
        if intent == UserIntent.NEW_TOPIC:
            topic = data.get("topic", text)
            if state in [SessionState.IDLE, SessionState.COMPLETED]:
                await self._handle_new_creation(session, topic)
            elif state not in [SessionState.WRITING, SessionState.REVIEWING, SessionState.OPTIMIZING]:
                # 其他状态下，如果是新主题，重置会话
                logger.info(f"🔄 检测到新主题，重置会话")
                await self.session_manager.reset_session(session)
                session = await self.session_manager.get_or_create_session(session.user_id)
                await self._handle_new_creation(session, topic)
            else:
                await self._send_message(
                    f"⏳ 当前正在{session.get_state_name()}，请等待完成后再开始新创作\n"
                    f"💡 输入「取消」可中止当前任务"
                )
            return

        # 根据当前状态处理其他意图
        if state == SessionState.IDLE:
            await self._handle_idle(session, text)

        elif state == SessionState.CONFIRMING_MATERIALS:
            if intent == UserIntent.CONFIRM_YES:
                await self._confirm_materials_yes(session)
            elif intent == UserIntent.CONFIRM_NO:
                await self._confirm_materials_no(session)
            else:
                await self._send_message(
                    "❓ 请回复：\n\n"
                    "• **是/确认** - 使用这些素材\n"
                    "• **否/不用** - 不使用素材，直接生成"
                )

        elif state == SessionState.GENERATING_OUTLINES:
            await self._handle_processing(session, text)

        elif state == SessionState.WAITING_SELECTION:
            if intent == UserIntent.SELECT_OUTLINE:
                num = data.get("number", 1)
                # 确保 num 是整数类型（LLM 可能返回字符串）
                num = int(num) if num is not None else 1
                await self._select_outline(session, num)
            elif intent == UserIntent.MODIFY_OUTLINE:
                num = data.get("number", 1)
                # 确保 num 是整数类型
                num = int(num) if num is not None else 1
                await self._enter_editing_mode(session, num)
            else:
                await self._send_message(
                    f"❓ 请选择大纲方案：\n\n"
                    f"• 输入数字（1-{len(session.outline_ids)}）选择方案\n\n"
                    f"• 输入「修改」编辑大纲"
                )

        elif state == SessionState.EDITING_OUTLINE:
            if intent == UserIntent.FINISH_EDITING:
                await self._finish_editing(session)
            elif intent == UserIntent.EDIT_INSTRUCTION:
                instruction = data.get("instruction", text)
                await self._apply_edit_instruction(session, instruction)
            else:
                # 默认当作编辑指令处理
                await self._apply_edit_instruction(session, text)

        elif state == SessionState.CONFIRMING_START:
            if intent == UserIntent.CONFIRM_YES:
                await self._start_writing(session)
            elif intent == UserIntent.CONFIRM_NO or intent == UserIntent.MODIFY_OUTLINE:
                session.state = SessionState.WAITING_SELECTION
                await self.session_manager.update_session(session)
                await self._send_message("🔄 请重新选择大纲方案（输入数字 1-3）")
            else:
                await self._send_message(
                    "❓ 请回复：\n\n"
                    "• **是/开始** - 开始写作\n\n"
                    "• **修改** - 修改大纲\n\n"
                    "• **重选** - 重新选择方案"
                )

        elif state == SessionState.WRITING:
            await self._handle_processing(session, text)

        elif state == SessionState.PAUSED_WRITING:
            if intent == UserIntent.CONTINUE_WRITING:
                await self._continue_writing(session)
            elif intent == UserIntent.REWRITE_SECTION:
                await self._rewrite_section(session, text)
            elif intent == UserIntent.STOP_WRITING:
                await self._stop_writing(session)
            else:
                await self._send_message(
                    "❓ 请回复：\n\n"
                    "• **继续** - 继续写作下一章\n\n"
                    "• **重写这章** - 重写当前章节\n\n"
                    "• **结束** - 保存当前内容"
                )

        elif state == SessionState.REVIEWING:
            await self._handle_processing(session, text)

        elif state == SessionState.WAITING_OPTIMIZATION:
            if intent == UserIntent.REQUEST_OPTIMIZE:
                await self._request_optimization(session)
            elif intent == UserIntent.FINISH_CREATION:
                await self._finish_creation(session)
            elif intent == UserIntent.VIEW_DETAIL_REPORT:
                await self._show_detail_reports(session)
            else:
                await self._send_message(
                    "❓ 请选择：\n\n"
                    "• **详细** - 查看各评审员的详细报告\n\n"
                    "• **优化** - 根据评审建议优化文章\n\n"
                    "• **完成** - 保存当前版本"
                )

        elif state == SessionState.OPTIMIZING:
            await self._handle_processing(session, text)

        elif state == SessionState.COMPLETED:
            await self._handle_completed(session, text)

        else:
            await self._handle_unknown_state(session, text)

    # ==================== 意图处理方法 ====================

    async def _confirm_materials_yes(self, session):
        """确认使用素材"""
        session.confirmed_material_ids = session.material_ids
        session.state = SessionState.GENERATING_OUTLINES
        await self.session_manager.update_session(session)

        await self._send_message(
            f"✅ 已确认使用 {len(session.material_ids)} 篇素材\n\n"
            f"📝 正在生成大纲方案...\n\n"
            f"⏱️ 预计 30 秒"
        )

        await self._request_outlines(session)

    async def _confirm_materials_no(self, session):
        """不使用素材"""
        session.confirmed_material_ids = []
        session.state = SessionState.GENERATING_OUTLINES
        await self.session_manager.update_session(session)

        await self._send_message(
            f"✅ 将不使用知识库素材，直接生成大纲\n\n"
            f"📝 正在生成大纲方案...\n\n"
            f"⏱️ 预计 30 秒"
        )

        await self._request_outlines(session)

    async def _select_outline(self, session, num: int):
        """选择大纲"""
        if num < 1 or num > len(session.outline_ids):
            await self._send_message(
                f"❌ 方案 {num} 不存在，请输入 1-{len(session.outline_ids)} 之间的数字"
            )
            return

        selected_id = session.outline_ids[num - 1]
        session.selected_outline_id = selected_id
        session.state = SessionState.CONFIRMING_START
        await self.session_manager.update_session(session)

        await self._send_message(
            f"✅ 已选择方案 {num}\n\n\n\n"
            f"📋 确认开始写作吗？\n\n\n\n"
            f"• 回复「**是/开始**」- 开始自动写作\n\n"
            f"• 回复「**修改**」- 返回修改大纲\n\n"
            f"• 回复「**重选**」- 重新选择方案"
        )

    async def _enter_editing_mode(self, session, num: int):
        """进入大纲编辑模式"""
        if num < 1 or num > len(session.outline_ids):
            num = 1  # 默认编辑第一个

        session.selected_outline_id = session.outline_ids[num - 1]
        session.state = SessionState.EDITING_OUTLINE
        await self.session_manager.update_session(session)

        await self._send_message(
            f"📝 进入大纲编辑模式（方案 {num}）\n\n\n\n"
            f"请描述你想要的修改，例如：\n\n"
            f"• 把第三章改成「实战案例」\n\n"
            f"• 增加一个关于性能优化的章节\n\n"
            f"• 删除最后一章\n\n\n\n"
            f"💡 输入「完成」结束编辑"
        )

    async def _finish_editing(self, session):
        """完成编辑"""
        session.state = SessionState.CONFIRMING_START
        await self.session_manager.update_session(session)

        await self._send_message(
            f"✅ 大纲编辑完成\n\n\n\n"
            f"📋 确认开始写作吗？\n\n"
            f"• 回复「**是/开始**」- 开始写作\n\n"
            f"• 回复「**继续修改**」- 继续编辑"
        )

    async def _apply_edit_instruction(self, session, instruction: str):
        """应用编辑指令"""
        event = Event(
            event_name="creation.modify_outline",
            source_id=self.agent_id,
            payload={
                "session_id": session.id,
                "outline_id": session.selected_outline_id,
                "modification": instruction
            }
        )
        await self.send_event(event)

        await self._send_message(
            f"📝 正在根据你的要求修改大纲...\n\n"
            f"修改内容：{instruction[:50]}..."
        )

    async def _start_writing(self, session):
        """开始写作"""
        session.state = SessionState.WRITING
        await self.session_manager.update_session(session)

        await self._send_message(
            f"✍️ 开始创作...\n\n\n\n"
            f"📊 将实时显示写作进度"
        )

        await self._request_writing(session)

    async def _continue_writing(self, session):
        """继续写作"""
        session.state = SessionState.WRITING
        await self.session_manager.update_session(session)

        event = Event(
            event_name="creation.continue_writing",
            source_id=self.agent_id,
            payload={
                "session_id": session.id,
                "section_index": session.current_section_index + 1
            }
        )
        await self.send_event(event)
        await self._send_message("✍️ 继续写作下一章节...")

    async def _rewrite_section(self, session, instruction: str):
        """重写章节"""
        event = Event(
            event_name="creation.rewrite_section",
            source_id=self.agent_id,
            payload={
                "session_id": session.id,
                "section_index": session.current_section_index,
                "instruction": instruction
            }
        )
        await self.send_event(event)
        await self._send_message("📝 正在重写当前章节...")

    async def _stop_writing(self, session):
        """停止写作"""
        session.state = SessionState.COMPLETED
        await self.session_manager.update_session(session)
        await self._send_message(
            "✅ 写作已停止，当前内容已保存\n\n"
            "💡 输入新主题开始下一篇创作"
        )

    async def _request_optimization(self, session):
        """请求优化"""
        session.state = SessionState.OPTIMIZING
        session.optimization_count += 1
        await self.session_manager.update_session(session)

        event = Event(
            event_name="creation.optimize_draft",
            source_id=self.agent_id,
            payload={
                "session_id": session.id,
                "draft_id": session.draft_id,
                "suggestions": session.review_suggestions
            }
        )
        await self.send_event(event)

        await self._send_message(
            f"🔧 正在根据评审建议优化文章...\n\n"
            f"（第 {session.optimization_count} 次优化）"
        )

    async def _finish_creation(self, session):
        """完成创作"""
        session.state = SessionState.COMPLETED
        await self.session_manager.update_session(session)

        await self._send_message(
            f"🎉 **创作完成！**\n\n\n\n"
            f"📚 文章已保存到知识库\n\n"
            f"💡 输入新主题开始下一篇创作"
        )

    async def _show_detail_reports(self, session):
        """展示各审查员的详细报告"""
        full_reviews = getattr(session, 'full_reviews', {})

        if not full_reviews:
            await self._send_message(
                "📭 暂无详细审查数据\n\n"
                "💡 请选择「优化」或「完成」继续"
            )
            return

        # 敏感词审查详细报告
        sensitive_review = full_reviews.get('sensitive', {})
        if sensitive_review:
            await self._send_sensitive_detail_report(sensitive_review)

        # AI味审查详细报告
        ai_flavor_review = full_reviews.get('ai_flavor', {})
        if ai_flavor_review:
            await self._send_ai_flavor_detail_report(ai_flavor_review)

        # 舆情审查详细报告
        public_opinion_review = full_reviews.get('public_opinion', {})
        if public_opinion_review:
            await self._send_public_opinion_detail_report(public_opinion_review)

        # 发送后续操作提示
        await self._send_message(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 **请选择**：\n\n"
            "• 回复「**优化**」- 根据建议自动优化\n\n"
            "• 回复「**完成**」- 保存当前版本"
        )

    async def _send_sensitive_detail_report(self, review_data: dict):
        """发送敏感词审查详细报告"""
        scores = review_data.get('scores', {})
        overall = review_data.get('overall_score', 0)
        strengths = review_data.get('strengths', [])
        weaknesses = review_data.get('weaknesses', [])
        sensitive_words = review_data.get('sensitive_words', [])
        risk_areas = review_data.get('risk_areas', [])
        recommendations = review_data.get('recommendations', [])
        verdict = review_data.get('verdict', '')

        msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "# 🚫 敏感违禁词审查详细报告\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n\n"
        msg += f"## 📊 合规评分\n\n"
        msg += f"- **政治合规**: {scores.get('political_compliance', 0)}/10\n\n"
        msg += f"- **广告合规**: {scores.get('ad_compliance', 0)}/10\n\n"
        msg += f"- **内容健康**: {scores.get('content_health', 0)}/10\n\n"
        msg += f"- **表述规范**: {scores.get('expression_standard', 0)}/10\n\n\n\n"
        msg += f"**综合评分**: {overall}/10\n\n\n\n"

        if strengths:
            msg += f"## ✅ 合规亮点\n\n"
            for s in strengths:
                msg += f"- {s}\n\n"
            msg += "\n\n"

        if sensitive_words:
            msg += f"## 🚨 敏感词检测\n\n"
            for sw in sensitive_words[:5]:
                word = sw.get('word', '')
                location = sw.get('location', '')
                risk = sw.get('risk_level', '')
                suggestion = sw.get('suggestion', '')
                msg += f"- **{word}** ({location}) - 风险:{risk}\n\n"
                msg += f"  建议: {suggestion}\n\n"
            msg += "\n\n"

        if risk_areas:
            msg += f"## ⚠️ 风险领域\n\n"
            for r in risk_areas:
                msg += f"- {r}\n\n"
            msg += "\n\n"

        if recommendations:
            msg += f"## 💡 修改建议\n\n"
            for r in recommendations:
                msg += f"- {r}\n\n"
            msg += "\n\n"

        msg += f"## 📝 审查结论\n\n{verdict}\n\n"
        msg += f"---\n*🚫 敏感词审查员*\n\n"

        await self._send_message(msg)

    async def _send_ai_flavor_detail_report(self, review_data: dict):
        """发送AI味审查详细报告"""
        scores = review_data.get('scores', {})
        overall = review_data.get('overall_score', 0)
        strengths = review_data.get('strengths', [])
        weaknesses = review_data.get('weaknesses', [])
        ai_indicators = review_data.get('ai_indicators', [])
        humanization_tips = review_data.get('humanization_tips', [])
        rewrite_suggestions = review_data.get('rewrite_suggestions', [])
        verdict = review_data.get('verdict', '')

        msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "# 🤖 AI味审查详细报告\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n\n"
        msg += f"## 📊 人味评分\n\n"
        msg += f"- **原创性**: {scores.get('originality', 0)}/10\n\n"
        msg += f"- **自然度**: {scores.get('naturalness', 0)}/10\n\n"
        msg += f"- **情感度**: {scores.get('emotionality', 0)}/10\n\n"
        msg += f"- **口语化**: {scores.get('colloquialism', 0)}/10\n\n\n\n"
        msg += f"**综合评分**: {overall}/10\n\n\n\n"

        if strengths:
            msg += f"## ✅ 人味亮点\n\n"
            for s in strengths:
                msg += f"- {s}\n\n"
            msg += "\n\n"

        if ai_indicators:
            msg += f"## 🚨 AI痕迹检测\n\n"
            for ai in ai_indicators[:5]:
                indicator = ai.get('indicator', '')
                examples = ai.get('examples', [])
                severity = ai.get('severity', '')
                msg += f"- **{indicator}** (严重度:{severity})\n\n"
                if examples:
                    msg += f"  示例: {', '.join(examples[:2])}\n\n"
            msg += "\n\n"

        if rewrite_suggestions:
            msg += f"## ✍️ 改写建议\n\n"
            for rw in rewrite_suggestions[:3]:
                original = rw.get('original', '')
                suggested = rw.get('suggested', '')
                msg += f"- 原文: 「{original}」\n\n"
                msg += f"  改为: 「{suggested}」\n\n"
            msg += "\n\n"

        if humanization_tips:
            msg += f"## 💡 人性化技巧\n\n"
            for tip in humanization_tips[:5]:
                msg += f"- {tip}\n\n"
            msg += "\n\n"

        msg += f"## 📝 审查结论\n\n{verdict}\n\n"
        msg += f"---\n*🤖 AI味审查员*\n\n"

        await self._send_message(msg)

    async def _send_public_opinion_detail_report(self, review_data: dict):
        """发送舆情风险审查详细报告"""
        scores = review_data.get('scores', {})
        overall = review_data.get('overall_score', 0)
        strengths = review_data.get('strengths', [])
        weaknesses = review_data.get('weaknesses', [])
        risk_assessment = review_data.get('risk_assessment', {})
        predicted_comments = review_data.get('predicted_comments', [])
        risk_points = review_data.get('risk_points', [])
        mitigation_suggestions = review_data.get('mitigation_suggestions', [])
        verdict = review_data.get('verdict', '')

        msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "# 🔥 舆情风险审查详细报告\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n\n"
        msg += f"## 📊 风险评分\n\n"
        msg += f"- **话题安全**: {scores.get('topic_safety', 0)}/10\n\n"
        msg += f"- **表述中立**: {scores.get('expression_neutrality', 0)}/10\n\n"
        msg += f"- **群体友好**: {scores.get('group_friendliness', 0)}/10\n\n"
        msg += f"- **舆论预判**: {scores.get('public_opinion_risk', 0)}/10\n\n\n\n"
        msg += f"**综合评分**: {overall}/10\n\n\n\n"

        if risk_assessment:
            msg += f"## 🎯 风险评估\n\n"
            msg += f"- **风险等级**: {risk_assessment.get('risk_level', 'N/A')}\n\n"
            controversy = risk_assessment.get('potential_controversy', [])
            if controversy:
                msg += f"- **潜在争议**: {', '.join(controversy[:3])}\n\n"
            affected = risk_assessment.get('affected_groups', [])
            if affected:
                msg += f"- **影响群体**: {', '.join(affected[:3])}\n\n"
            msg += "\n\n"

        if predicted_comments:
            msg += f"## 💬 评论区预判\n\n"
            for pc in predicted_comments[:3]:
                pc_type = pc.get('type', '')
                content = pc.get('content', '')
                prob = pc.get('probability', '')
                msg += f"- [{pc_type}] {content} (概率:{prob})\n\n"
            msg += "\n\n"

        if risk_points:
            msg += f"## 🚨 风险点\n\n"
            for rp in risk_points[:3]:
                content = rp.get('content', '')
                risk = rp.get('risk', '')
                suggestion = rp.get('suggestion', '')
                msg += f"- **{content}**\n\n"
                msg += f"  风险: {risk} | 建议: {suggestion}\n\n"
            msg += "\n\n"

        if mitigation_suggestions:
            msg += f"## 💡 风险规避建议\n\n"
            for ms in mitigation_suggestions[:5]:
                msg += f"- {ms}\n\n"
            msg += "\n\n"

        msg += f"## 📝 审查结论\n\n{verdict}\n\n"
        msg += f"---\n*🔥 舆情风险审查员*\n\n"

        await self._send_message(msg)

    # ==================== 状态处理器 ====================

    async def _handle_idle(self, session, text: str):
        """处理空闲状态"""
        await self._send_message(
            "💡 **开始创作**\n\n"
            "请输入创作主题，例如：\n\n"
            "• 写一篇关于AI编程助手的文章\n\n"
            "• 创作主题：大模型应用开发\n\n"
            "• 直接输入：RAG技术详解"
        )

    async def _handle_new_creation(self, session, topic: str):
        """处理新创作请求 - 先搜索素材"""
        try:
            session.topic = topic
            session.state = SessionState.CONFIRMING_MATERIALS
            await self.session_manager.update_session(session)

            # 通知用户
            await self._send_message(
                f"🎯 收到创作请求：**「{topic}」**\n\n"
                f"🔍 正在搜索知识库中的相关素材..."
            )

            # 发送事件搜索素材
            event = Event(
                event_name="creation.search_materials",
                source_id=self.agent_id,
                payload={
                    "session_id": session.id,
                    "user_id": session.user_id,
                    "topic": topic
                }
            )
            await self.send_event(event)

            logger.info(f"✅ 已发送素材搜索请求: session={session.id}, topic={topic}")

        except Exception as e:
            logger.error(f"❌ 处理新创作请求失败: {e}", exc_info=True)
            await self._send_message(f"❌ 处理失败: {str(e)}")

    async def _handle_processing(self, session, text: str):
        """处理进行中状态（生成大纲/写作/评审/优化）"""
        await self._send_message(
            f"⏳ 正在处理中...\n\n\n\n"
            f"当前状态：{session.get_state_name()}\n\n"
            f"{session.get_progress_info()}\n\n\n\n"
            f"💡 输入「取消」可中止当前任务"
        )

    async def _handle_completed(self, session, text: str):
        """处理已完成状态"""
        await self._send_message(
            "✅ 上一篇创作已完成\n\n\n\n"
            "💡 输入新主题开始下一篇创作"
        )

    async def _handle_unknown_state(self, session, text: str):
        """处理未知状态"""
        logger.warning(f"未知状态: {session.state}")
        await self.session_manager.reset_session(session)
        await self._send_message(
            "⚠️ 会话状态异常，已重置\n\n"
            "💡 请输入创作主题重新开始"
        )

    # ==================== 辅助方法：发送请求 ====================

    async def _request_outlines(self, session):
        """发送大纲生成请求"""
        event = Event(
            event_name="creation.request_outlines",
            source_id=self.agent_id,
            payload={
                "session_id": session.id,
                "user_id": session.user_id,
                "topic": session.topic,
                "material_ids": session.confirmed_material_ids
            }
        )
        await self.send_event(event)
        logger.info(f"✅ 已发送大纲生成请求: session={session.id}")

    async def _request_writing(self, session):
        """发送写作请求"""
        event = Event(
            event_name="creation.start_writing",
            source_id=self.agent_id,
            payload={
                "session_id": session.id,
                "outline_id": session.selected_outline_id,
                "topic": session.topic,
                "writing_mode": session.writing_mode
            }
        )
        await self.send_event(event)
        logger.info(f"✅ 已发送写作请求: session={session.id}")

    # ==================== 事件处理器 ====================

    @on_event("creation.materials_found")
    async def handle_materials_found(self, context):
        """处理素材搜索完成事件"""
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            materials = event_data.get('materials', [])

            logger.info(f"📚 收到素材搜索结果: session={session_id}, 数量={len(materials)}")

            session = await self.session_manager.get_session(session_id)
            if not session:
                logger.error(f"❌ 会话不存在: {session_id}")
                return

            # 保存素材ID
            session.material_ids = [m.get('id') for m in materials if m.get('id')]
            await self.session_manager.update_session(session)

            if materials:
                # 展示找到的素材
                msg = f"🔍 找到 **{len(materials)}** 篇相关素材：\n\n"
                for i, m in enumerate(materials[:5], 1):
                    title = m.get('title', 'N/A')[:40]
                    summary = m.get('summary', '')[:60]
                    msg += f"{i}. **{title}**\n\n"
                    if summary:
                        msg += f"   {summary}...\n\n"
                    msg += "\n\n"

                if len(materials) > 5:
                    msg += f"... 还有 {len(materials) - 5} 篇\n\n"

                msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                msg += "📋 是否基于这些素材生成大纲？\n\n\n\n"
                msg += "• 回复「**是**」- 使用素材\n\n"
                msg += "• 回复「**否**」- 不使用，直接生成"

                await self._send_message(msg)
            else:
                # 没有找到素材，直接生成大纲
                session.confirmed_material_ids = []
                session.state = SessionState.GENERATING_OUTLINES
                await self.session_manager.update_session(session)

                await self._send_message(
                    f"📭 知识库中暂无相关素材\n\n\n\n"
                    f"📝 将直接生成大纲方案...\n\n"
                    f"⏱️ 预计 30 秒"
                )

                await self._request_outlines(session)

        except Exception as e:
            logger.error(f"❌ 处理素材搜索结果失败: {e}", exc_info=True)

    @on_event("creation.outlines_ready")
    async def handle_outlines_ready(self, context):
        """处理大纲生成完成事件"""
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            outlines = event_data.get('outlines', [])
            outline_ids = event_data.get('outline_ids', [])

            logger.info(f"🎉 收到大纲完成事件: session={session_id}, 数量={len(outlines)}")

            session = await self.session_manager.get_session(session_id)
            if not session:
                logger.error(f"❌ 会话不存在: {session_id}")
                return

            # 更新会话状态
            session.state = SessionState.WAITING_SELECTION
            session.outline_ids = outline_ids
            await self.session_manager.update_session(session)

            # 展示大纲给用户
            msg = f"✅ 已为「{session.topic}」生成 **{len(outlines)}** 个大纲方案：\n\n\n\n"

            for i, outline in enumerate(outlines, 1):
                msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                msg += f"📋 **方案 {i}**\n\n"
                msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n\n"

                title = outline.get('title', 'N/A')
                msg += f"📌 **{title}**\n\n\n\n"

                subtitle = outline.get('subtitle') or outline.get('description', '')
                if subtitle:
                    msg += f"📝 {subtitle[:80]}{'...' if len(subtitle) > 80 else ''}\n\n\n\n"

                style = outline.get('style', '')
                if style:
                    msg += f"🏷️ 风格：{style}\n\n"

                audience = outline.get('target_audience', '')
                if audience:
                    msg += f"👥 读者：{audience}\n\n"

                # 章节结构
                structure = outline.get('structure', [])
                if structure:
                    msg += "\n\n📂 **章节**：\n\n"
                    for j, sec in enumerate(structure[:4], 1):
                        sec_title = sec.get('section', '') if isinstance(sec, dict) else str(sec)
                        msg += f"   {j}. {sec_title}\n\n"
                    if len(structure) > 4:
                        msg += f"   ... 共 {len(structure)} 章\n\n"

                words = outline.get('total_estimated_words') or outline.get('estimated_words', 2000)
                msg += f"\n\n📏 约 {words} 字\n\n\n\n"

            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            msg += "💡 **请选择**：\n\n"
            msg += "• 输入数字（1/2/3）选择方案\n\n"
            msg += "• 输入「修改 N」编辑第 N 个方案"

            await self._send_message(msg)
            logger.info(f"✅ 大纲展示完成: session={session_id}")

        except Exception as e:
            logger.error(f"❌ 处理大纲完成事件失败: {e}", exc_info=True)

    @on_event("creation.outline_modified")
    async def handle_outline_modified(self, context):
        """处理大纲修改完成事件"""
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            modified_outline = event_data.get('outline', {})

            session = await self.session_manager.get_session(session_id)
            if not session:
                return

            # 保存修改后的大纲
            session.selected_outline = modified_outline
            await self.session_manager.update_session(session)

            # 展示修改后的大纲
            msg = "✅ 大纲已修改：\n\n\n\n"
            msg += f"📌 **{modified_outline.get('title', 'N/A')}**\n\n\n\n"

            structure = modified_outline.get('structure', [])
            if structure:
                msg += "📂 **章节**：\n\n"
                for j, sec in enumerate(structure, 1):
                    sec_title = sec.get('section', '') if isinstance(sec, dict) else str(sec)
                    msg += f"   {j}. {sec_title}\n\n"

            msg += "\n\n💡 继续修改或输入「完成」结束编辑"

            await self._send_message(msg)

        except Exception as e:
            logger.error(f"❌ 处理大纲修改事件失败: {e}", exc_info=True)

    @on_event("creation.writing_progress")
    async def handle_writing_progress(self, context):
        """处理写作进度事件"""
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            section_index = event_data.get('section_index', 0)
            total_sections = event_data.get('total_sections', 0)
            section_title = event_data.get('section_title', '')
            status = event_data.get('status', '')  # started, completed

            session = await self.session_manager.get_session(session_id)
            if not session:
                return

            # 更新进度
            session.current_section_index = section_index
            session.total_sections = total_sections
            await self.session_manager.update_session(session)

            if status == 'started':
                await self._send_message(
                    f"✍️ 正在写作第 {section_index + 1}/{total_sections} 章：**{section_title}**"
                )
            elif status == 'completed':
                await self._send_message(
                    f"✅ 第 {section_index + 1} 章完成"
                )

        except Exception as e:
            logger.error(f"❌ 处理写作进度事件失败: {e}", exc_info=True)

    @on_event("creation.draft_ready")
    async def handle_draft_ready(self, context):
        """处理文章完成事件"""
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            draft = event_data.get('draft', {})
            draft_id = event_data.get('draft_id')

            logger.info(f"🎉 收到文章完成事件: session={session_id}")

            session = await self.session_manager.get_session(session_id)
            if not session:
                logger.error(f"❌ 会话不存在: {session_id}")
                return

            # 更新会话状态为评审中
            session.state = SessionState.REVIEWING
            session.draft_id = draft_id
            await self.session_manager.update_session(session)

            # 初始化评审追踪
            self.pending_reviews[session_id] = {
                'sensitive': None,
                'ai_flavor': None,
                'public_opinion': None,
                'suggestions': [],
                'count': 0,
                'full_reviews': {},
                'draft_title': draft.get('title', '')
            }

            # 发送结果给用户
            msg = f"✅ **初稿完成！**\n\n\n\n"
            msg += f"📌 **{draft.get('title', 'N/A')}**\n\n"
            msg += f"📊 共 {draft.get('word_count', 0)} 字\n\n\n\n"
            msg += f"🔍 正在进行三维度专业评审...\n\n"
            msg += f"• 敏感词审查\n\n"
            msg += f"• AI味审查\n\n"
            msg += f"• 舆情审查"

            await self._send_message(msg)
            logger.info(f"✅ 文章展示完成，等待评审: session={session_id}")

        except Exception as e:
            logger.error(f"❌ 处理文章完成事件失败: {e}", exc_info=True)

    @on_event("creation.review_completed")
    async def handle_review_completed(self, context):
        """收集评审结果并汇总"""
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            review_type = event_data.get('review_type')
            score = event_data.get('overall_score', 0)
            suggestions = event_data.get('suggestions', [])
            verdict = event_data.get('verdict', '')
            full_review = event_data.get('full_review', {})
            draft_title = event_data.get('draft_title', '')

            if not session_id or not review_type:
                return

            logger.info(f"📊 收到评审结果: session={session_id}, type={review_type}, score={score}")

            # 初始化评审追踪
            if session_id not in self.pending_reviews:
                self.pending_reviews[session_id] = {
                    'sensitive': None,
                    'ai_flavor': None,
                    'public_opinion': None,
                    'suggestions': [],
                    'count': 0,
                    'full_reviews': {},  # 保存完整评审数据
                    'draft_title': draft_title
                }

            # 记录评审结果
            self.pending_reviews[session_id][review_type] = {
                'score': score,
                'verdict': verdict
            }
            self.pending_reviews[session_id]['suggestions'].extend(suggestions)
            self.pending_reviews[session_id]['count'] += 1
            # 保存完整评审数据用于按需展示
            self.pending_reviews[session_id]['full_reviews'][review_type] = full_review

            # 检查是否所有评审都完成
            reviews = self.pending_reviews[session_id]
            if reviews['count'] >= 3:
                await self._send_review_summary(session_id, reviews)

        except Exception as e:
            logger.error(f"❌ 处理评审完成事件失败: {e}", exc_info=True)

    async def _send_review_summary(self, session_id: str, reviews: dict):
        """发送审查汇总并询问是否优化"""
        try:
            session = await self.session_manager.get_session(session_id)
            if not session:
                return

            sensitive = reviews.get('sensitive', {}).get('score', 0) or 0
            ai_flavor = reviews.get('ai_flavor', {}).get('score', 0) or 0
            public_opinion = reviews.get('public_opinion', {}).get('score', 0) or 0

            scores = [s for s in [sensitive, ai_flavor, public_opinion] if s > 0]
            avg_score = sum(scores) / len(scores) if scores else 0

            # 保存审查结果到会话
            session.review_scores = {
                'sensitive': sensitive,
                'ai_flavor': ai_flavor,
                'public_opinion': public_opinion,
                'average': avg_score
            }
            session.review_suggestions = reviews.get('suggestions', [])[:5]  # 保留前5条建议
            # 保存完整审查数据到会话，用于按需展示
            session.full_reviews = reviews.get('full_reviews', {})
            session.state = SessionState.WAITING_OPTIMIZATION
            await self.session_manager.update_session(session)

            # 构建汇总消息
            msg = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            msg += "🔍 **三维度审查汇总**\n\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n\n"
            msg += f"🚫 敏感词审查: **{sensitive}/10**\n\n"
            msg += f"🤖 AI味审查: **{ai_flavor}/10**\n\n"
            msg += f"🔥 舆情审查: **{public_opinion}/10**\n\n\n\n"
            msg += f"📊 **综合评分: {avg_score:.1f}/10**\n\n\n\n"

            # 显示主要建议
            suggestions = session.review_suggestions
            if suggestions:
                msg += "💡 **主要改进建议**：\n\n"
                for i, s in enumerate(suggestions[:3], 1):
                    msg += f"   {i}. {s[:60]}{'...' if len(s) > 60 else ''}\n\n"
                msg += "\n\n"

            # 根据评分给出建议
            if avg_score >= 8.0:
                msg += "✨ 优秀！文章质量很高。\n\n\n\n"
            elif avg_score >= 6.0:
                msg += "👍 良好！可根据建议适当优化。\n\n\n\n"
            else:
                msg += "💡 建议根据评审意见进行优化。\n\n\n\n"

            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            msg += "📋 **请选择**：\n\n"
            msg += "• 回复「**详细**」- 查看各评审员的详细报告\n\n"
            msg += "• 回复「**优化**」- 根据建议自动优化\n\n"
            msg += "• 回复「**完成**」- 保存当前版本"

            await self._send_message(msg)
            logger.info(f"✅ 评审汇总已发送: session={session_id}, avg={avg_score:.1f}")

        except Exception as e:
            logger.error(f"❌ 发送评审汇总失败: {e}", exc_info=True)

    @on_event("creation.optimization_done")
    async def handle_optimization_done(self, context):
        """处理优化完成事件"""
        try:
            event_data = context.incoming_event.payload
            session_id = event_data.get('session_id')
            new_draft = event_data.get('draft', {})
            improvements = event_data.get('improvements', [])

            session = await self.session_manager.get_session(session_id)
            if not session:
                return

            # 更新状态
            session.state = SessionState.COMPLETED
            await self.session_manager.update_session(session)

            msg = f"🎉 **优化完成！**\n\n\n\n"
            msg += f"📌 **{new_draft.get('title', 'N/A')}**\n\n"
            msg += f"📊 共 {new_draft.get('word_count', 0)} 字\n\n\n\n"

            if improvements:
                msg += "✨ **改进内容**：\n\n"
                for imp in improvements[:3]:
                    msg += f"   • {imp}\n\n"
                msg += "\n\n"

            msg += f"📚 已保存到知识库\n\n"
            msg += f"💡 输入新主题开始下一篇创作"

            await self._send_message(msg)

        except Exception as e:
            logger.error(f"❌ 处理优化完成事件失败: {e}", exc_info=True)


async def main():
    """运行 Creation Coordinator Agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Creation Coordinator Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    args = parser.parse_args()

    # 配置日志
    log_file = Path(__file__).parent.parent / 'logs' / 'agents' / 'creation_coordinator.log'
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

    agent = CreationCoordinator()

    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )

        logger.info("Creation Coordinator v3 Agent running. Press Ctrl+C to stop.")

        # 保持运行
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("\n\n\n\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())