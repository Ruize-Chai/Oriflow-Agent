from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from Nodes.node import Node

try:
    from Server.llm_adapter import LLMAdapter
except Exception:
    LLMAdapter = None


class Self_node(Node):
    """简单的 LLM Answer 插件。

    node_data['params'] 可包含:
      - model: 模型名 (默认 'gpt-3.5-turbo')
      - provider: 'openai' (默认)
      - prompt_template: 可选，字符串模板，使用 payload 作为格式化上下文
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.model = self.params.get("model", "gpt-3.5-turbo")
        self.provider = self.params.get("provider", "openai")
        self.prompt_template = self.params.get("prompt_template")
        # instantiate adapter lazily
        self._adapter = None

    def _get_adapter(self):
        if self._adapter is None:
            if LLMAdapter is None:
                raise RuntimeError("LLMAdapter not available; please install openai package")
            self._adapter = LLMAdapter(provider=self.provider)
        return self._adapter

    async def execute(self, payload: Any) -> Any:
        """执行 LLM 调用并将结果写入节点输出（返回值）。

        payload 可以是字符串或 dict；如果提供 `prompt_template`，会用 `str.format` 格式化。
        """
        prompt = None
        if isinstance(payload, str):
            prompt = payload
        elif isinstance(payload, dict):
            # 如果 payload 包含 'text' 字段优先使用
            prompt = payload.get("text") or str(payload)
        else:
            prompt = str(payload)

        if self.prompt_template:
            try:
                prompt = self.prompt_template.format(payload=payload)
            except Exception:
                # fallback to raw
                pass

        adapter = self._get_adapter()
        # build messages for chat completion
        messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]

        # call adapter
        try:
            resp = await adapter.chat(self.model, messages)
        except Exception as e:
            return {"error": str(e)}

        # extract text from common OpenAI response structure
        try:
            # chat completion
            choice = resp.get("choices", [])[0]
            delta = choice.get("message") if isinstance(choice.get("message"), dict) else None
            if delta:
                return delta.get("content")
            # legacy completion
            text = choice.get("text")
            if text:
                return text
        except Exception:
            pass

        # fallback: return full response
        return resp


__all__ = ["Self_node"]
