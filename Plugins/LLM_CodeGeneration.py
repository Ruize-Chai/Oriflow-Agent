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
    """LLM_CodeGeneration：根据描述生成代码文件并保存到 `FileBase`。

    params:
        - language: 文件扩展名或语言提示（例如 'py')
        - filename_prefix: 可选的文件名前缀
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.model = self.params.get("model", "gpt-3.5-turbo")
        self.provider = self.params.get("provider", "openai")
        self.lang = self.params.get("language", "py")
        self.prefix = self.params.get("filename_prefix", "gen")
        self.file_dir = os.path.join(os.getcwd(), "FileBase")
        os.makedirs(self.file_dir, exist_ok=True)

    async def execute(self, payload: Any) -> Any:
        # 有效负载示例: {"prompt": str} 或直接为字符串描述
        prompt = None
        if isinstance(payload, dict):
            prompt = payload.get("prompt") or payload.get("description")
        elif isinstance(payload, str):
            prompt = payload
        else:
            prompt = str(payload)

        if not prompt:
            return {"error": "no prompt provided"}

        if LLMAdapter is None:
            return {"error": "LLMAdapter not available"}

        adapter = LLMAdapter(provider=self.provider)
        messages = [{"role": "user", "content": f"Generate {self.lang} code for: {prompt}"}]
        try:
            resp = await adapter.chat(self.model, messages)
        except Exception as e:
            return {"error": str(e)}

        code = None
        try:
            choice = resp.get("choices", [])[0]
            msg = choice.get("message") or {}
            code = msg.get("content") or choice.get("text")
        except Exception:
            code = None

        if not code:
            return {"response": resp}

        filename = f"{self.prefix}_{uuid.uuid4().hex}.{self.lang}"
        path = os.path.join(self.file_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            return {"file": path, "code": code}
        except Exception as e:
            return {"error": str(e), "code": code}


__all__ = ["Self_node"]
