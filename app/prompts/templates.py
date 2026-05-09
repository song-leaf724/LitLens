from typing import Dict, List, Optional


LITERATURE_SYSTEM_PROMPT = """你是「文学作品深度阅读助手」。
你的任务是基于用户上传的原文进行文学分析，而不是泛泛聊天。
回答时请遵守：
1. 优先依据给定原文片段，不要编造不存在的情节、人物或引用。
2. 如果证据不足，要明确说明“当前片段不足以判断”。
3. 尽量给出引用编号，例如“根据[引用 1]...”。
4. 分析要有文学阅读深度：关注叙事、人物、主题、意象、修辞、情绪和结构。
5. 输出使用中文，除非用户明确要求其他语言。
"""


TASK_TEMPLATES: Dict[str, str] = {
    "qa": """请结合原文回答用户问题。

用户问题：
{user_input}

可用原文片段：
{context}

请输出：
- 直接回答
- 原文依据
- 如果有不确定处，请说明原因
""",
    "plot": """请基于原文进行情节梳理。

分析目标：
{user_input}

可用原文片段：
{context}

请输出：
- 主要情节概览
- 关键事件
- 叙事线索
- 情节推进中的转折或冲突
- 引用依据
""",
    "characters": """请基于原文进行人物分析。

分析目标：
{user_input}

可用原文片段：
{context}

请输出：
- 主要人物及其性格特征
- 人物动机和心理变化
- 人物关系
- 人物的象征意义或叙事功能
- 引用依据
""",
    "themes": """请基于原文分析主题与意象。

分析目标：
{user_input}

可用原文片段：
{context}

请输出：
- 核心主题
- 反复出现的意象
- 隐喻、象征或情绪氛围
- 主题如何通过人物、情节或语言呈现
- 引用依据
""",
    "close_reading": """请对下面的段落进行文学细读。

段落：
{passage}

补充问题：
{user_input}

请输出：
- 字面含义
- 语言风格与修辞
- 叙事视角
- 情绪变化
- 潜在含义或主题关联
""",
    "bilingual": """请对下面的英文或双语片段进行双语赏析。

文本：
{passage}

补充问题：
{user_input}

请输出：
- 中文解释
- 关键词解析
- 文学化翻译
- 语感与风格分析
- 如果涉及文化或典故，请说明
""",
    "notes": """请根据原文生成结构化阅读笔记。

笔记重点：
{user_input}

可用原文片段：
{context}

请输出：
- 作品概览
- 情节提要
- 主要人物与关系
- 主题与意象
- 精彩摘录或可引用片段
- 值得继续思考的问题
""",
    "agent_final": """你是文学阅读多智能体系统中的汇总智能体。

用户任务：
{user_input}

工具观察结果：
{context}

请给出最终分析，要求：
- 明确回答任务
- 使用原文证据
- 如果证据不足，请指出
- 给出后续可深入阅读的问题
""",
}


def build_literature_messages(
    task_type: str,
    user_input: str,
    context: str = "",
    history: Optional[List[Dict[str, str]]] = None,
    passage: Optional[str] = None,
) -> List[Dict[str, str]]:
    template = TASK_TEMPLATES.get(task_type, TASK_TEMPLATES["qa"])
    user_content = template.format(
        user_input=user_input or "请基于原文进行分析。",
        context=context or "未提供原文片段。",
        passage=passage or "",
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": LITERATURE_SYSTEM_PROMPT},
    ]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_content})
    return messages

