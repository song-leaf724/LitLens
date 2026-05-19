from typing import Literal, List, Optional

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    task: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    document_id: Optional[str] = None
    task_type: str = "literature"
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    mode: Literal["fast", "deep"] = "deep"


class AgentStepResponse(BaseModel):
    role: str
    step_type: str
    tool_name: Optional[str] = None
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    error_message: Optional[str] = None


class AgentRunResponse(BaseModel):
    run_id: str
    status: str
    answer: str
    mode: str = "deep"
    steps: List[AgentStepResponse] = []

