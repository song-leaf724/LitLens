from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AgentTask:
    task: str
    task_type: str = "literature"
    document_id: Optional[str] = None
    session_id: Optional[str] = None
    top_k: Optional[int] = None
    mode: str = "deep"


@dataclass
class AgentRole:
    name: str
    description: str
    output_focus: str


@dataclass
class AgentToolCall:
    name: str
    arguments: Dict[str, Any]

