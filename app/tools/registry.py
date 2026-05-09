import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


ToolFunc = Callable[[Dict[str, Any], Dict[str, Any]], Any]


@dataclass
class Tool:
    name: str
    description: str
    func: ToolFunc


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    async def call(
        self, name: str, arguments: Dict[str, Any], context: Dict[str, Any]
    ) -> Any:
        tool = self.get(name)
        result = tool.func(arguments, context)
        if inspect.isawaitable(result):
            return await result
        return result

