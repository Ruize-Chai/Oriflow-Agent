from typing import Any, List, Dict
import os
import json
import uuid

from Nodes.node import Node


class Self_Node(Node):
    """LLM_GenerateWorkflow：使用 LLM 生成并保存 workflow JSON 至 `WorkflowBase/`。

    行为（按 DesignFull）：
    - 采集 `params.context_slot` 指定的上下文作为生成输入。
    - 使用全局 `Workflow.llm_config` 提供的 api_key/endpoint 调用 LLM（与 `LLM_Answer` 类似），生成 workflow 内容。
    - 将生成结果保存为 `WorkflowBase/{workflow_id}.json`（如果能解析为 JSON 则保存为 JSON，否则保存为文本）。
    - 更新或创建 `WorkflowBase/workflowlists.json`，将新 workflow 的元数据（id, filename）加入列表。
    - 在节点 `context` 中写入 `workflow_id` 与 `path`，并缓存到 `ex_hub` 以供前端读取。

    Context Outputs:
    - `workflow_id` (str): 生成的 workflow 唯一 id（文件名，不含扩展名）。
    - `path` (str): 文件系统路径，例：`WorkflowBase/{workflow_id}.json`。
    """

    def __init__(self, data: dict, llm_config=None, **kwargs) -> None:
        super().__init__(data, **kwargs)
        self.llm_config = llm_config

    def _gather_contexts(self) -> List[str]:
        params = self.params or {}
        slots = params.get("context_slot", [])
        results: List[str] = []
        node_getter = getattr(self, "node_getter", None)
        for s in slots:
            try:
                sid = int(s.get("id"))
                key = s.get("key")
            except Exception:
                continue

            if sid == self.node_id:
                if isinstance(self.context, dict) and key in self.context:
                    results.append(str(self.context.get(key)))
                    continue
                for c in (self.contexts or []):
                    if isinstance(c, dict) and key in c:
                        results.append(str(c.get(key)))
                        continue

            if callable(node_getter):
                try:
                    target = node_getter(sid)
                    if target is not None:
                        tctx = getattr(target, "context", None)
                        if isinstance(tctx, dict) and key in tctx:
                            results.append(str(tctx.get(key)))
                            continue
                        for c in getattr(target, "contexts", []) or []:
                            if isinstance(c, dict) and key in c:
                                results.append(str(c.get(key)))
                                continue
                except Exception:
                    pass

        return results

    def _call_llm(self, prompt: str, cfg: Dict[str, Any]) -> str:
        # Reuse simple openai usage pattern from LLM_Answer but keep local and tolerant
        api_key = None
        endpoint = None
        try:
            if self.llm_config is not None:
                cfgvals = getattr(self.llm_config, "get_llm_api", lambda: {"api_key": None, "endpoint": None})()
            else:
                from Workflow.llm_config import get_llm_api

                cfgvals = get_llm_api()
            api_key = cfgvals.get("api_key")
            endpoint = cfgvals.get("endpoint")
        except Exception:
            api_key = None
            endpoint = None

        try:
            import openai

            if api_key:
                try:
                    setattr(openai, "api_key", api_key)
                except Exception:
                    pass
            if endpoint:
                try:
                    setattr(openai, "api_base", endpoint)
                except Exception:
                    pass

            Completion = getattr(openai, "Completion", None)
            if Completion is not None:
                resp = Completion.create(model=cfg.get("model", "text-davinci-003"), prompt=prompt, max_tokens=cfg.get("max_tokens", 512))
                return getattr(resp.choices[0], "text", "") if getattr(resp, "choices", None) else ""

            ChatCompletion = getattr(openai, "ChatCompletion", None)
            if ChatCompletion is not None:
                resp = ChatCompletion.create(model=cfg.get("model", "gpt-3.5-turbo"), messages=[{"role": "user", "content": prompt}], max_tokens=cfg.get("max_tokens", 512))
                if getattr(resp, "choices", None):
                    choice0 = resp.choices[0]
                    try:
                        return choice0.message.get("content")
                    except Exception:
                        return getattr(choice0, "text", "")

            return ""
        except Exception as e:
            return f"LLM call failed: {e}"

    def _save_workflow(self, content: str, as_json: bool = True) -> Dict[str, str]:
        base_dir = os.path.join(os.getcwd(), "WorkflowBase")
        os.makedirs(base_dir, exist_ok=True)
        wid = str(uuid.uuid4())
        filename = f"{wid}.json"
        path = os.path.join(base_dir, filename)

        try:
            if as_json:
                # try parsing content as JSON
                parsed = json.loads(content)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception:
            # fallback: write raw text
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

        # update workflowlists.json
        lists_path = os.path.join(base_dir, "workflowlists.json")
        try:
            if os.path.exists(lists_path):
                with open(lists_path, "r", encoding="utf-8") as f:
                    lists = json.load(f)
            else:
                lists = []
        except Exception:
            lists = []

        entry = {"id": wid, "filename": filename}
        lists.append(entry)
        try:
            with open(lists_path, "w", encoding="utf-8") as f:
                json.dump(lists, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return {"workflow_id": wid, "path": path}

    def execute(self) -> List[int]:
        params = self.params or {}
        cfg = params.get("param_config", {}) or {}

        contents = self._gather_contexts()
        prompt = cfg.get("prompt_template") or ("Generate a workflow JSON from the context:\n{context}".replace("{context}", "\n".join(contents)))

        # call LLM
        generated = self._call_llm(prompt, cfg)

        # try save as json if possible
        saved = self._save_workflow(generated, as_json=True)

        # write into node context and ex_hub
        try:
            if not isinstance(self.context, dict):
                self.context = {}
            self.context.update(saved)
        except Exception:
            pass

        ex_hub = getattr(self, "ex_hub", None)
        if ex_hub is not None:
            try:
                ex_hub.cache(self.node_id, saved)
            except Exception:
                pass

        listener = getattr(self, "listener", None)
        if listener is not None:
            try:
                listener.set_state(self.node_id, "OUTPUT")
            except Exception:
                pass

        return list(range(len(self.outputs or [])))
