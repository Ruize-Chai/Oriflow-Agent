from typing import Any, Dict

import requests

from core.json_util import validate_workflow


def post_workflow(url: str, data: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
	"""
	发送workflow数据包消息
	"""
	validate_workflow(data, raise_on_error=True)
	response = requests.post(url, json=data, timeout=timeout)
	response.raise_for_status()
	return response.json()


def fetch_workflow(url: str, workflow_id: str, timeout: float = 10.0) -> Dict[str, Any]:
	"""
	接受workflow数据包消息
	"""
	response = requests.get(f"{url.rstrip('/')}/{workflow_id}", timeout=timeout)
	response.raise_for_status()
	return response.json()