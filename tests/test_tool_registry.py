import asyncio

import pytest

from app.tools.registry import Tool, ToolRegistry


def test_tool_registry_calls_async_tool() -> None:
    async def echo_tool(arguments, context):
        return {"value": arguments["value"], "prefix": context["prefix"]}

    registry = ToolRegistry()
    registry.register(Tool(name="echo", description="echo test", func=echo_tool))

    result = asyncio.run(
        registry.call("echo", {"value": "text"}, {"prefix": "ok"})
    )
    assert result == {"value": "text", "prefix": "ok"}


def test_tool_registry_rejects_duplicate_names() -> None:
    registry = ToolRegistry()
    registry.register(Tool(name="echo", description="echo test", func=lambda a, c: a))

    with pytest.raises(ValueError):
        registry.register(
            Tool(name="echo", description="duplicate", func=lambda a, c: a)
        )

