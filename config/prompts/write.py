"""
文章写作提示词模板
用于 Writer Agent 根据大纲生成完整文章
"""

SYSTEM_PROMPT = """你是一位资深的技术内容创作者，拥有丰富的科技媒体写作经验。你的文章曾发表于知名技术博客和科技媒体。

## 写作风格特点

### 1. 语言表达
- **清晰精准**：用最简洁的语言表达复杂概念，避免冗余
- **专业但不晦涩**：技术术语使用恰当，必要时提供解释
- **节奏感强**：长短句交替，段落有呼吸感
- **有温度**：在专业中融入人文关怀，让技术有温度

### 2. 内容组织
- **开门见山**：每段首句点明核心观点
- **论据充分**：观点必有数据、案例或权威引用支撑
- **逻辑严密**：因果关系清晰，推理过程完整
- **过渡自然**：段落间有承上启下的衔接

### 3. 技术写作规范
- **准确性第一**：技术细节必须准确，不确定的内容要标注
- **版本敏感**：涉及技术版本时要明确标注
- **代码规范**：代码示例要可运行、有注释
- **引用规范**：数据和观点要标注来源

### 4. 读者体验
- **价值导向**：每一段都要给读者带来价值
- **易于扫读**：使用小标题、列表、加粗等增强可读性
- **互动感**：适当使用设问、反问增强互动
- **行动导向**：给读者明确的下一步建议

## 质量标准

- 信息密度高，无水分内容
- 观点鲜明，论述有力
- 案例生动，数据可信
- 结构清晰，层次分明
- 语言流畅，可读性强
"""

SECTION_PROMPT_TEMPLATE = """## 写作任务

**文章标题**：{article_title}
**当前章节**：{section_title}
**目标字数**：约 {target_words} 字

---

## 章节要点

{section_points}

---

## 可引用素材

{materials}

---

## 上下文（前文摘要）

{previous_context}

---

## 写作要求

### 内容要求
1. **紧扣要点**：确保覆盖上述所有要点，但不要机械罗列
2. **深度适中**：既要有深度，又要保持可读性
3. **素材融合**：自然地引用素材中的观点、数据或案例
4. **逻辑连贯**：与前文保持逻辑上的承接和呼应

### 格式要求
1. 使用 Markdown 格式
2. 可以使用**加粗**强调关键概念
3. 适当使用列表提升可读性
4. 重要引用要标注来源（如：据XX报道...）
5. 如有代码示例，使用代码块并添加语言标识

### 风格要求
1. 开头要有吸引力，可以用问题、数据或场景引入
2. 段落长度适中（3-5句为宜）
3. 避免过于口语化或过于学术化
4. 保持客观中立，但可以有适度的观点表达

### 禁止事项
- 不要包含章节标题（标题会自动添加）
- 不要使用"首先、其次、最后"等过于程式化的过渡词
- 不要出现"本文将介绍"等自我指涉的表述
- 不要编造数据或虚构案例

请直接输出该章节的正文内容。
"""


def format_section_prompt(
    article_title: str,
    section_title: str,
    section_points: list[str],
    materials: list[dict],
    previous_context: str = "",
    target_words: int = 400,
    section_type: str = "body",
    writing_tips: str = "",
    core_argument: str = ""
) -> tuple[str, str]:
    """
    格式化章节写作提示词

    Args:
        article_title: 文章总标题
        section_title: 当前章节标题
        section_points: 章节要点列表
        materials: 相关素材
        previous_context: 前文内容（最后500字）
        target_words: 目标字数
        section_type: 章节类型 (intro/body/conclusion/case_study/deep_dive)
        writing_tips: 写作建议
        core_argument: 核心论点

    Returns:
        (system_prompt, user_prompt) 元组
    """
    # 格式化要点 - 更详细的展示
    points_text = ""
    for i, point in enumerate(section_points, 1):
        points_text += f"{i}. {point}\n"

    if core_argument:
        points_text = f"**核心论点**：{core_argument}\n\n**具体要点**：\n{points_text}"

    if writing_tips:
        points_text += f"\n**写作建议**：{writing_tips}"

    # 格式化素材 - 更丰富的信息
    materials_text = ""
    for mat in materials:
        mat_id = mat.get('id', 'unknown')
        title = mat.get('title', '未知')
        source = mat.get('source', '未知')
        summary = mat.get('summary', '')
        key_points = mat.get('key_points', [])

        materials_text += f"### [{mat_id}] {title}\n"
        materials_text += f"**来源**：{source}\n"

        if summary:
            materials_text += f"**摘要**：{summary[:200]}{'...' if len(summary) > 200 else ''}\n"

        if key_points:
            materials_text += "**可引用要点**：\n"
            for point in key_points[:3]:
                materials_text += f"  - {point}\n"

        materials_text += "\n"

    if not materials_text:
        materials_text = "暂无直接相关素材，请基于专业知识撰写"

    # 截取前文context - 提供更好的上下文
    if len(previous_context) > 800:
        previous_context = "...\n\n" + previous_context[-800:]

    if not previous_context:
        if section_type == "intro":
            previous_context = "这是文章的开篇，需要吸引读者注意力"
        else:
            previous_context = "这是文章的第一部分"

    # 根据章节类型添加特殊指导
    section_guidance = ""
    if section_type == "intro":
        section_guidance = "\n\n**章节类型提示**：这是引言部分，需要：\n- 用引人入胜的开头抓住读者\n- 简明介绍主题背景\n- 预告文章将要讨论的内容"
    elif section_type == "conclusion":
        section_guidance = "\n\n**章节类型提示**：这是结论部分，需要：\n- 总结全文核心观点\n- 给出前瞻性思考或建议\n- 不要引入新的论点"
    elif section_type == "case_study":
        section_guidance = "\n\n**章节类型提示**：这是案例分析部分，需要：\n- 详细描述案例背景\n- 分析关键决策和结果\n- 提炼可借鉴的经验"
    elif section_type == "deep_dive":
        section_guidance = "\n\n**章节类型提示**：这是深度分析部分，需要：\n- 深入剖析技术原理或机制\n- 提供详细的技术细节\n- 可以包含代码示例或架构图说明"

    user_prompt = SECTION_PROMPT_TEMPLATE.format(
        article_title=article_title,
        section_title=section_title,
        section_points=points_text + section_guidance,
        materials=materials_text,
        previous_context=previous_context,
        target_words=target_words
    )

    return SYSTEM_PROMPT, user_prompt


# 引言部分的特殊提示词
INTRODUCTION_TEMPLATE = """## 引言写作任务

**文章标题**：{article_title}
**主题**：{topic}
**目标字数**：200-300 字

---

## 文章大纲概览

{outline_overview}

---

## 写作要求

### 引言的核心目标
1. **抓住注意力**：用一个引人入胜的开头（可以是问题、数据、场景或故事）
2. **建立相关性**：让读者感受到这个主题与他们的关联
3. **设定预期**：简要预告文章将要讨论的内容
4. **激发兴趣**：让读者有继续阅读的欲望

### 开头技巧（选择一种）
- **数据开头**：用一个震撼的数据或统计引入
- **问题开头**：提出一个读者关心的问题
- **场景开头**：描绘一个具体的场景或情境
- **故事开头**：讲述一个简短的相关故事
- **对比开头**：展示一个有趣的对比或反差

### 格式要求
- 使用 Markdown 格式
- 段落简洁有力（2-3段为宜）
- 不要使用"本文将介绍..."等程式化表述
- 不要包含标题

请直接输出引言内容。
"""


def format_introduction_prompt(
    article_title: str,
    topic: str,
    outline_overview: str
) -> tuple[str, str]:
    """格式化引言写作提示词"""
    user_prompt = INTRODUCTION_TEMPLATE.format(
        article_title=article_title,
        topic=topic,
        outline_overview=outline_overview
    )
    return SYSTEM_PROMPT, user_prompt


# 结尾部分的特殊提示词
CONCLUSION_TEMPLATE = """## 结尾写作任务

**文章标题**：{article_title}
**主题**：{topic}
**目标字数**：200-300 字

---

## 文章要点回顾

{key_points}

---

## 全文上下文（最后部分）

{article_context}

---

## 写作要求

### 结尾的核心目标
1. **总结升华**：提炼全文核心观点，但不是简单重复
2. **价值强化**：强调文章给读者带来的价值
3. **展望思考**：给出前瞻性的思考或预测
4. **行动号召**：给读者一个明确的下一步建议

### 结尾技巧（选择一种或组合）
- **回顾式**：简洁总结核心观点，强调关键收获
- **展望式**：对未来趋势进行预测或展望
- **行动式**：给出具体的行动建议或下一步
- **思考式**：留下一个开放性问题引发思考
- **呼应式**：与开头形成呼应，形成闭环

### 格式要求
- 使用 Markdown 格式
- 段落简洁有力（2-3段为宜）
- 可以使用**加粗**强调关键结论
- 不要引入新的论点或概念
- 不要包含标题

### 禁止事项
- 不要使用"总之"、"综上所述"等陈词滥调
- 不要简单罗列前文内容
- 不要过于说教或鸡汤

请直接输出结尾内容。
"""


def format_conclusion_prompt(
    article_title: str,
    topic: str,
    key_points: list[str],
    article_context: str
) -> tuple[str, str]:
    """格式化结尾写作提示词"""
    points_text = "\n".join([f"- {point}" for point in key_points])
    
    if len(article_context) > 1000:
        article_context = "..." + article_context[-1000:]
    
    user_prompt = CONCLUSION_TEMPLATE.format(
        article_title=article_title,
        topic=topic,
        key_points=points_text,
        article_context=article_context
    )
    return SYSTEM_PROMPT, user_prompt