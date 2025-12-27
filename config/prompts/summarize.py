"""
摘要生成提示词模板
用于 Summarizer Agent 生成不同长度的内容摘要
"""

SYSTEM_PROMPT = """你是一个专业的内容摘要助手。你的任务是为文章生成不同长度的摘要。

要求：
1. 准确把握文章核心内容和主旨
2. 提取关键信息和要点
3. 保持客观中立的语气
4. 避免主观评价和猜测
5. 使用简洁清晰的语言
6. 保持原文的技术术语和专有名词

输出格式：
必须返回有效的 JSON 格式，包含以下字段。
"""

USER_PROMPT_TEMPLATE = """请为以下文章生成摘要：

标题：{title}
来源：{source}
URL：{url}

内容：
{content}

请输出 JSON 格式，包含以下字段：
{{
    "one_line": "20-30字的一句话摘要，概括核心内容",
    "paragraph": "100-150字的段落摘要，包含主要观点",
    "detailed": "300-500字的详细摘要，包含完整论述",
    "key_points": ["关键要点1", "关键要点2", "关键要点3"],
    "key_quotes": ["重要引用1（如果有）", "重要引用2（如果有）"]
}}

注意：
- 摘要要忠实于原文，不要添加原文没有的内容
- 关键要点应该是独立的观点或发现
- 引用应该是原文中的精彩或重要语句
"""


def format_prompt(title: str, source: str, url: str, content: str) -> tuple[str, str]:
    """
    格式化提示词
    
    Args:
        title: 文章标题
        source: 来源名称
        url: 文章链接
        content: 文章内容（建议截取前8000字符以控制token）
    
    Returns:
        (system_prompt, user_prompt) 元组
    """
    # 截取内容以避免超出 token 限制
    max_content_length = 8000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "\n\n[内容已截断...]"
    
    user_prompt = USER_PROMPT_TEMPLATE.format(
        title=title,
        source=source,
        url=url,
        content=content
    )
    
    return SYSTEM_PROMPT, user_prompt