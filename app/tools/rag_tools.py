from typing import Any, Dict

from app.rag.retriever import retrieve_relevant_chunks
from app.tools.registry import Tool, ToolRegistry


def _dump_model(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


async def rag_search_tool(arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    db = context["db"]
    query = arguments["query"]
    document_id = arguments.get("document_id")
    top_k = arguments.get("top_k")

    citations = await retrieve_relevant_chunks(
        query=query,
        db=db,
        document_id=document_id,
        top_k=top_k,
    )
    return {
        "tool": "rag_search",
        "query": query,
        "citations": [_dump_model(citation) for citation in citations],
    }


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="rag_search",
            description="根据用户问题检索上传文学作品中的相关原文片段。",
            func=rag_search_tool,
        )
    )
    return registry

