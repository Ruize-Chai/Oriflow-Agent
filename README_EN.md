# Oriflow-Agent BETA 1.0

Oriflow-Agent is a prototype workflow engine that supports plugin-based nodes, runtime orchestration, and LLM-driven nodes.

Contents
- `main.py` — FastAPI server entrypoint exposing management and runtime APIs.
- `Workflow/` — Runtime engine and helpers (`WorkflowEngine`, `PinManager`, `InCommunicateHub`, `ExCommunicateHub`, `FlowListener`, `Interrupt`).
- `Nodes/` — Node base classes and plugin loader.
- `Plugins/` — Built-in node implementations (basic and LLM plugins).
- `Docs/` — Documentation: node contexts, param_config reference, server API.

Quick Start
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Run server:
```bash
python main.py
# or
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Installation (with requirements)
- Install from the repository root:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Docker
- Build image:

```bash
docker build -t oriflow-agent .
```

- Run container (exposes port 8000):

```bash
docker run --rm -p 8000:8000 \
	-e OPENAI_API_KEY="<your-key>" \
	oriflow-agent
```

- Notes:
	- The image starts `uvicorn main:app` by default. Use environment variables (for example `OPENAI_API_KEY`) if your LLM plugins require them, or use the `/llm/save` API to set LLM credentials at runtime.
	- For development, prefer `uvicorn main:app --reload` on the host for faster iteration.

Key API endpoints
- `/plugins/` — list available plugins
- `/workflow/*` — create/alter/get/delete/list workflows
- `/runtime/*` — run workflows and handle human inputs
- `/llm/*` — get/save LLM runtime configuration
- `/filebase/*` — list generated files

Documentation
- Node contexts: `Docs/nodes_contexts_v2.md`
- Param config reference: `Docs/param_config_reference.md`
- Server API: `Docs/Server_API.md`

License & Contribution
This is an internal prototype. Please open issues or PRs in the repository for changes.
