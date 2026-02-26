"""简易 LLM adapter，基于 OpenAI SDK 的异步封装。

当前实现支持 provider='openai'，通过环境变量 `OPENAI_API_KEY` 注入凭证。
如果本地没有可用的异步方法，会回退到线程池执行同步调用。

注意：这只是一个最小适配层，后续可扩展 provider、限速、重试和并发控制。
"""
from __future__ import annotations

import os
import asyncio
import inspect
from typing import Any, Dict, Optional

try:
    import openai
except Exception:
    openai = None
try:
    import httpx
except Exception:
    httpx = None


class LLMAdapter:
    """最小化 LLM 适配器，支持类似 OpenAI 的 chat completion 接口。

    用法示例：
        adapter = LLMAdapter(provider='openai')
        resp = await adapter.chat("gpt-3.5-turbo", messages=[{"role":"user","content":"Hello"}])
    """

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        self.provider = provider
        # prefer explicit api_key, then environment, then keys manager
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            try:
                from Server.keys_manager import get_api_key

                self.api_key = get_api_key("openai")
            except Exception:
                self.api_key = None

        if self.provider == "openai":
            if openai is None:
                raise RuntimeError("openai package not installed")
            if self.api_key:
                openai.api_key = self.api_key

    async def chat(self, model: str, messages: Any, **kwargs) -> Any:
        """Perform a chat completion. Returns the raw provider response dict.

        `messages` should be a list of {role, content} dicts.
        """
        if self.provider != "openai":
            raise RuntimeError("unsupported provider")

        # Try several call patterns to support multiple openai SDK versions.
        loop = asyncio.get_event_loop()

        errors = []

        # If openai SDK is available, detect its version and choose a safe code path.
        if openai is not None:
            ver = getattr(openai, "VERSION", None) or getattr(openai, "__version__", None) or getattr(openai, "version", None)
            major = None
            try:
                if ver is not None:
                    major = int(str(ver).split(".")[0])
            except Exception:
                major = None

            # For openai >= 1.x: avoid legacy top-level ChatCompletion/Completion access
            if major is not None and major >= 1:
                    # Prefer AsyncOpenAI client when available
                    if not self.api_key:
                        errors.append("openai>=1 detected but no API key configured (set OPENAI_API_KEY or pass api_key)")
                    else:
                        # Try async client first (use getattr to avoid static attribute access)
                        AsyncOpenAICls = getattr(openai, "AsyncOpenAI", None)
                        if AsyncOpenAICls is not None:
                            try:
                                async_client = AsyncOpenAICls(api_key=self.api_key)
                                chat = getattr(async_client, "chat", None)
                                comps = getattr(chat, "completions", None)
                                create = getattr(comps, "create", None)
                                if callable(create):
                                    try:
                                        res = create(model=model, messages=messages, **kwargs)
                                        if inspect.isawaitable(res):
                                            return await res
                                        return res
                                    except Exception as e:
                                        errors.append(f"AsyncOpenAI create error: {e}")
                            except Exception as e:
                                errors.append(f"AsyncOpenAI client error: {e}")

                        # Try sync client via threadpool (use getattr to avoid static attribute access)
                        OpenAICls = getattr(openai, "OpenAI", None)
                        if OpenAICls is not None:
                            try:
                                client = OpenAICls(api_key=self.api_key)
                                chat = getattr(client, "chat", None)
                                comps = getattr(chat, "completions", None)
                                create = getattr(comps, "create", None)
                                if callable(create):
                                    return await loop.run_in_executor(None, lambda: create(model=model, messages=messages, **kwargs))
                            except Exception as e:
                                errors.append(f"OpenAI client sync error: {e}")

                # we've handled the modern client path (or collected errors); skip legacy attribute access
            else:
                # old-style openai (<1.0) - attempt legacy interfaces below
                try:
                    ChatCompletion = getattr(openai, "ChatCompletion", None)
                    acreate = getattr(ChatCompletion, "acreate", None)
                    if callable(acreate):
                        try:
                            res = acreate(model=model, messages=messages, **kwargs)
                            if inspect.isawaitable(res):
                                return await res
                            return res
                        except Exception as e:
                            errors.append(f"ChatCompletion.acreate error: {e}")
                except Exception as e:
                    errors.append(f"ChatCompletion.acreate lookup error: {e}")

                try:
                    ChatCompletion = getattr(openai, "ChatCompletion", None)
                    create = getattr(ChatCompletion, "create", None)
                    if callable(create):
                        def _sync_chat():
                            return create(model=model, messages=messages, **kwargs)

                        return await loop.run_in_executor(None, _sync_chat)
                except Exception as e:
                    errors.append(f"ChatCompletion.create error: {e}")

                try:
                    Completion = getattr(openai, "Completion", None)
                    create2 = getattr(Completion, "create", None)
                    if callable(create2):
                        def _sync_completion():
                            return create2(model=model, prompt=messages, **kwargs)

                        return await loop.run_in_executor(None, _sync_completion)
                except Exception as e:
                    errors.append(f"Completion.create error: {e}")

        # Fallback: direct HTTP call to OpenAI REST API via httpx (if available)
        if httpx is not None and self.api_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                    payload = {"model": model, "messages": messages}
                    for k, v in kwargs.items():
                        payload[k] = v

                    resp = await client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                errors.append(f"HTTP fallback error: {e}")

        # Diagnostics for user: list available top-level attrs on openai (or note none)
        available = [] if openai is None else sorted([attr for attr in dir(openai) if not attr.startswith("_")])
        msg = (
            "No supported OpenAI chat completion method succeeded.\n"
            f"Attempts errors: {errors}\n"
            f"openai module present: {openai is not None}; top-level attrs: {available}\n"
            "Ensure you have a compatible 'openai' package or set an API key for HTTP fallback."
        )
        raise RuntimeError(msg)


__all__ = ["LLMAdapter"]
