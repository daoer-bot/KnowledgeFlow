"""
意图识别模块 - 使用 LLM 判断用户意图
替代硬编码的正则规则，更灵活地理解用户输入
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """用户意图枚举"""
    # 创作相关
    NEW_TOPIC = "new_topic"              # 新的创作主题

    # 确认相关
    CONFIRM_YES = "confirm_yes"          # 确认/同意
    CONFIRM_NO = "confirm_no"            # 拒绝/取消

    # 大纲选择相关
    SELECT_OUTLINE = "select_outline"    # 选择大纲（带数字）
    MODIFY_OUTLINE = "modify_outline"    # 修改大纲

    # 编辑相关
    EDIT_INSTRUCTION = "edit_instruction"  # 编辑指令（如"改成两个章节"）
    FINISH_EDITING = "finish_editing"      # 完成编辑

    # 写作控制
    CONTINUE_WRITING = "continue_writing"  # 继续写作
    REWRITE_SECTION = "rewrite_section"    # 重写章节
    STOP_WRITING = "stop_writing"          # 停止写作

    # 优化相关
    REQUEST_OPTIMIZE = "request_optimize"  # 请求优化
    FINISH_CREATION = "finish_creation"    # 完成创作
    VIEW_DETAIL_REPORT = "view_detail_report"  # 查看详细评审报告

    # 其他
    CANCEL = "cancel"                      # 取消当前操作
    UNKNOWN = "unknown"                    # 无法识别


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: UserIntent
    confidence: float  # 0-1
    extracted_data: Dict[str, Any]  # 提取的数据，如主题、数字等
    reasoning: str  # LLM 的推理过程


class IntentDetector:
    """基于 LLM 的意图识别器"""

    def __init__(self, llm_client):
        """
        初始化意图识别器

        Args:
            llm_client: LLM 客户端实例
        """
        self.llm = llm_client

    async def detect_intent(
        self,
        user_input: str,
        current_state: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentResult:
        """
        识别用户意图

        Args:
            user_input: 用户输入的文本
            current_state: 当前会话状态
            context: 额外上下文（如当前主题、大纲数量等）

        Returns:
            IntentResult 对象
        """
        context = context or {}

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(user_input, current_state, context)

        try:
            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,  # 低温度，更确定性
                max_tokens=500
            )

            if not result:
                logger.warning("LLM 返回空结果，使用默认意图")
                return IntentResult(
                    intent=UserIntent.UNKNOWN,
                    confidence=0.0,
                    extracted_data={},
                    reasoning="LLM 返回空结果"
                )

            # 解析结果
            intent_str = result.get("intent", "unknown")
            try:
                intent = UserIntent(intent_str)
            except ValueError:
                intent = UserIntent.UNKNOWN

            return IntentResult(
                intent=intent,
                confidence=result.get("confidence", 0.5),
                extracted_data=result.get("extracted_data", {}),
                reasoning=result.get("reasoning", "")
            )

        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            return IntentResult(
                intent=UserIntent.UNKNOWN,
                confidence=0.0,
                extracted_data={},
                reasoning=f"识别出错: {str(e)}"
            )

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个意图识别助手，负责分析用户在"创作工坊"中的输入意图。

创作工坊是一个帮助用户创作文章的系统，有以下状态流程：
1. idle - 空闲，等待用户输入创作主题
2. confirming_materials - 确认是否使用搜索到的素材
3. generating_outlines - 正在生成大纲
4. waiting_selection - 等待用户选择大纲方案
5. editing_outline - 用户正在修改大纲
6. confirming_start - 确认是否开始写作
7. writing - 正在写作
8. paused_writing - 写作暂停
9. reviewing - 评审中
10. waiting_optimization - 等待用户决定是否优化
11. optimizing - 正在优化
12. completed - 完成

根据用户输入和当前状态，判断用户的意图。

可能的意图：
- new_topic: 用户想创作新文章，输入了一个主题（如"写一篇关于AI的文章"、"RAG技术详解"）
- confirm_yes: 用户确认/同意（如"是"、"好"、"确认"、"开始"、"继续"）
- confirm_no: 用户拒绝/取消（如"否"、"不"、"取消"、"重新"）
- select_outline: 用户选择大纲方案（如"1"、"选择2"、"第三个"）
- modify_outline: 用户想修改大纲（如"修改"、"编辑"、"调整"）
- edit_instruction: 用户给出编辑指令（如"改成两个章节"、"增加一个关于性能的部分"）
- finish_editing: 用户完成编辑（如"完成"、"结束"、"确定"、"done"）
- continue_writing: 继续写作
- rewrite_section: 重写当前章节
- stop_writing: 停止写作
- request_optimize: 请求优化文章（如"优化"、"改进"）
- finish_creation: 完成创作，保存文章（如"完成"、"保存"、"结束"）
- view_detail_report: 查看详细评审报告（如"详细"、"详情"、"查看详细"、"看详细报告"）
- cancel: 取消当前操作
- unknown: 无法识别

重要规则：
1. 在 editing_outline 状态下，用户的输入通常是编辑指令（edit_instruction）或完成编辑（finish_editing）
2. 只有在 idle 或 completed 状态下，才应该识别为 new_topic
3. 如果用户输入包含"完成"、"结束"等词，在 editing_outline 状态下应该是 finish_editing
4. 数字输入在 waiting_selection 状态下是 select_outline

返回 JSON 格式：
{
    "intent": "意图名称",
    "confidence": 0.0-1.0,
    "extracted_data": {
        "topic": "如果是new_topic，提取的主题",
        "number": "如果是select_outline，提取的数字",
        "instruction": "如果是edit_instruction，提取的编辑指令"
    },
    "reasoning": "简短的推理说明"
}"""

    def _build_user_prompt(
        self,
        user_input: str,
        current_state: str,
        context: Dict[str, Any]
    ) -> str:
        """构建用户提示词"""
        prompt = f"""当前状态: {current_state}
用户输入: "{user_input}"
"""

        if context.get("topic"):
            prompt += f"当前主题: {context['topic']}\n"

        if context.get("outline_count"):
            prompt += f"可选大纲数量: {context['outline_count']}\n"

        prompt += "\n请分析用户意图。"

        return prompt


# 便捷函数
async def detect_user_intent(
    llm_client,
    user_input: str,
    current_state: str,
    context: Optional[Dict[str, Any]] = None
) -> IntentResult:
    """
    便捷函数：识别用户意图

    Args:
        llm_client: LLM 客户端
        user_input: 用户输入
        current_state: 当前状态
        context: 上下文

    Returns:
        IntentResult
    """
    detector = IntentDetector(llm_client)
    return await detector.detect_intent(user_input, current_state, context)
