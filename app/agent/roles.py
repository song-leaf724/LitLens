from app.agent.types import AgentRole


READER_AGENT = AgentRole(
    name="ReaderAgent",
    description="负责原文理解、情节梳理、人物基础分析。",
    output_focus="忠实于文本，提取情节、人物、叙事线索和引用证据。",
)

CRITIC_AGENT = AgentRole(
    name="CriticAgent",
    description="负责主题、象征、文学批评角度分析。",
    output_focus="分析主题、意象、隐喻、象征和作品结构。",
)

TRANSLATOR_AGENT = AgentRole(
    name="TranslatorAgent",
    description="负责英文文本翻译、关键词解析和双语赏析。",
    output_focus="提供中文解释、文学化翻译和语感分析。",
)

VERIFIER_AGENT = AgentRole(
    name="VerifierAgent",
    description="负责检查回答是否有原文依据。",
    output_focus="核对结论与引用片段是否匹配，标出证据不足之处。",
)

LITERATURE_AGENT = AgentRole(
    name="LiteratureAgent",
    description="MVP 通用文学分析智能体。",
    output_focus="结合检索结果完成深度阅读分析。",
)

