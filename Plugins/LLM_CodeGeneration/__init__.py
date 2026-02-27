from typing import Any

from Plugins.LLM_Answer import Self_Node as BaseLLM


class Self_Node(BaseLLM):
    """LLM_CodeGeneration：继承自 LLM_Answer，设置缺省 prompt_template 用于代码生成。

    可通过 `params.param_config.language` 指定目标编程语言。
    """

    def __init__(self, data: dict, **kwargs) -> None:
        super().__init__(data, **kwargs)
        try:
            params = self.params or {}
            pc = params.get("param_config", {}) or {}
            lang = pc.get("language", "Python")
            pc.setdefault("prompt_template", f"Generate {lang} code for the following specification:\n{{context}}")
            params["param_config"] = pc
            self.params = params
        except Exception:
            pass
