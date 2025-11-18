"""
Windows集成模块
提供Windows系统功能集成，包括主题检测和任务栏功能
"""
import sys
from time import time
from typing import Optional
from .logger_util import get_logger, log_error

try:
    import winreg
    from PyQt5.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False


class WindowsIntegration:
    """Windows系统集成"""
    _theme_cache_value: Optional[str] = None
    _theme_cache_expire: float = 0.0
    _theme_cache_ttl: float = 2.0  # 秒
    
    def __init__(self, window):
        """
        初始化Windows集成
        
        Args:
            window: QMainWindow实例
        """
        self.window = window
        self.taskbar_button: Optional[QWinTaskbarButton] = None
        self.taskbar_progress: Optional[QWinTaskbarProgress] = None
        self._initialized = False
        self._logger = get_logger(__name__)
    
    def initialize(self):
        """延迟初始化（需要在窗口显示后调用）"""
        if not WINDOWS_AVAILABLE or sys.platform != 'win32':
            return
        
        if self._initialized:
            return
        
        try:
            # 确保窗口已经显示并且有有效的窗口句柄
            if not self.window.isVisible():
                return
            
            window_handle = self.window.windowHandle()
            if window_handle:
                # 检查窗口句柄是否有效（使用try-except而不是isValid方法）
                try:
                    self.taskbar_button = QWinTaskbarButton()
                    self.taskbar_button.setWindow(window_handle)
                    self.taskbar_progress = self.taskbar_button.progress()
                    self._initialized = True
                except Exception:
                    # 如果设置失败，说明窗口句柄无效
                    pass
        except Exception as e:
            # Windows集成失败不影响程序运行，只记录日志
            self._logger.debug(f"Windows集成初始化失败: {e}")
    
    @classmethod
    def _read_system_theme(cls) -> str:
        """直接从系统读取主题（无缓存）"""
        if not WINDOWS_AVAILABLE or sys.platform != 'win32':
            return 'light'
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            )
            try:
                value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
                return 'dark' if value == 0 else 'light'
            finally:
                winreg.CloseKey(key)
        except (OSError, FileNotFoundError):
            return 'light'
    
    @classmethod
    def get_system_theme(cls) -> str:
        """
        获取系统主题
        
        Returns:
            'light' 或 'dark'
        """
        now = time()
        if cls._theme_cache_value and now < cls._theme_cache_expire:
            return cls._theme_cache_value
        
        theme = cls._read_system_theme()
        cls._theme_cache_value = theme
        cls._theme_cache_expire = now + cls._theme_cache_ttl
        return theme
    
    @classmethod
    def is_dark_theme(cls) -> bool:
        """
        检测Windows是否为深色主题
        """
        return cls.get_system_theme() == 'dark'
    
    def set_progress(self, value: int, maximum: int = 100):
        """
        设置任务栏进度
        
        Args:
            value: 当前进度值
            maximum: 最大值
        """
        if not self._initialized:
            self.initialize()
        
        if self.taskbar_progress:
            try:
                self.taskbar_progress.setRange(0, maximum)
                self.taskbar_progress.setValue(value)
                self.taskbar_progress.setVisible(True)
            except Exception as e:
                log_error("设置任务栏进度失败", e, self._logger)
    
    def hide_progress(self):
        """隐藏任务栏进度"""
        if self.taskbar_progress:
            try:
                self.taskbar_progress.setVisible(False)
            except Exception as e:
                log_error("隐藏任务栏进度失败", e, self._logger)
