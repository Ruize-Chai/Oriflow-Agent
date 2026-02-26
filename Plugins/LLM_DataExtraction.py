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
    """LLM_DataExtraction: 从文本中抽取结构化数据（基于字段提示），并可保存到 FileBase。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.model = self.params.get("model", "gpt-3.5-turbo")
        self.provider = self.params.get("provider", "openai")
        self.fields = self.params.get("fields", [])
        self.save_to_file = bool(self.params.get("save_to_file", False))
        self.file_dir = os.path.join(os.getcwd(), "FileBase")
        os.makedirs(self.file_dir, exist_ok=True)

    async def execute(self, payload: Any) -> Any:
        text = None
        if isinstance(payload, dict):
            text = payload.get("text") or payload.get("content")
        elif isinstance(payload, str):
            text = payload
        else:
            text = str(payload)

        if not text:
            return {"error": "no text to extract from"}

        if LLMAdapter is None:
            return {"error": "LLMAdapter not available"}

        fields_desc = ", ".join(self.fields) if self.fields else "key information"
        adapter = LLMAdapter(provider=self.provider)
        prompt = f"Extract the following fields ({fields_desc}) from the text and return JSON:\n\n{text}"
        messages = [{"role": "user", "content": prompt}]
        try:
            resp = await adapter.chat(self.model, messages)
        except Exception as e:
            return {"error": str(e)}

        extracted = None
        try:
            choice = resp.get("choices", [])[0]
            msg = choice.get("message") or {}
            extracted = msg.get("content") or choice.get("text")
        except Exception:
            extracted = None

        out = {"extracted": extracted if extracted is not None else resp}
        if self.save_to_file and isinstance(extracted, str):
            filename = f"extracted_{uuid.uuid4().hex}.json"
            path = os.path.join(self.file_dir, filename)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(extracted)
                out["file"] = path
            except Exception as e:
                out["file_error"] = str(e)

        return out


__all__ = ["Self_node"]
