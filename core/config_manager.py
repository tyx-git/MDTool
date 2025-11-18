"""
配置管理模块
负责应用程序配置的读取、保存和管理
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from .resource_path import get_config_dir
from .logger_util import get_logger, log_error


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_file = get_config_dir() / 'app.json'
        self._config: Dict[str, Any] = {}
        self._logger = get_logger(__name__)
        self._load()
    
    def _normalize_path(self, file_path: Optional[str]) -> Optional[str]:
        """统一路径格式（使用绝对路径和正斜杠）"""
        if not file_path:
            return file_path
        try:
            path = Path(file_path).expanduser().resolve(strict=False)
            return path.as_posix()
        except Exception:
            # 如果标准化失败，退回原始字符串
            return str(file_path)
    
    def _load(self):
        """从文件加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                log_error("加载配置失败", e, self._logger)
                self._config = {}
        else:
            self._config = {}
        
        # 设置默认值
        self._set_defaults()
    
    def _set_defaults(self):
        """设置默认配置值"""
        defaults = {
            'window': {
                'x': 100,
                'y': 100,
                'width': 1200,
                'height': 800,
                'splitter_position': 300,
                'maximized': False  # 窗口是否最大化
            },
            'theme': 'auto',
            'font': {
                'body_size': 16,
                'code_size': 14,
                'code_family': 'Consolas, Monaco, "Courier New", monospace',
                'code_weight': 'normal',  # normal, bold
                'code_inline_color': None,  # None表示使用主题默认颜色
                'code_block_color': None
            },
            'recent_files': [],
            'recent_dirs': [],
            'marked_files': {},
            'expanded_paths': {},  # 每个根目录的展开路径列表
            'file_scroll_positions': {},  # 文件滚动位置
            'last_file': None,  # 最后打开的文件
            'last_dir': None  # 最后打开的目录
        }
        
        # 合并默认值
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in self._config[key]:
                        self._config[key][sub_key] = sub_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键，支持点号分隔（如 'window.width'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键，支持点号分隔（如 'window.width'）
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 创建嵌套字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            log_error("保存配置失败", e, self._logger)
    
    def get_window_config(self) -> Dict[str, Any]:
        """获取窗口配置"""
        return {
            'x': self.get('window.x', 100),
            'y': self.get('window.y', 100),
            'width': self.get('window.width', 1200),
            'height': self.get('window.height', 800),
            'maximized': self.get('window.maximized', False)
        }
    
    def set_window_config(self, x: int, y: int, width: int, height: int, maximized: bool = False):
        """设置窗口配置"""
        self.set('window.x', x)
        self.set('window.y', y)
        self.set('window.width', width)
        self.set('window.height', height)
        self.set('window.maximized', maximized)
    
    def get_window_maximized(self) -> bool:
        """获取窗口是否最大化"""
        return self.get('window.maximized', False)
    
    def set_window_maximized(self, maximized: bool):
        """设置窗口是否最大化"""
        self.set('window.maximized', maximized)
    
    def get_splitter_position(self) -> int:
        """获取分割器位置"""
        return self.get('window.splitter_position', 300)
    
    def set_splitter_position(self, position: int):
        """设置分割器位置"""
        self.set('window.splitter_position', position)
    
    def get_file_mark(self, file_path: str) -> Optional[str]:
        """
        获取文件标记
        
        Args:
            file_path: 文件路径
            
        Returns:
            标记类型（'green'/'red'）或None
        """
        marked_files = self.get('marked_files', {})
        # 确保marked_files是字典类型
        if not isinstance(marked_files, dict):
            marked_files = {}
            self.set('marked_files', marked_files)
        
        normalized_path = self._normalize_path(file_path)
        mark = marked_files.get(normalized_path)
        
        # 兼容旧版本：如果旧格式存在，迁移到新key
        if mark is None and normalized_path and normalized_path != file_path:
            legacy_mark = marked_files.get(file_path)
            if legacy_mark is not None:
                marked_files.pop(file_path, None)
                marked_files[normalized_path] = legacy_mark
                self.set('marked_files', marked_files)
                mark = legacy_mark
        
        return mark
    
    def set_file_mark(self, file_path: str, mark_type: Optional[str]):
        """
        设置文件标记
        
        Args:
            file_path: 文件路径
            mark_type: 标记类型（'green'/'red'）或None（取消标记）
        """
        marked_files = self.get('marked_files', {})
        # 确保marked_files是字典类型
        if not isinstance(marked_files, dict):
            marked_files = {}
        
        normalized_path = self._normalize_path(file_path)
        target_key = normalized_path or file_path
        
        if mark_type:
            marked_files[target_key] = mark_type
            # 移除旧格式key，避免重复
            if target_key != file_path:
                marked_files.pop(file_path, None)
        else:
            marked_files.pop(target_key, None)
            if target_key != file_path:
                marked_files.pop(file_path, None)
        
        self.set('marked_files', marked_files)
    
    def add_recent_file(self, file_path: str, max_count: int = 10):
        """
        添加最近文件
        
        Args:
            file_path: 文件路径
            max_count: 最大保存数量
        """
        # 获取实际列表（确保是配置中的列表，不是默认值）
        recent_files = self._config.get('recent_files', [])
        if not isinstance(recent_files, list):
            recent_files = []
        
        # 移除已存在的
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # 添加到开头
        recent_files.insert(0, file_path)
        
        # 限制数量
        recent_files = recent_files[:max_count]
        
        self.set('recent_files', recent_files)
    
    def get_recent_files(self) -> List[str]:
        """获取最近文件列表"""
        return self.get('recent_files', [])
    
    def add_recent_dir(self, dir_path: str, max_count: int = 10):
        """
        添加最近目录
        
        Args:
            dir_path: 目录路径
            max_count: 最大保存数量
        """
        # 获取实际列表（确保是配置中的列表，不是默认值）
        recent_dirs = self._config.get('recent_dirs', [])
        if not isinstance(recent_dirs, list):
            recent_dirs = []
        
        # 移除已存在的
        if dir_path in recent_dirs:
            recent_dirs.remove(dir_path)
        
        # 添加到开头
        recent_dirs.insert(0, dir_path)
        
        # 限制数量
        recent_dirs = recent_dirs[:max_count]
        
        self.set('recent_dirs', recent_dirs)
    
    def get_recent_dirs(self) -> List[str]:
        """获取最近目录列表"""
        return self.get('recent_dirs', [])
    
    def get_expanded_paths(self, root_path: str) -> List[str]:
        """
        获取指定根目录的展开路径列表
        
        Args:
            root_path: 根目录路径
            
        Returns:
            展开路径列表
        """
        expanded_paths = self.get('expanded_paths', {})
        if not isinstance(expanded_paths, dict):
            expanded_paths = {}
        return expanded_paths.get(root_path, [])
    
    def set_expanded_paths(self, root_path: str, paths: List[str]):
        """
        设置指定根目录的展开路径列表
        
        Args:
            root_path: 根目录路径
            paths: 展开路径列表
        """
        expanded_paths = self.get('expanded_paths', {})
        if not isinstance(expanded_paths, dict):
            expanded_paths = {}
        expanded_paths[root_path] = paths
        self.set('expanded_paths', expanded_paths)
    
    def get_file_scroll_position(self, file_path: str) -> int:
        """
        获取文件的滚动位置
        
        Args:
            file_path: 文件路径
            
        Returns:
            滚动位置（像素）
        """
        scroll_positions = self.get('file_scroll_positions', {})
        if not isinstance(scroll_positions, dict):
            scroll_positions = {}
        return scroll_positions.get(file_path, 0)
    
    def set_file_scroll_position(self, file_path: str, position: int):
        """
        设置文件的滚动位置
        
        Args:
            file_path: 文件路径
            position: 滚动位置（像素）
        """
        scroll_positions = self.get('file_scroll_positions', {})
        if not isinstance(scroll_positions, dict):
            scroll_positions = {}
        scroll_positions[file_path] = position
        self.set('file_scroll_positions', scroll_positions)
    
    def get_last_file(self) -> Optional[str]:
        """获取最后打开的文件"""
        return self.get('last_file')
    
    def set_last_file(self, file_path: str):
        """设置最后打开的文件"""
        self.set('last_file', file_path)
    
    def get_last_dir(self) -> Optional[str]:
        """获取最后打开的目录"""
        return self.get('last_dir')
    
    def set_last_dir(self, dir_path: str):
        """设置最后打开的目录"""
        self.set('last_dir', dir_path)
