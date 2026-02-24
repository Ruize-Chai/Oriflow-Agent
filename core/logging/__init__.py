"""
===============================================================================
工作流引擎日志模块 - 统一暴露接口
===============================================================================

本模块提供统一的日志访问接口，供整个项目调用。
使用方法：
    from core.logging import get_logger, Logger, log_error, catch_error
    
    # 获取日志实例
    logger = get_logger()
    logger.info("工作流启动")
    
    # 使用装饰器自动捕获异常
    @catch_error()
    def my_function():
        pass

版本: 2.0.0
作者: 智创未来团队
日期: 2026-02-24
===============================================================================
"""

import functools
import sys
from typing import Optional, Dict, Any, Callable, TypeVar, Union, Tuple
from pathlib import Path

# =============================================================================
# 从实现模块导入所有需要暴露的类和函数
# =============================================================================

# 导入主日志类
from .logger import Logger as _Logger

# 导入错误类和枚举
from .logger import (
    # 错误类
    WorkflowError,
    NetworkError,
    ConfigError,
    UserMistakeError,
    SkillError,
    
    # 枚举
    ErrorAction,
    ErrorLevel,
    
    # 工具函数
    get_logger as _get_logger_impl,
)

# =============================================================================
# 重新导出核心类和函数（定义__all__）
# =============================================================================

__all__ = [
    # 核心类
    'Logger',
    'WorkflowError',
    'NetworkError',
    'ConfigError',
    'UserMistakeError',
    'SkillError',
    
    # 枚举
    'ErrorAction',
    'ErrorLevel',
    
    # 主要函数
    'get_logger',
    'log_error',
    'catch_error',
    'with_logging',
    
    # 便捷函数
    'info',
    'error',
    'warning',
    'debug',
    'fatal',
]

# =============================================================================
# 类型变量
# =============================================================================

F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

# =============================================================================
# 单例管理
# =============================================================================

# 全局默认日志实例
_default_logger_instance = None
_default_logger_config = {
    'log_dir': 'logs',
    'app_name': 'workflow_engine',
    'error_codes_path': 'config/error_lists.json'
}

class Logger:
    """
    日志类 - 对外统一包装
    
    这是一个包装类，提供与底层实现相同的方法签名，
    但支持单例模式和懒加载。
    """
    
    def __init__(self, log_dir: Optional[str] = None, 
                 app_name: Optional[str] = None,
                 error_codes_path: Optional[str] = None):
        """
        初始化日志实例
        
        Args:
            log_dir: 日志目录路径
            app_name: 应用名称
            error_codes_path: 错误码表路径
        """
        self._log_dir = log_dir or _default_logger_config['log_dir']
        self._app_name = app_name or _default_logger_config['app_name']
        self._error_codes_path = error_codes_path or _default_logger_config['error_codes_path']
        self._logger = None
    
    def _get_impl(self) -> _Logger:
        """获取或创建底层实现（懒加载）"""
        if self._logger is None:
            self._logger = _Logger(
                log_dir=self._log_dir,
                app_name=self._app_name,
                error_codes_path=self._error_codes_path
            )
        return self._logger
    
    # =========================================================================
    # 日志方法代理
    # =========================================================================
    
    def info(self, message: str, code: str = "6001", **kwargs):
        """记录信息日志"""
        self._get_impl().info(message, code=code, **kwargs)
    
    def warning(self, message: str, code: str = "5001", **kwargs):
        """记录警告日志"""
        self._get_impl().warning(message, code=code, **kwargs)
    
    def error(self, message: str, code: str = "3001", **kwargs):
        """记录错误日志"""
        self._get_impl().error(message, code=code, **kwargs)
    
    def debug(self, message: str, code: str = "7001", **kwargs):
        """记录调试日志"""
        self._get_impl().debug(message, code=code, **kwargs)
    
    def fatal(self, message: str, code: str = "1001", **kwargs):
        """记录致命错误日志"""
        self._get_impl().fatal(message, code=code, **kwargs)
    
    def retryable(self, message: str, code: str = "4001", **kwargs):
        """记录可重试错误"""
        self._get_impl().retryable(message, code=code, **kwargs)
    
    def ignorable(self, message: str, code: str = "8001", **kwargs):
        """记录可忽略错误"""
        self._get_impl().ignorable(message, code=code, **kwargs)
    
    def log(self, level: str, message: str, code: Optional[str] = None, **kwargs):
        """通用日志方法"""
        self._get_impl().log(level, message, code=code, **kwargs)
    
    def handle_error(self, error: WorkflowError):
        """处理工作流错误"""
        return self._get_impl().handle_error(error)
    
    # =========================================================================
    # 属性访问
    # =========================================================================
    
    @property
    def log_file(self) -> Path:
        """获取当前日志文件路径"""
        return self._get_impl().log_file
    
    @property
    def recovery(self):
        """获取错误恢复管理器"""
        return self._get_impl().recovery
    
    def __repr__(self) -> str:
        return f"<Logger app={self._app_name} file={self.log_file.name}>"


# =============================================================================
# 全局函数接口
# =============================================================================

def get_logger(log_dir: Optional[str] = None,
               app_name: Optional[str] = None,
               error_codes_path: Optional[str] = None) -> Logger:
    """
    获取日志实例（单例模式）
    
    这是项目中最主要的日志获取方式，建议在所有模块中使用。
    
    Args:
        log_dir: 日志目录（可选，第一次调用后设置将无效）
        app_name: 应用名称（可选，第一次调用后设置将无效）
        error_codes_path: 错误码表路径（可选，第一次调用后设置将无效）
    
    Returns:
        Logger: 日志实例
    
    Examples:
        >>> from core.logging import get_logger
        >>> logger = get_logger()
        >>> logger.info("服务启动")
    """
    global _default_logger_instance, _default_logger_config
    
    # 更新配置（仅当实例还未创建时）
    if _default_logger_instance is None:
        if log_dir:
            _default_logger_config['log_dir'] = log_dir
        if app_name:
            _default_logger_config['app_name'] = app_name
        if error_codes_path:
            _default_logger_config['error_codes_path'] = error_codes_path
        
        _default_logger_instance = Logger(
            log_dir=_default_logger_config['log_dir'],
            app_name=_default_logger_config['app_name'],
            error_codes_path=_default_logger_config['error_codes_path']
        )
    
    return _default_logger_instance


def log_error(func: F = None, *, 
              code: str = "3000", 
              level: str = "ERROR",
              reraise: bool = True,
              default_return: Any = None) -> F:
    """
    函数装饰器：自动记录函数执行过程中的错误
    
    Args:
        func: 被装饰的函数
        code: 错误码
        level: 错误级别
        reraise: 是否重新抛出异常
        default_return: 发生错误时的默认返回值
    
    Returns:
        装饰后的函数
    
    Examples:
        >>> @log_error(code="3001", default_return=[])
        >>> def fetch_data():
        >>>     return 1 / 0  # 会触发错误，但返回 []
    """
    def decorator(f: F) -> F:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # 记录错误
                func_name = f.__name__
                module_name = f.__module__
                logger.log(
                    level=level,
                    message=f"函数 {module_name}.{func_name} 执行失败: {str(e)}",
                    code=code,
                    error=e,
                    func=func_name,
                    module=module_name,
                    args=str(args)[:100],
                    kwargs=str(kwargs)[:100]
                )
                
                if reraise:
                    raise
                return default_return
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


def catch_error(error_types: Union[type, Tuple[type, ...]] = Exception,
                code: str = "3000",
                level: str = "ERROR",
                fallback: Optional[Callable] = None) -> Callable:
    """
    更细粒度的异常捕获装饰器
    
    Args:
        error_types: 要捕获的异常类型
        code: 错误码
        level: 错误级别
        fallback: 错误发生后的回退函数
    
    Returns:
        装饰器
    
    Examples:
        >>> @catch_error(error_types=(ValueError, KeyError), 
        ...              code="4001", level="RETRY")
        >>> def process_input(data):
        >>>     return data['required_field']
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            try:
                return func(*args, **kwargs)
            except error_types as e:
                # 记录错误
                logger.log(
                    level=level,
                    message=f"{func.__name__} 捕获到异常: {str(e)}",
                    code=code,
                    error=e,
                    error_type=type(e).__name__
                )
                
                # 执行回退函数
                if fallback:
                    return fallback(*args, **kwargs)
                
                # 根据错误级别决定是否重新抛出
                error_level = ErrorLevel.from_code(code)
                if not error_level.recoverable:
                    raise
                
                return None
        return wrapper
    return decorator


def with_logging(level: str = "INFO", code: str = "6001") -> Callable:
    """
    函数执行日志装饰器（记录开始和结束）
    
    Args:
        level: 日志级别
        code: 错误码
    
    Returns:
        装饰器
    
    Examples:
        >>> @with_logging(level="DEBUG")
        >>> def long_running_task():
        >>>     time.sleep(1)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            import time
            
            start_time = time.time()
            logger.log(level, f"开始执行 {func.__name__}", 
                      code=code, state="start")
            
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                logger.log(level, f"完成执行 {func.__name__}", 
                          code=code, state="end", elapsed_ms=f"{elapsed:.2f}")
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.log("ERROR", f"执行失败 {func.__name__}: {str(e)}",
                          code="3000", state="error", elapsed_ms=f"{elapsed:.2f}")
                raise
        return wrapper
    return decorator


# =============================================================================
# 便捷函数（直接调用全局实例）
# =============================================================================

def info(message: str, code: str = "6001", **kwargs):
    """全局信息日志函数"""
    get_logger().info(message, code=code, **kwargs)

def error(message: str, code: str = "3001", **kwargs):
    """全局错误日志函数"""
    get_logger().error(message, code=code, **kwargs)

def warning(message: str, code: str = "5001", **kwargs):
    """全局警告日志函数"""
    get_logger().warning(message, code=code, **kwargs)

def debug(message: str, code: str = "7001", **kwargs):
    """全局调试日志函数"""
    get_logger().debug(message, code=code, **kwargs)

def fatal(message: str, code: str = "1001", **kwargs):
    """全局致命错误日志函数"""
    get_logger().fatal(message, code=code, **kwargs)

def retryable(message: str, code: str = "4001", **kwargs):
    """全局可重试错误函数"""
    get_logger().retryable(message, code=code, **kwargs)

def ignorable(message: str, code: str = "8001", **kwargs):
    """全局可忽略错误函数"""
    get_logger().ignorable(message, code=code, **kwargs)


# =============================================================================
# 初始化检查
# =============================================================================

# 确保错误码文件存在
def ensure_error_codes():
    """确保错误码文件存在"""
    import os
    from pathlib import Path
    
    config_path = Path(_default_logger_config['error_codes_path'])
    if not config_path.exists():
        # 创建默认错误码文件
        config_path.parent.mkdir(parents=True, exist_ok=True)
        default_codes = {
            "version": "2.0",
            "categories": {
                "INFO": {"name": "提示信息", "action": "ignore", "recoverable": True},
                "ERROR": {"name": "一般错误", "action": "prompt", "recoverable": True}
            },
            "errors": {
                "6001": {"category": "INFO", "message": "操作成功完成"},
                "3001": {"category": "ERROR", "message": "操作失败", "suggestion": "请重试"}
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(default_codes, f, ensure_ascii=False, indent=2)

# 执行初始化检查
ensure_error_codes()


# =============================================================================
# 便捷导入
# =============================================================================

# 导出常用的错误类型别名
ValidationError = UserMistakeError  # 输入验证错误
TimeoutError = NetworkError         # 超时错误
ResourceError = SkillError          # 资源错误
