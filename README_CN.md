# Oriflow-Agent BETA 1.0

Oriflow-Agent 是一个工作流引擎原型，支持插件化节点、运行时编排以及基于大模型的节点扩展。

仓库结构要点
- `main.py` — FastAPI 服务入口，包含管理与运行时相关 API。
- `Workflow/` — 运行引擎与辅助模块（`WorkflowEngine`、`PinManager`、`InCommunicateHub`、`ExCommunicateHub`、`FlowListener`、`Interrupt`）。
- `Nodes/` — 节点基类与插件加载器。
- `Plugins/` — 内置节点实现（基础节点与 LLM 节点）。
- `Docs/` — 文档：节点 context、`param_config` 参考、HTTP API 说明等。

快速开始
1. 安装依赖：
```bash
pip install -r requirements.txt
```
2. 启动服务：
```bash
python main.py
# 或
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

安装（含 requirements）
1. 推荐先升级 pip：

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Docker 使用
1. 构建镜像：

```bash
docker build -t oriflow-agent .
```

2. 运行容器（对外映射 8000 端口）：

```bash
docker run --rm -p 8000:8000 \
	-e OPENAI_API_KEY="<你的-openai-key>" \
	oriflow-agent
```

说明：
- 镜像默认以 `uvicorn main:app` 启动服务。若 LLM 插件需要凭证，可通过环境变量传入 `OPENAI_API_KEY` 或者启动后调用 `/llm/save` API 动态设置。
- 本地开发推荐直接用 `uvicorn ... --reload`，便于热重载调试。

主要接口
- `/plugins/` — 获取插件列表
- `/workflow/*` — 创建/修改/读取/删除/列出工作流
- `/runtime/*` — 启动工作流与处理人工输入（文本/数字/checkbox/chatbox）
- `/llm/*` — 获取/保存运行时 LLM 配置
- `/filebase/*` — 列出生成的文件

文档位置
- 节点 context 列表：`Docs/nodes_contexts_v2.md`
- 参数配置参考：`Docs/param_config_reference.md`
- HTTP API：`Docs/Server_API.md`

发布与贡献
此项目为后端原型；如需改进请在仓库中创建 issue 或提交 PR。
