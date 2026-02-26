from __future__ import annotations

from typing import Any, Dict
import uuid
import os

from Nodes.node import Node

try:
    from Server.llm_adapter import LLMAdapter
except Exception:
    LLMAdapter = None


class Self_node(Node):
    """LLM_FileProduction: 生成长文本/文件内容并保存到 `FileBase`，返回文件路径。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.model = self.params.get("model", "gpt-3.5-turbo")
        self.provider = self.params.get("provider", "openai")
        self.filename_prefix = self.params.get("filename_prefix", "output")
        self.extension = self.params.get("extension", "txt")
        self.file_dir = os.path.join(os.getcwd(), "FileBase")
        os.makedirs(self.file_dir, exist_ok=True)

    async def execute(self, payload: Any) -> Any:
        # 有效负载示例: {"prompt": str}，有效负载应包含 prompt 字段或直接为字符串
        prompt = None
        if isinstance(payload, dict):
            prompt = payload.get("prompt") or payload.get("content")
        elif isinstance(payload, str):
            prompt = payload
        else:
            prompt = str(payload)

        if not prompt:
            return {"error": "no prompt provided"}

        if LLMAdapter is None:
            return {"error": "LLMAdapter not available"}

        adapter = LLMAdapter(provider=self.provider)
        messages = [{"role": "user", "content": prompt}]
        try:
            resp = await adapter.chat(self.model, messages)
        except Exception as e:
            return {"error": str(e)}

        content = None
        try:
            choice = resp.get("choices", [])[0]
            msg = choice.get("message") or {}
            content = msg.get("content") or choice.get("text")
        except Exception:
            content = None

        if content is None:
            return {"response": resp}

        filename = f"{self.filename_prefix}_{uuid.uuid4().hex}.{self.extension}"
        path = os.path.join(self.file_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"file": path}
        except Exception as e:
            return {"error": str(e)}


__all__ = ["Self_node"]
