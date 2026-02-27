from typing import Any

from Plugins.LLM_Answer import Self_Node as BaseLLM


class Self_Node(BaseLLM):
    """LLM_Conversation：继承自 LLM_Answer，设置缺省 prompt_template 用于对话风格生成。"""

    def __init__(self, data: dict, **kwargs) -> None:
        super().__init__(data, **kwargs)
        try:
            params = self.params or {}
            pc = params.get("param_config", {}) or {}
            pc.setdefault("prompt_template", "You are a helpful assistant. Context:\n{context}")
            params["param_config"] = pc
            self.params = params
        except Exception:
            pass
