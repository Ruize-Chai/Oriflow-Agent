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
    """LLM_QA: 基于提供的 context 回答问题；可将长答案保存到 FileBase 文件。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.model = self.params.get("model", "gpt-3.5-turbo")
        self.provider = self.params.get("provider", "openai")
        self.save_to_file = bool(self.params.get("save_to_file", False))
        self.file_dir = os.path.join(os.getcwd(), "FileBase")
        os.makedirs(self.file_dir, exist_ok=True)

    async def execute(self, payload: Any) -> Any:
        # 有效负载示例: {"question": str, "context": str}
        if not isinstance(payload, dict):
            return {"error": "payload must be dict with question/context"}
        question = payload.get("question")
        context = payload.get("context")
        if not question:
            return {"error": "question missing"}

        if LLMAdapter is None:
            return {"error": "LLMAdapter not available"}

        adapter = LLMAdapter(provider=self.provider)
        prompt = f"Answer the question based on the context below.\n\nContext:\n{context}\n\nQuestion:\n{question}"
        messages = [{"role": "user", "content": prompt}]
        try:
            resp = await adapter.chat(self.model, messages)
        except Exception as e:
            return {"error": str(e)}

        # extract answer
        answer = None
        try:
            choice = resp.get("choices", [])[0]
            msg = choice.get("message") or {}
            answer = msg.get("content") or choice.get("text")
        except Exception:
            answer = None

        out = {"answer": answer if answer is not None else resp}
        if self.save_to_file and isinstance(answer, str):
            filename = f"qa_{uuid.uuid4().hex}.txt"
            path = os.path.join(self.file_dir, filename)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(answer)
                out["file"] = path
            except Exception as e:
                out["file_error"] = str(e)

        return out


__all__ = ["Self_node"]
