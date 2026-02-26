"""
工作流核心处理模块 - 基于流程图实现
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
from ..logging import get_logger, log_workflow_cycle_error, log_workflow_attr_error

logger = get_logger()

class WorkflowProcessor:
    """工作流处理器 - 实现FlowSmith核心逻辑"""
    
    def __init__(self, max_retry: int = 3):
        self.max_retry = max_retry
        self.llm_handler = LLMHandler()
        self.validator = ProtocolValidator()
        self.detector = CycleDetector()
        
    async def process(self, user_query: str) -> Dict[str, Any]:
        """
        处理用户输入，生成工作流
        对应流程图中的主流程
        """
        # 1. 加载配置
        setup_prompt = self._load_file("config/setup_prompt.md")
        protocol_schema = self._load_json("config/protocol_for_work_schema.json")
        skill_plugins = self._load_json("config/skill_plugins_list.json")
        
        # 2. Fix-LLM阶段（带重试）
        workflow = None
        latest_context = None
        
        for attempt in range(self.max_retry):
            # 调用LLM生成工作流
            workflow = await self.llm_handler.generate(
                user_query=user_query,
                setup_prompt=setup_prompt,
                skill_plugins=skill_plugins,
                context=latest_context
            )
            
            # 验证工作流
            is_valid, advice = await self._validate_workflow(workflow, protocol_schema)
            
            if is_valid:
                logger.info("工作流验证通过", workflow_id=workflow.get("id"))
                break
            else:
                # 生成建议提示
                latest_context = self._generate_advice(advice, attempt)
                logger.warning(f"工作流验证失败，第{attempt+1}次重试", 
                             workflow_id=workflow.get("id"),
                             advice=advice)
        else:
            # 超过最大重试次数
            logger.error("工作流生成失败，超过最大重试次数", 
                        user_query=user_query[:100])
            raise Exception("工作流生成失败")
        
        # 3. 输出最终结果
        return workflow
    
    async def _validate_workflow(self, workflow: Dict, schema: Dict) -> tuple:
        """
        工作流验证 - 包含Protocol格式验证和环路检测
        """
        # 格式验证
        format_valid, format_advice = self.validator.validate(workflow, schema)
        if not format_valid:
            log_workflow_attr_error(
                workflow_id=workflow.get("id", "unknown"),
                attr_name="format",
                reason=format_advice
            )
            return False, format_advice
        
        # 环路检测
        acyclic, cycle_advice = self.detector.detect(workflow)
        if not acyclic:
            log_workflow_cycle_error(
                workflow_id=workflow.get("id", "unknown"),
                cycle_nodes=cycle_advice.get("cycles", [])
            )
            return False, cycle_advice.get("message", "检测到环路")
        
        return True, None
    
    def _load_file(self, path: str) -> str:
        """加载文本文件"""
        with open(Path(__file__).parent.parent / path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_json(self, path: str) -> Dict:
        """加载JSON文件"""
        with open(Path(__file__).parent.parent / path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _generate_advice(self, advice: str, attempt: int) -> str:
        """生成建议提示"""
        return f"第{attempt+1}次尝试失败，建议：{advice}"
