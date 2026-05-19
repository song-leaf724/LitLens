import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from sqlalchemy.orm import Session

from app.agent.roles import CRITIC_AGENT, READER_AGENT, VERIFIER_AGENT
from app.agent.types import AgentTask
from app.db.models import AgentRun, AgentStep
from app.prompts.templates import build_literature_messages
from app.rag.retriever import format_citations_for_prompt
from app.services.llm_service import llm_service
from app.tools.rag_tools import build_default_registry

logger = logging.getLogger(__name__)


class LiteraryAgentState(TypedDict, total=False):
    db: Session
    run_id: str
    task: str
    task_type: str
    document_id: Optional[str]
    session_id: Optional[str]
    top_k: Optional[int]
    mode: str
    plan: str
    citations: List[Dict[str, Any]]
    citation_context: str
    reader_output: str
    critic_output: str
    verifier_output: str
    final_answer: str
    errors: List[str]


class EvidenceBasedLiteraryWorkflow:
    """LangGraph workflows for fast and deep evidence-based literary analysis."""

    def __init__(self) -> None:
        self.registry = build_default_registry()
        self._deep_graph = None
        self._fast_graph = None

    async def run(self, db: Session, task: AgentTask) -> AgentRun:
        run = AgentRun(
            session_id=task.session_id,
            task_type=task.task_type,
            status="running",
            input_text=task.task,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        state: LiteraryAgentState = {
            "db": db,
            "run_id": run.id,
            "task": task.task,
            "task_type": task.task_type,
            "document_id": task.document_id,
            "session_id": task.session_id,
            "top_k": task.top_k,
            "mode": task.mode,
            "errors": [],
        }

        try:
            result = await self._compiled_graph(task.mode).ainvoke(state)
            run.status = "completed"
            run.output_text = result.get("final_answer", "")
            run.ended_at = datetime.utcnow()
            db.commit()
            db.refresh(run)
            return run
        except Exception as exc:
            logger.exception("Evidence-based literary workflow failed")
            error_message = self._format_error(exc)
            self._add_step(db, run.id, role="LiteratureAgent", step_type="error", error_message=error_message)
            run.status = "failed"
            run.output_text = error_message
            run.ended_at = datetime.utcnow()
            db.commit()
            db.refresh(run)
            return run

    def _compiled_graph(self, mode: str):
        normalized_mode = mode if mode in {"fast", "deep"} else "deep"
        if normalized_mode == "fast":
            return self._compiled_fast_graph()
        return self._compiled_deep_graph()

    def _compiled_deep_graph(self):
        if self._deep_graph is not None:
            return self._deep_graph
        try:
            from langgraph.graph import END, StateGraph
        except ImportError as exc:  # pragma: no cover - environment setup guard
            raise RuntimeError("LangGraph is not installed. Run `pip install -r requirements.txt`.") from exc

        graph = StateGraph(LiteraryAgentState)
        graph.add_node("planner", self.planner_node)
        graph.add_node("retriever", self.retriever_node)
        graph.add_node("reader", self.reader_node)
        graph.add_node("critic", self.critic_node)
        graph.add_node("verifier", self.verifier_node)
        graph.add_node("final", self.final_node)

        graph.set_entry_point("planner")
        graph.add_edge("planner", "retriever")
        graph.add_edge("retriever", "reader")
        graph.add_edge("reader", "critic")
        graph.add_edge("critic", "verifier")
        graph.add_edge("verifier", "final")
        graph.add_edge("final", END)
        self._deep_graph = graph.compile()
        return self._deep_graph

    def _compiled_fast_graph(self):
        if self._fast_graph is not None:
            return self._fast_graph
        try:
            from langgraph.graph import END, StateGraph
        except ImportError as exc:  # pragma: no cover - environment setup guard
            raise RuntimeError("LangGraph is not installed. Run `pip install -r requirements.txt`.") from exc

        graph = StateGraph(LiteraryAgentState)
        graph.add_node("retriever", self.retriever_node)
        graph.add_node("fast_final", self.fast_final_node)

        graph.set_entry_point("retriever")
        graph.add_edge("retriever", "fast_final")
        graph.add_edge("fast_final", END)
        self._fast_graph = graph.compile()
        return self._fast_graph

    async def planner_node(self, state: LiteraryAgentState) -> Dict[str, Any]:
        db = state["db"]
        context = json.dumps(
            {
                "task_type": state.get("task_type"),
                "document_id": state.get("document_id"),
                "top_k": state.get("top_k"),
            },
            ensure_ascii=False,
        )
        messages = build_literature_messages(
            task_type="agent_planner",
            user_input=state["task"],
            context=context,
        )
        plan = await self._llm_or_fallback(
            messages=messages,
            fallback="计划阶段模型调用失败，降级为：先检索原文证据，再进行 Reader/Critic/Verifier 分析。",
            max_tokens=600,
        )
        self._add_step(db, state["run_id"], role="PlannerAgent", step_type="plan", output_text=plan)
        return {"plan": plan}

    async def retriever_node(self, state: LiteraryAgentState) -> Dict[str, Any]:
        db = state["db"]
        tool_args = {
            "query": state["task"],
            "document_id": state.get("document_id"),
            "top_k": state.get("top_k"),
        }
        observation = await self.registry.call("rag_search", tool_args, context={"db": db})
        citations = observation.get("citations", [])
        citation_context = self._citation_context(citations)
        self._add_step(
            db,
            state["run_id"],
            role="Retriever",
            step_type="retrieve",
            tool_name="rag_search",
            input_text=json.dumps(tool_args, ensure_ascii=False),
            output_text=json.dumps(observation, ensure_ascii=False, indent=2),
        )
        return {"citations": citations, "citation_context": citation_context}

    async def fast_final_node(self, state: LiteraryAgentState) -> Dict[str, Any]:
        if not state.get("citations"):
            answer = (
                "当前证据不足：系统没有检索到可用的原文片段，因此不能基于原文完成可靠回答。"
                "请先上传或导入作品文本，或换一个更贴近原文的问题。"
            )
        else:
            messages = build_literature_messages(
                task_type="agent_fast_final",
                user_input=state["task"],
                context=state.get("citation_context", "未检索到可用原文片段。"),
            )
            answer = await self._llm_or_fallback(
                messages=messages,
                fallback=self._fallback_fast_answer(state),
                max_tokens=700,
            )
        self._add_step(state["db"], state["run_id"], role="FastLiteraryAgent", step_type="fast_answer", output_text=answer)
        return {"final_answer": answer}

    async def reader_node(self, state: LiteraryAgentState) -> Dict[str, Any]:
        if not state.get("citations"):
            output = "当前没有检索到可用原文证据，Reader Agent 不能进行可靠的文本细读。"
        else:
            messages = build_literature_messages(
                task_type="agent_reader",
                user_input=state["task"],
                context=state.get("citation_context", "未检索到可用原文片段。"),
            )
            output = await self._llm_or_fallback(
                messages=messages,
                fallback="Reader Agent 模型调用失败，已保留检索到的原文证据，无法生成完整细读。",
                max_tokens=900,
            )
        self._add_step(state["db"], state["run_id"], role=READER_AGENT.name, step_type="reader_analysis", output_text=output)
        return {"reader_output": output}

    async def critic_node(self, state: LiteraryAgentState) -> Dict[str, Any]:
        context = self._dump_context(
            {
                "plan": state.get("plan"),
                "reader_output": state.get("reader_output"),
                "citations": state.get("citation_context"),
            }
        )
        if not state.get("citations"):
            output = "当前缺少原文证据，Critic Agent 只能记录分析方向，不能给出确定的主题或象征判断。"
        else:
            messages = build_literature_messages(
                task_type="agent_critic",
                user_input=state["task"],
                context=context,
            )
            output = await self._llm_or_fallback(
                messages=messages,
                fallback="Critic Agent 模型调用失败，无法补充主题、象征和叙事结构分析。",
                max_tokens=900,
            )
        self._add_step(state["db"], state["run_id"], role=CRITIC_AGENT.name, step_type="critic_analysis", output_text=output)
        return {"critic_output": output}

    async def verifier_node(self, state: LiteraryAgentState) -> Dict[str, Any]:
        context = self._dump_context(
            {
                "reader_output": state.get("reader_output"),
                "critic_output": state.get("critic_output"),
                "citations": state.get("citation_context"),
            }
        )
        if not state.get("citations"):
            output = "证据不足：没有检索到可引用原文，最终回答必须明确说明无法基于原文下结论。"
        else:
            messages = build_literature_messages(
                task_type="agent_verifier",
                user_input=state["task"],
                context=context,
            )
            output = await self._llm_or_fallback(
                messages=messages,
                fallback=(
                    "Verifier Agent 模型调用失败，降级检查结果：最终回答只能使用已检索到的引用片段，"
                    "并应避免声称原文没有支持的结论。"
                ),
                max_tokens=600,
            )
        self._add_step(state["db"], state["run_id"], role=VERIFIER_AGENT.name, step_type="verification", output_text=output)
        return {"verifier_output": output}

    async def final_node(self, state: LiteraryAgentState) -> Dict[str, Any]:
        if not state.get("citations"):
            answer = (
                "当前证据不足：系统没有检索到可用的原文片段，因此不能基于原文完成可靠的文学分析。"
                "请先上传或导入作品文本，或调整 document_id / 问题范围后再试。"
            )
        else:
            context = self._dump_context(
                {
                    "plan": state.get("plan"),
                    "reader_output": state.get("reader_output"),
                    "critic_output": state.get("critic_output"),
                    "verifier_output": state.get("verifier_output"),
                    "citations": state.get("citation_context"),
                }
            )
            messages = build_literature_messages(
                task_type="agent_evidence_final",
                user_input=state["task"],
                context=context,
            )
            answer = await self._llm_or_fallback(
                messages=messages,
                fallback=self._fallback_final_answer(state),
                max_tokens=900,
            )
        self._add_step(state["db"], state["run_id"], role="FinalWriterAgent", step_type="final", output_text=answer)
        return {"final_answer": answer}

    async def _llm_or_fallback(
        self,
        messages: List[Dict[str, str]],
        fallback: str,
        max_tokens: int,
    ) -> str:
        try:
            return await llm_service.chat_completion(messages, max_tokens=max_tokens)
        except Exception as exc:  # pragma: no cover - depends on external API behavior
            logger.warning("Agent LLM step failed, using fallback: %s", self._format_error(exc))
            return f"{fallback}\n\n[模型调用错误：{self._format_error(exc)}]"

    def _fallback_fast_answer(self, state: LiteraryAgentState) -> str:
        citations = state.get("citation_context") or "未检索到可用原文片段。"
        return (
            "## 简要回答\n"
            "快速回答模型调用失败，以下是基于已检索原文的降级结果。请结合右侧原文依据继续核对。\n\n"
            "## 原文依据\n"
            f"{citations}\n\n"
            "## 需要谨慎的地方\n"
            "当前回答只使用已检索到的片段，涉及作者生平、创作年代或外部史料的问题需要额外资料支持。"
        )

    def _fallback_final_answer(self, state: LiteraryAgentState) -> str:
        citations = state.get("citation_context") or "未检索到可用原文片段。"
        reader = state.get("reader_output") or "Reader Agent 未生成结果。"
        critic = state.get("critic_output") or "Critic Agent 未生成结果。"
        verifier = state.get("verifier_output") or "Verifier Agent 未生成结果。"
        return (
            "## 核心结论\n"
            "最终汇总模型调用失败，以下为基于已有步骤的降级回答。\n\n"
            "## 原文依据\n"
            f"{citations}\n\n"
            "## 细读分析\n"
            f"### Reader 分析\n{reader}\n\n"
            f"### Critic 分析\n{critic}\n\n"
            "## 证据边界\n"
            f"{verifier}\n\n"
            "## 可继续深读\n"
            "- 重新运行最终汇总节点，获得更完整的结构化回答。\n"
            "- 对照引用片段检查每个判断是否有原文依据。"
        )

    def _format_error(self, exc: Exception) -> str:
        message = str(exc).strip()
        if message:
            return message
        return exc.__class__.__name__

    def _citation_context(self, citations: List[Dict[str, Any]]) -> str:
        if not citations:
            return "未检索到可用原文片段。"
        from app.schemas.rag import Citation

        citation_models = [Citation(**citation) for citation in citations]
        return format_citations_for_prompt(citation_models)

    def _dump_context(self, payload: Dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _add_step(
        self,
        db: Session,
        run_id: str,
        role: str,
        step_type: str,
        tool_name: Optional[str] = None,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> AgentStep:
        step = AgentStep(
            run_id=run_id,
            role=role,
            step_type=step_type,
            tool_name=tool_name,
            input_text=input_text,
            output_text=output_text,
            error_message=error_message,
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step


literary_workflow = EvidenceBasedLiteraryWorkflow()
