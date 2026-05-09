from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.orchestrator import agent_orchestrator
from app.agent.types import AgentTask
from app.db.session import get_db
from app.schemas.agent import AgentRunRequest, AgentRunResponse, AgentStepResponse

router = APIRouter()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest, db: Session = Depends(get_db)
) -> AgentRunResponse:
    run = await agent_orchestrator.run(
        db=db,
        task=AgentTask(
            task=request.task,
            task_type=request.task_type,
            document_id=request.document_id,
            session_id=request.session_id,
            top_k=request.top_k,
        ),
    )
    return AgentRunResponse(
        run_id=run.id,
        status=run.status,
        answer=run.output_text or "",
        steps=[
            AgentStepResponse(
                role=step.role,
                step_type=step.step_type,
                tool_name=step.tool_name,
                input_text=step.input_text,
                output_text=step.output_text,
                error_message=step.error_message,
            )
            for step in run.steps
        ],
    )

