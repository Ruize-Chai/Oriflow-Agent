from __future__ import annotations

from typing import Any, Dict, List
import os
import uuid

from Nodes.node import Node

try:
    from Server.llm_adapter import LLMAdapter
except Exception:
    LLMAdapter = None


class Self_node(Node):
    """LLM_Conversation: 管理简单会话状态，累积消息并调用 LLM 生成回复。

    state 存在于实例属性 `_history`。
    可选参数：`save_to_file` 将会话记录保存到 FileBase。
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.model = self.params.get("model", "gpt-3.5-turbo")
        self.provider = self.params.get("provider", "openai")
        self.save_to_file = bool(self.params.get("save_to_file", False))
        self.file_dir = os.path.join(os.getcwd(), "FileBase")
        os.makedirs(self.file_dir, exist_ok=True)
        self._history: List[Dict[str, str]] = []

    async def execute(self, payload: Any) -> Any:
        # 有效负载可以是字符串，或形如 {"role":..., "content":...} 的字典
        if isinstance(payload, dict) and payload.get("role") and payload.get("content"):
            self._history.append({"role": payload["role"], "content": payload["content"]})
        elif isinstance(payload, str):
            self._history.append({"role": "user", "content": payload})
        else:
            self._history.append({"role": "user", "content": str(payload)})

        if LLMAdapter is None:
            return {"error": "LLMAdapter not available"}

        adapter = LLMAdapter(provider=self.provider)
        try:
            resp = await adapter.chat(self.model, self._history)
        except Exception as e:
            return {"error": str(e)}

        reply = None
        try:
            choice = resp.get("choices", [])[0]
            msg = choice.get("message") or {}
            reply = msg.get("content") or choice.get("text")
        except Exception:
            reply = None

        if reply is not None:
            self._history.append({"role": "assistant", "content": reply})

        out = {"reply": reply if reply is not None else resp}
        if self.save_to_file and self._history:
            filename = f"conv_{uuid.uuid4().hex}.txt"
            path = os.path.join(self.file_dir, filename)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    for m in self._history:
                        f.write(f"{m['role']}: {m['content']}\n")
                out["file"] = path
            except Exception as e:
                out["file_error"] = str(e)

        return out


__all__ = ["Self_node"]
