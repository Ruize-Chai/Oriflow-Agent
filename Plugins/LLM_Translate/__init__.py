from typing import Any

from Plugins.LLM_Answer import Self_Node as BaseLLM


class Self_Node(BaseLLM):
    """LLM_Translate：继承自 LLM_Answer，设置缺省 prompt_template 用于翻译任务。

    如果需要目标语言，请在 `params.param_config.target_lang` 中指定。
    """

    def __init__(self, data: dict, **kwargs) -> None:
        super().__init__(data, **kwargs)
        try:
            params = self.params or {}
            pc = params.get("param_config", {}) or {}
            target = pc.get("target_lang", "English")
            pc.setdefault("prompt_template", f"Translate the context to {target}:\n{{context}}")
            params["param_config"] = pc
            self.params = params
        except Exception:
            pass
