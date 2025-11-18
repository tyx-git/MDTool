"""
资源路径模块
负责资源文件路径解析，支持开发环境和打包环境
"""
import os
import sys
from pathlib import Path


def _get_base_path():
    """获取应用程序基础路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境（PyInstaller）
        return Path(sys.executable).parent
    else:
        # 开发环境
        return Path(__file__).parent.parent


BASE_PATH = _get_base_path()


def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件的绝对路径
    
    Args:
        relative_path: 相对于项目根目录的相对路径
        
    Returns:
        资源文件的绝对路径
    """
    return BASE_PATH / relative_path


def get_assets_dir() -> Path:
    """获取assets目录路径"""
    return get_resource_path('assets')


def get_config_dir() -> Path:
    """获取config目录路径（Windows AppData）"""
    if sys.platform == 'win32':
        appdata = os.getenv('APPDATA')
        if appdata:
            config_dir = Path(appdata) / 'MarkdownReader' / 'config'
            config_dir.mkdir(parents=True, exist_ok=True)
            return config_dir
    # 非Windows系统或无法获取AppData时，使用项目目录
    return get_resource_path('config')


def get_logs_dir() -> Path:
    """获取logs目录路径"""
    logs_dir = get_resource_path('logs')
    logs_dir.mkdir(exist_ok=True)
    return logs_dir
