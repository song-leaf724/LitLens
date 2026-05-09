import json
import logging
from typing import AsyncGenerator, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not settings.llm_api_key or settings.llm_use_fake:
            return self._fake_response(messages)

        url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
        payload: Dict[str, object] = {
            "model": settings.llm_model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(settings.llm_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        if not settings.llm_api_key or settings.llm_use_fake:
            fake = self._fake_response(messages)
            for token in fake.split():
                yield token + " "
            return

        url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.llm_model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(settings.llm_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    try:
                        payload = json.loads(data)
                        delta = payload["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        logger.debug("Skip malformed stream line: %s", line)

    def _fake_response(self, messages: List[Dict[str, str]]) -> str:
        user_content = messages[-1]["content"] if messages else ""
        snippet = user_content.strip().replace("\n", " ")
        snippet = snippet[:260] + ("..." if len(snippet) > 260 else "")
        return (
            "【本地调试回答】当前未配置可用的 LLM_API_KEY，因此返回本地 fallback 结果。\n\n"
            "我会基于你提供的任务与原文片段进行分析。可见上下文摘要："
            f"{snippet}\n\n"
            "接入真实 OpenAI-compatible 模型后，这里会生成更完整的文学细读、引用依据和结构化分析。"
        )


llm_service = LLMService()

