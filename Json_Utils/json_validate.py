import json
from typing import Any, Union

from pydantic import ValidationError

from Schema.payload.node_payload import NodePayload
from Schema.payload.workflow_payload import WorkflowPayload
from Logger import (
    NodePayloadValidationError,
    WorkflowPayloadValidationError,
    NodeDictValidationError,
    WorkflowDictValidationError,
    JSONDoesNotRepresentObject,
    InvalidJSON,
    UnsupportedDataTypeError,
)

# more specific node/workflow field errors
from Logger import (
    PayloadNotADict,
    TypeMissingOrInvalid,
    InputsMissingOrInvalid,
    OutputsMissingOrInvalid,
    ParamsMissingOrInvalid,
    ListenMissingOrInvalid,
    WorkflowIDMissingOrInvalid,
    EntryMissingOrInvalid,
    NodesMissingOrInvalid,
    EachNodeMustBeObject,
    NodeIDMustBeInteger,
    NodeTypeMustBeString,
)

#安全转化dict
def _ensure_dict(data: Union[str, dict, Any]) -> dict:
    """尝试把输入转为 dict,失败时抛出 ValueError。"""
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                return parsed
            raise JSONDoesNotRepresentObject()
        except Exception as e:
            raise InvalidJSON(str(e))
    raise UnsupportedDataTypeError()

#校验node pydantic payload
def is_valid_node_payload(data: Union[str, dict, Any]) -> bool:
    """验证 `NodePayload`，校验失败时抛出 `NodePayloadValidationError`。成功返回 True。"""
    try:
        d = _ensure_dict(data)
    except ValueError as e:
        raise NodePayloadValidationError(str(e))
    try:
        NodePayload(**d)
        return True
    except ValidationError as ve:
        raise NodePayloadValidationError(str(ve))
    except Exception as e:
        raise NodePayloadValidationError(str(e))

#校验workflow pydantic payload
def is_valid_workflow_payload(data: Union[str, dict, Any]) -> bool:
    """验证 `WorkflowPayload`，校验失败时抛出 `WorkflowPayloadValidationError`。成功返回 True。"""
    try:
        d = _ensure_dict(data)
    except ValueError as e:
        raise WorkflowPayloadValidationError(str(e))
    try:
        WorkflowPayload(**d)
        return True
    except ValidationError as ve:
        raise WorkflowPayloadValidationError(str(ve))
    except Exception as e:
        raise WorkflowPayloadValidationError(str(e))

#校验node python dict
def is_valid_node_dict(d: Any) -> bool:
    """针对已解析的 Python dict 做结构校验，校验失败时抛出 `NodeDictValidationError`。"""
    if not isinstance(d, dict):
        raise PayloadNotADict()
    # 必需字段
    if "type" not in d or not isinstance(d["type"], str):
        raise TypeMissingOrInvalid()
    # inputs
    inputs = d.get("inputs", [])
    if not isinstance(inputs, list) or not all(isinstance(i, int) for i in inputs):
        raise InputsMissingOrInvalid()
    # outputs
    outputs = d.get("outputs", [])
    if not isinstance(outputs, list) or not all((isinstance(o, int) or o is None) for o in outputs):
        raise OutputsMissingOrInvalid()
    # params
    params = d.get("params", None)
    if not isinstance(params, dict):
        raise ParamsMissingOrInvalid()
    # context_slot in params should be list of objects {id:int, key:str}
    context_slot = params.get("context_slot", [])
    if context_slot is not None:
        if not isinstance(context_slot, list):
            raise ParamsMissingOrInvalid()
        for item in context_slot:
            if not isinstance(item, dict):
                raise ParamsMissingOrInvalid()
            if "id" not in item or not isinstance(item.get("id"), int):
                raise ParamsMissingOrInvalid()
            if "key" not in item or not isinstance(item.get("key"), str):
                raise ParamsMissingOrInvalid()
    # context (node-level) should be an object/dict
    context = d.get("context", {})
    if context is not None and not isinstance(context, dict):
        raise ParamsMissingOrInvalid()
    # listen
    listen = d.get("listen", [])
    if listen is not None and (not isinstance(listen, list) or not all(isinstance(i, int) for i in listen)):
        raise ListenMissingOrInvalid()
    return True

#校验workflow python dict
def is_valid_workflow_dict(d: Any) -> bool:
    """针对已解析的 Python dict 做 workflow 结构校验，校验失败时抛出 `WorkflowDictValidationError`。"""
    if not isinstance(d, dict):
        raise PayloadNotADict()
    if "workflow_id" not in d or not isinstance(d["workflow_id"], str) or len(d["workflow_id"]) == 0:
        raise WorkflowIDMissingOrInvalid()
    if "entry" not in d or not isinstance(d["entry"], int):
        raise EntryMissingOrInvalid()
    nodes = d.get("nodes", None)
    if not isinstance(nodes, list) or len(nodes) < 1:
        raise NodesMissingOrInvalid()
    for n in nodes:
        if not isinstance(n, dict):
            raise EachNodeMustBeObject()
        if "id" not in n or not isinstance(n.get("id"), int):
            raise NodeIDMustBeInteger()
        if "type" not in n or not isinstance(n.get("type"), str):
            raise NodeTypeMustBeString()
        # reuse node dict checks for node-like fields
        try:
            is_valid_node_dict({
                "type": n.get("type"),
                "inputs": n.get("inputs", []),
                "outputs": n.get("outputs", []),
                "params": n.get("params", {}),
                "listen": n.get("listen", []),
                "context": n.get("context", {}),
            })
        except NodeDictValidationError as nde:
            raise nde
    return True

