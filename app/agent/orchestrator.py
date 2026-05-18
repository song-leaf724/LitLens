from sqlalchemy.orm import Session

from app.agent.types import AgentTask
from app.agent.workflow import workflow_engine
from app.db.models import AgentRun


class AgentOrchestrator:
    async def run(self, db: Session, task: AgentTask) -> AgentRun:
        return await workflow_engine.run(db=db, task=task)


agent_orchestrator = AgentOrchestrator()
