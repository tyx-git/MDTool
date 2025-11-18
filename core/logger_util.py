"""
日志工具模块
提供统一的日志接口，同时支持print和logging
"""
import logging
import sys


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（通常是模块名）
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name or __name__)


def log_error(message: str, exception: Exception = None, logger: logging.Logger = None):
    """
    记录错误（同时输出到print和日志）
    
    Args:
        message: 错误消息
        exception: 异常对象（可选）
        logger: 日志记录器（可选，默认使用调用模块的logger）
    """
    if logger is None:
        logger = get_logger()
    
    error_msg = f"{message}"
    if exception:
        error_msg += f": {exception}"
    
    # 同时使用print和logging
    print(error_msg, file=sys.stderr)
    logger.error(error_msg, exc_info=exception)


def log_warning(message: str, logger: logging.Logger = None):
    """
    记录警告（同时输出到print和日志）
    
    Args:
        message: 警告消息
        logger: 日志记录器（可选）
    """
    if logger is None:
        logger = get_logger()
    
    # 同时使用print和logging
    print(f"警告: {message}")
    logger.warning(message)


def log_info(message: str, logger: logging.Logger = None):
    """
    记录信息（同时输出到print和日志）
    
    Args:
        message: 信息消息
        logger: 日志记录器（可选）
    """
    if logger is None:
        logger = get_logger()
    
    # 同时使用print和logging
    print(message)
    logger.info(message)


def log_debug(message: str, logger: logging.Logger = None):
    """
    记录调试信息（仅输出到日志，不print）
    
    Args:
        message: 调试消息
        logger: 日志记录器（可选）
    """
    if logger is None:
        logger = get_logger()
    
    logger.debug(message)

