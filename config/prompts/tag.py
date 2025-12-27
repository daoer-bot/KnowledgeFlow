"""
标签生成提示词模板
用于 Tagger Agent 为内容生成标签和分类
"""

SYSTEM_PROMPT = """你是一个专业的内容分类和标签生成助手。

分类体系：
- **技术教程**：教学性质的技术文章
- **行业动态**：新闻、发布、事件等
- **产品评测**：产品测评、对比分析
- **最佳实践**：经验分享、实战案例
- **思考总结**：观点、见解、反思
- **开源项目**：开源软件、工具介绍

标签层级：
- **主题标签**：AI、编程、创业、设计、产品等大类
- **技术标签**：Python、React、机器学习、区块链等具体技术
- **场景标签**：教程、案例、评测、新闻等

情感倾向：
- positive：积极、乐观、推荐
- neutral：中立、客观、陈述
- negative：批评、质疑、警告

相关性评分（0-1）：
- 内容对目标受众的价值和实用性
"""

USER_PROMPT_TEMPLATE = """请为以下内容生成标签和分类：

标题：{title}
来源：{source}
摘要：{summary}

请输出 JSON 格式：
{{
    "category": "从分类体系中选择最合适的一个主分类",
    "tags": {{
        "topics": ["主题标签1", "主题标签2"],
        "technologies": ["技术标签1", "技术标签2"],
        "scenarios": ["场景标签1"]
    }},
    "sentiment": "positive/neutral/negative",
    "relevance_score": 0.85
}}

要求：
- 每个层级最多3个标签
- 标签要准确反映内容特征
- 相关性评分要客观合理
- 技术标签要使用规范名称
"""


def format_prompt(title: str, source: str, summary: str) -> tuple[str, str]:
    """
    格式化提示词
    
    Args:
        title: 文章标题
        source: 来源名称
        summary: 文章摘要（使用 paragraph 级别的摘要）
    
    Returns:
        (system_prompt, user_prompt) 元组
    """
    user_prompt = USER_PROMPT_TEMPLATE.format(
        title=title,
        source=source,
        summary=summary
    )
    
    return SYSTEM_PROMPT, user_prompt