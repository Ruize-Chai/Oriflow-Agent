# 后端 HTTP 服务接口参考

本文档列出仓库中已实现的 HTTP 服务路由、方法、请求/响应示例与注意事项，便于前端或外部系统集成。

基础信息
- 服务器入口：`main.py`（FastAPI app），已包含并注册下列子路由模块。
- 路由前缀：按模块划分 `/plugins`, `/workflow`, `/runtime`, `/llm`, `/filebase`。

说明约定
- 所有请求与响应使用 JSON。
- `in_hub`：后端内部接收前端主动输入（由 `/runtime` 的输入路由写入）；`ex_hub`：后端对外寄存（前端通过 GET 获取并在需要时清除或读取）。

1. 插件列表
- GET `/plugins/`
  - 描述：返回 `Plugins/pluginLists.json` 中声明的插件分组。
  - 请求：无
  - 响应示例：
    {
      "basic_plugins": [...],
      "llm_plugins": [...]
    }

2. 工作流管理（Workflow）
- POST `/workflow/create`
  - 描述：创建/保存工作流，若未提供 `id` 则生成 UUID。
  - 请求体：工作流 payload（示例字段 `id`, `name`, `nodes`）
  - 响应：{"status":"ok","id": "..."}

- POST `/workflow/alter`
  - 描述：更新已存在的工作流（需包含 `id`）。
  - 请求体：工作流 payload
  - 响应：{"status":"ok","id": "..."}

- GET `/workflow/{workflow_id}`
  - 描述：按 id 读取工作流文件（来自 `WorkflowBase/{id}.json`）。

- POST `/workflow/delete`
  - 描述：删除工作流（请求体需包含 `id`）。
  - 响应：{"status":"ok"}

- GET `/workflow/list`
  - 描述：返回 `WorkflowBase/workflowlists.json` 列表（数组，每项包含 `id` 与 `filename`）。

3. 运行时控制（Runtime）
- POST `/runtime/run`
  - 描述：启动一个工作流运行实例（非阻塞）。
  - 请求体：{"workflow_id": "..."}
  - 响应：{"status":"started","nodes": [...state snapshot...]}（`nodes` 为 `FlowListener.read()` 的快照）

- POST `/runtime/{workflow_id}/input/text`
  - 描述：用于向处于 `TEXT_INPUT` 状态的节点发送文本输入。
  - 请求体：{"node_id": N, "value": "..."}

- POST `/runtime/{workflow_id}/input/number`
  - 描述：向 `NUMBER_INPUT` 节点发送数字输入。
  - 请求体：{"node_id": N, "value": 123}

- GET `/runtime/{workflow_id}/checkbox/{node_id}`
  - 描述：获取 checkbox 节点的当前选项缓存（来自 `ex_hub.read(node_id)`)。

- POST `/runtime/{workflow_id}/checkbox/{node_id}`
  - 描述：提交 checkbox 选择结果（前端 POST 后端再写入 `in_hub`）。
  - 请求体：{"selection": [...]}（同时会写入 `in_hub.send(node_id, {"selection": [...]})`）

- GET `/runtime/{workflow_id}/chatbox/{node_id}`
  - 描述：获取并清除 chatbox 输出（使用 `ex_hub.fetch(node_id)`，前端会得到一次性消息）。

- POST `/runtime/interrupt`
  - 描述：广播中断请求到所有运行实例（会触发 `Interrupt.set_true()`）。

4. LLM 管理
- GET `/llm/`
  - 描述：返回当前运行时 LLM 配置（由 `Workflow/llm_config.get_llm_api()` 提供）。
  - 响应示例：{"api_key": null, "endpoint": null}

- POST `/llm/save`
  - 描述：保存/覆盖运行时 LLM 配置（仅在内存中），字段：{"api_key":..., "endpoint":...}

5. FileBase
- GET `/filebase/list`
  - 描述：返回 `FileBase/filebaselists.json` 或该目录下文件列表。

注意事项与集成提示
- `main.py` 已将上述 routers 全部 `include_router`，启动服务直接运行 `python main.py`（需安装 `uvicorn`, `fastapi`）。
- 运行期状态与数据流：
  - 前端想要接收节点交互（文本/数字/checkbox/chatbox），应轮询或在用户操作时调用对应 `/runtime/...` 路由。
  - 节点内部由 `WorkflowEngine` 注入的 `in_hub`/`ex_hub`/`listener`/`pin_manager` 等负责协调节点执行与前端交互。

示例启动命令
```bash
pip install -r requirements.txt
python main.py
# 或使用 uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

若需要，我可以：
- 将本 API 文档摘要加入 `Docs/nodes_contexts_v2.md`（把服务接口也列入主文档）。
- 启动本地服务器并演示一次 `POST /workflow/create` + `POST /runtime/run` 的调用流程。
