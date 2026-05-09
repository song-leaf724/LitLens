import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.agent.roles import LITERATURE_AGENT
from app.agent.types import AgentTask
from app.db.models import AgentRun, AgentStep
from app.prompts.templates import build_literature_messages
from app.services.llm_service import llm_service
from app.tools.rag_tools import build_default_registry

logger = logging.getLogger(__name__)


class SimpleWorkflowEngine:
    """轻量 Planner -> Tool -> Observation -> Final 流程，后续可替换为 LangGraph。"""

    def __init__(self) -> None:
        self.registry = build_default_registry()

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

        try:
            plan = (
                "先调用 rag_search 检索与任务相关的原文片段，再基于证据生成文学分析。"
            )
            self._add_step(db, run.id, "plan", output_text=plan)

            tool_args = {
                "query": task.task,
                "document_id": task.document_id,
                "top_k": task.top_k,
            }
            self._add_step(
                db,
                run.id,
                "action",
                tool_name="rag_search",
                input_text=json.dumps(tool_args, ensure_ascii=False),
            )

            observation = await self.registry.call(
                "rag_search", tool_args, context={"db": db}
            )
            observation_text = json.dumps(observation, ensure_ascii=False, indent=2)
            self._add_step(
                db,
                run.id,
                "observation",
                tool_name="rag_search",
                output_text=observation_text,
            )

            messages = build_literature_messages(
                task_type="agent_final",
                user_input=task.task,
                context=observation_text,
            )
            answer = await llm_service.chat_completion(messages)
            self._add_step(db, run.id, "final", output_text=answer)

            run.status = "completed"
            run.output_text = answer
            run.ended_at = datetime.utcnow()
            db.commit()
            db.refresh(run)
            return run
        except Exception as exc:
            logger.exception("Agent workflow failed")
            self._add_step(db, run.id, "error", error_message=str(exc))
            run.status = "failed"
            run.output_text = str(exc)
            run.ended_at = datetime.utcnow()
            db.commit()
            db.refresh(run)
            return run

    def _add_step(
        self,
        db: Session,
        run_id: str,
        step_type: str,
        tool_name: str = None,
        input_text: str = None,
        output_text: str = None,
        error_message: str = None,
    ) -> AgentStep:
        step = AgentStep(
            run_id=run_id,
            role=LITERATURE_AGENT.name,
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


workflow_engine = SimpleWorkflowEngine()

