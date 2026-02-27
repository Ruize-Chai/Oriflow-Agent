import json
import os
from typing import Any, Dict, List, Optional


BASE = os.getcwd()
WORKFLOW_DIR = os.path.join(BASE, "WorkflowBase")
FILEBASE_DIR = os.path.join(BASE, "FileBase")
PLUGIN_LISTS = os.path.join(BASE, "Plugins", "pluginLists.json")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_plugin_lists() -> Dict[str, Any]:
    try:
        with open(PLUGIN_LISTS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"basic_plugins": [], "llm_plugins": []}


def read_workflow_lists() -> List[Dict[str, Any]]:
    ensure_dir(WORKFLOW_DIR)
    p = os.path.join(WORKFLOW_DIR, "workflowlists.json")
    try:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_workflow_lists(lists: List[Dict[str, Any]]) -> None:
    ensure_dir(WORKFLOW_DIR)
    p = os.path.join(WORKFLOW_DIR, "workflowlists.json")
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(lists, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def save_workflow(workflow_id: str, payload: Dict[str, Any]) -> str:
    ensure_dir(WORKFLOW_DIR)
    filename = f"{workflow_id}.json"
    path = os.path.join(WORKFLOW_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    lists = read_workflow_lists()
    # replace or append
    found = False
    for e in lists:
        if e.get("id") == workflow_id:
            e["filename"] = filename
            found = True
            break
    if not found:
        lists.append({"id": workflow_id, "filename": filename})
    save_workflow_lists(lists)
    return path


def load_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
    ensure_dir(WORKFLOW_DIR)
    path = os.path.join(WORKFLOW_DIR, f"{workflow_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def delete_workflow(workflow_id: str) -> bool:
    ensure_dir(WORKFLOW_DIR)
    path = os.path.join(WORKFLOW_DIR, f"{workflow_id}.json")
    try:
        if os.path.exists(path):
            os.remove(path)
        lists = read_workflow_lists()
        lists = [e for e in lists if e.get("id") != workflow_id]
        save_workflow_lists(lists)
        return True
    except Exception:
        return False


def read_filebase_lists() -> List[Dict[str, Any]]:
    ensure_dir(FILEBASE_DIR)
    p = os.path.join(FILEBASE_DIR, "filebaselists.json")
    try:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    # fallback: list files
    try:
        files = [f for f in os.listdir(FILEBASE_DIR) if os.path.isfile(os.path.join(FILEBASE_DIR, f))]
        return [{"filename": fn} for fn in files]
    except Exception:
        return []
