"""
主窗口模块
提供主窗口UI和功能协调
"""
from pathlib import Path
from time import perf_counter
from typing import Dict, Optional, Tuple
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QLabel, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from .config_manager import ConfigManager
from .markdown_renderer import MarkdownRenderer
from .file_tree import FileTree
from .windows_integration import WindowsIntegration
from .settings_dialog import SettingsDialog
from .resource_path import get_resource_path
from .logger_util import get_logger, log_error

_STYLESHEET_CACHE: Dict[str, Tuple[float, str]] = {}


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, config_manager: ConfigManager = None):
        super().__init__()
        
        self._logger = get_logger(__name__)
        
        # 初始化组件（优先使用传入的配置管理器，避免重复加载）
        if config_manager:
            self.config_manager = config_manager
        else:
            self.config_manager = ConfigManager()
        
        # 先加载配置，用于初始化窗口
        window_config = self.config_manager.get_window_config()
        
        # 使用配置初始化窗口（在显示前设置，避免闪烁）
        if not window_config.get('maximized', False):
            self.resize(window_config['width'], window_config['height'])
            self.move(window_config['x'], window_config['y'])
        
        # 初始化其他组件（延迟初始化非关键组件）
        self.markdown_renderer: Optional[MarkdownRenderer] = None
        self.windows_integration: Optional[WindowsIntegration] = None
        self.web_view: Optional[QWebEngineView] = None
        self.preview_placeholder: Optional[QLabel] = None
        self.file_tree: Optional[FileTree] = None
        self.current_file: Optional[Path] = None
        
        # 防抖定时器
        self.splitter_save_timer = QTimer()
        self.splitter_save_timer.setSingleShot(True)
        self.splitter_save_timer.timeout.connect(self._save_splitter_position)
        
        # 初始化UI（此时窗口大小和位置已设置）
        ui_begin = perf_counter()
        self._init_ui()
        self._logger.debug(
            "启动诊断: 主窗口UI初始化耗时 %.1f ms",
            (perf_counter() - ui_begin) * 1000,
        )
        self._apply_theme()
        
        # 设置窗口标题
        self.setWindowTitle('Markdown Reader')
    
    def _init_ui(self):
        """初始化用户界面"""
        init_begin = perf_counter()
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)
        
        # 创建文件树
        tree_begin = perf_counter()
        self.file_tree = FileTree(self.config_manager, self)
        self._logger.debug(
            "启动诊断: FileTree 初始化耗时 %.1f ms",
            (perf_counter() - tree_begin) * 1000,
        )
        self.file_tree.file_selected.connect(self._on_file_selected)
        self.splitter.addWidget(self.file_tree)
        
        # 预览占位符（WebView改为延迟初始化）
        self.preview_placeholder = QLabel('正在准备预览区域…')
        self.preview_placeholder.setAlignment(Qt.AlignCenter)
        self.preview_placeholder.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 14px;
            }
        """)
        self.splitter.addWidget(self.preview_placeholder)
        
        # 设置分割器比例
        self.splitter.setStretchFactor(0, 0)  # 文件树不拉伸
        self.splitter.setStretchFactor(1, 1)  # 预览区域拉伸
        
        # 连接分割器信号
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建状态栏
        self._create_status_bar()
        
        # 加载样式表
        stylesheet_begin = perf_counter()
        self._load_stylesheet()
        self._logger.debug(
            "启动诊断: 样式表加载耗时 %.1f ms",
            (perf_counter() - stylesheet_begin) * 1000,
        )
        
        # 延迟显示欢迎页面（避免阻塞UI初始化）
        QTimer.singleShot(50, self._show_welcome_page)
        self._logger.debug(
            "启动诊断: _init_ui 总耗时 %.1f ms",
            (perf_counter() - init_begin) * 1000,
        )
        
        # 延迟加载配置内容
        QTimer.singleShot(50, self._load_config)

    def _ensure_web_view(self) -> QWebEngineView:
        """确保WebView已创建，必要时延迟初始化"""
        if self.web_view:
            return self.web_view

        webview_begin = perf_counter()
        self.web_view = QWebEngineView()

        if self.preview_placeholder:
            placeholder_index = self.splitter.indexOf(self.preview_placeholder)
            if placeholder_index != -1:
                self.splitter.replaceWidget(placeholder_index, self.web_view)
            else:
                self.splitter.addWidget(self.web_view)
            self.preview_placeholder.deleteLater()
            self.preview_placeholder = None
        else:
            self.splitter.addWidget(self.web_view)

        self.splitter.setStretchFactor(1, 1)
        self._logger.debug(
            "启动诊断: QWebEngineView 延迟初始化耗时 %.1f ms",
            (perf_counter() - webview_begin) * 1000,
        )
        return self.web_view

    def _get_markdown_renderer(self) -> MarkdownRenderer:
        """延迟创建Markdown渲染器"""
        if self.markdown_renderer is None:
            renderer_begin = perf_counter()
            self.markdown_renderer = MarkdownRenderer()
            self._logger.debug(
                "启动诊断: MarkdownRenderer 延迟初始化耗时 %.1f ms",
                (perf_counter() - renderer_begin) * 1000,
            )
        return self.markdown_renderer

    def _init_windows_integration(self):
        """延迟初始化Windows集成"""
        if self.windows_integration is None:
            init_begin = perf_counter()
            self.windows_integration = WindowsIntegration(self)
            self._logger.debug(
                "启动诊断: WindowsIntegration 延迟初始化耗时 %.1f ms",
                (perf_counter() - init_begin) * 1000,
            )
        if hasattr(self.windows_integration, 'initialize'):
            self.windows_integration.initialize()
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        file_menu.addAction('打开文件', self._open_file, 'Ctrl+O')
        file_menu.addAction('打开文件夹', self._open_folder, 'Ctrl+K')
        file_menu.addSeparator()
        file_menu.addAction('最近文件', self._show_recent_files)
        file_menu.addSeparator()
        file_menu.addAction('退出', self.close, 'Alt+F4')
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        view_menu.addAction('刷新', self._refresh_file_tree, 'F5')
        view_menu.addSeparator()
        
        theme_menu = view_menu.addMenu('主题')
        theme_menu.addAction('浅色', lambda: self._set_theme('light'))
        theme_menu.addAction('深色', lambda: self._set_theme('dark'))
        theme_menu.addAction('自动', lambda: self._set_theme('auto'))
        
        # 设置菜单
        settings_menu = menubar.addMenu('设置')
        settings_menu.addAction('设置', self._show_settings, 'Ctrl+,')
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        help_menu.addAction('关于', self._show_about)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_label = QLabel('就绪')
        self.status_bar.addWidget(self.status_label)
    
    def _load_stylesheet(self):
        """加载样式表"""
        stylesheet_file = get_resource_path('assets/styles.qss')
        if not stylesheet_file.exists():
            return
        
        cache_key = str(stylesheet_file)
        try:
            mtime = stylesheet_file.stat().st_mtime
        except OSError as e:
            log_error("读取样式表信息失败", e, self._logger)
            return
        
        cached_entry = _STYLESHEET_CACHE.get(cache_key)
        if cached_entry and cached_entry[0] == mtime:
            stylesheet = cached_entry[1]
        else:
            try:
                with open(stylesheet_file, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                _STYLESHEET_CACHE[cache_key] = (mtime, stylesheet)
            except IOError as e:
                log_error("加载样式表失败", e, self._logger)
                return
        
        self.setStyleSheet(stylesheet)
    
    def _show_welcome_page(self):
        """显示欢迎页面"""
        theme = self.config_manager.get('theme', 'auto')
        body_size = self.config_manager.get('font.body_size', 16)
        code_size = self.config_manager.get('font.code_size', 14)
        code_family = self.config_manager.get('font.code_family')
        code_weight = self.config_manager.get('font.code_weight', 'normal')
        code_inline_color = self.config_manager.get('font.code_inline_color')
        code_block_color = self.config_manager.get('font.code_block_color')
        
        # 根据主题选择颜色
        is_dark = (theme == 'dark' or (theme == 'auto' and WindowsIntegration.get_system_theme() == 'dark'))
        
        if is_dark:
            title_color = "#ffffff"
            subtitle_color = "#858585"
            text_color = "#d4d4d4"
            accent_color = "#4ec9b0"
            border_color = "#3e3e42"
            divider_color = "#3e3e42"
        else:
            title_color = "#24292e"
            subtitle_color = "#6a737d"
            text_color = "#24292e"
            accent_color = "#0366d6"
            border_color = "#e0e0e0"
            divider_color = "#e0e0e0"
        
        welcome_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: {'#1e1e1e' if is_dark else '#ffffff'};
        }}
        .welcome-container {{
            text-align: center;
            padding: 60px 40px;
            max-width: 600px;
            width: 100%;
        }}
        .title {{
            font-size: 3.5em;
            margin-bottom: 20px;
            font-weight: 300;
            letter-spacing: 3px;
            color: {title_color};
        }}
        .subtitle {{
            font-size: 1.3em;
            margin-bottom: 50px;
            font-style: italic;
            color: {subtitle_color};
        }}
        .developer {{
            color: {accent_color};
            font-weight: 500;
        }}
        .divider {{
            border: none;
            border-top: 2px solid {divider_color};
            margin: 50px auto;
            width: 120px;
        }}
        .description {{
            font-size: 1.15em;
            line-height: 1.8;
            color: {text_color};
            margin: 40px 0;
        }}
        .hint {{
            margin-top: 60px;
            padding-top: 30px;
            border-top: 1px solid {border_color};
        }}
        .hint-text {{
            font-size: 0.95em;
            color: {subtitle_color};
        }}
    </style>
</head>
<body>
    <div class="welcome-container">
        <h1 class="title">MarkDown 阅读器</h1>
        <p class="subtitle">由 <span class="developer">TTxzy</span> 开发</p>
        <hr class="divider">
        <p class="description">
            一个简洁优雅的 Markdown 阅读工具<br>
            专注于提供流畅的阅读体验
        </p>
        <div class="hint">
            <p class="hint-text">💡 提示：通过菜单 <strong>文件</strong> 打开文件夹或文件开始使用</p>
        </div>
    </div>
</body>
</html>"""
        
        # 直接使用HTML，不通过Markdown渲染
        html = welcome_html
        web_view = self._ensure_web_view()
        web_view.setHtml(html)
        self.current_file = None
        self.status_label.setText('就绪')
        self.setWindowTitle('Markdown Reader')
    
    def _load_config(self):
        """加载配置（延迟加载内容，窗口大小已在__init__中设置）"""
        # 加载分割器位置（在showEvent中设置）
        
        # 加载最后打开的目录或最近目录（延迟加载，避免阻塞启动）
        last_dir = self.config_manager.get_last_dir()
        if last_dir and Path(last_dir).exists():
            QTimer.singleShot(100, lambda: self._load_last_dir(last_dir))
        else:
            recent_dirs = self.config_manager.get_recent_dirs()
            if recent_dirs:
                QTimer.singleShot(100, lambda: self._load_last_dir(recent_dirs[0]))
        
        # 加载最后打开的文件（延迟加载）
        last_file = self.config_manager.get_last_file()
        if last_file and Path(last_file).exists():
            QTimer.singleShot(200, lambda: self._open_file_path(last_file))
    
    def _load_last_dir(self, dir_path: str):
        """加载目录"""
        self.file_tree.set_root_path(dir_path)
    
    def _save_config(self):
        """保存配置"""
        # 保存窗口配置
        geometry = self.geometry()
        is_maximized = self.isMaximized()
        self.config_manager.set_window_config(
            geometry.x(), geometry.y(),
            geometry.width(), geometry.height(),
            is_maximized
        )
        
        # 保存分割器位置
        self._save_splitter_position()
        
        # 保存配置
        self.config_manager.save()
    
    def changeEvent(self, event):
        """窗口状态改变事件（用于检测最大化/最小化）"""
        super().changeEvent(event)
        # 当窗口状态改变时，保存配置（防抖）
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.WindowStateChange:
            if hasattr(self, '_window_state_timer'):
                self._window_state_timer.stop()
            else:
                self._window_state_timer = QTimer()
                self._window_state_timer.setSingleShot(True)
                self._window_state_timer.timeout.connect(self._save_window_state)
            self._window_state_timer.start(300)
    
    def _save_window_state(self):
        """保存窗口状态"""
        geometry = self.geometry()
        is_maximized = self.isMaximized()
        self.config_manager.set_window_config(
            geometry.x(), geometry.y(),
            geometry.width(), geometry.height(),
            is_maximized
        )
        self.config_manager.save()
    
    def moveEvent(self, event):
        """窗口移动事件"""
        super().moveEvent(event)
        # 只有在非最大化状态下才保存位置
        if not self.isMaximized():
            if hasattr(self, '_move_timer'):
                self._move_timer.stop()
            else:
                self._move_timer = QTimer()
                self._move_timer.setSingleShot(True)
                self._move_timer.timeout.connect(self._save_window_position)
            self._move_timer.start(500)  # 500ms防抖
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 只有在非最大化状态下才保存大小
        if not self.isMaximized():
            if hasattr(self, '_resize_timer'):
                self._resize_timer.stop()
            else:
                self._resize_timer = QTimer()
                self._resize_timer.setSingleShot(True)
                self._resize_timer.timeout.connect(self._save_window_size)
            self._resize_timer.start(500)  # 500ms防抖
    
    def _save_window_position(self):
        """保存窗口位置"""
        if not self.isMaximized():
            geometry = self.geometry()
            self.config_manager.set_window_config(
                geometry.x(), geometry.y(),
                geometry.width(), geometry.height(),
                False
            )
            self.config_manager.save()
    
    def _save_window_size(self):
        """保存窗口大小"""
        if not self.isMaximized():
            geometry = self.geometry()
            self.config_manager.set_window_config(
                geometry.x(), geometry.y(),
                geometry.width(), geometry.height(),
                False
            )
            self.config_manager.save()
    
    def _save_splitter_position(self):
        """保存分割器位置"""
        sizes = self.splitter.sizes()
        if sizes[0] > 0:  # 确保文件树已初始化
            self.config_manager.set_splitter_position(sizes[0])
            self.config_manager.save()
    
    def _on_splitter_moved(self, pos: int, index: int):
        """分割器移动事件"""
        # 限制文件树最大宽度为总宽度的1/3
        total_width = self.splitter.width()
        max_tree_width = total_width // 3
        if pos > max_tree_width:
            self.splitter.setSizes([max_tree_width, total_width - max_tree_width])
        
        # 防抖保存
        self.splitter_save_timer.stop()
        self.splitter_save_timer.start(500)  # 500ms延迟
    
    def _open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '打开文件', '',
            'Markdown文件 (*.md *.markdown);;所有文件 (*.*)'
        )
        
        if file_path:
            self._open_file_path(file_path)
    
    def _open_folder(self):
        """打开文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, '打开文件夹', ''
        )
        
        if folder_path:
            self.file_tree.set_root_path(folder_path)
            self.config_manager.add_recent_dir(folder_path)
            self.config_manager.set_last_dir(folder_path)
            self.config_manager.save()
            self.status_label.setText(f'已打开文件夹: {folder_path}')
    
    def _open_file_path(self, file_path: str):
        """打开指定文件路径"""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            QMessageBox.warning(self, '错误', '文件不存在')
            return
        
        # 添加到最近文件并设置为最后打开的文件
        self.config_manager.add_recent_file(str(path))
        self.config_manager.set_last_file(str(path))
        
        # 设置文件树根路径（如果文件不在当前根路径下）
        if self.file_tree.root_path:
            try:
                path.relative_to(self.file_tree.root_path)
            except ValueError:
                # 文件不在当前根路径下，设置新的根路径
                self.file_tree.set_root_path(str(path.parent))
                self.config_manager.add_recent_dir(str(path.parent))
                self.config_manager.set_last_dir(str(path.parent))
        
        # 统一保存配置（避免重复保存）
        self.config_manager.save()
        
        # 选中文件
        self.file_tree.select_file(str(path))
        
        # 渲染文件
        self._render_file(path)
    
    def _on_file_selected(self, file_path: str):
        """文件选中事件"""
        self._render_file(Path(file_path))
    
    def _render_file(self, file_path: Path):
        """渲染Markdown文件"""
        self.current_file = file_path
        
        # 更新状态栏
        self.status_label.setText(f'正在加载: {file_path.name}')
        
        try:
            # 获取配置
            theme = self.config_manager.get('theme', 'auto')
            body_size = self.config_manager.get('font.body_size', 16)
            code_size = self.config_manager.get('font.code_size', 14)
            code_family = self.config_manager.get('font.code_family')
            code_weight = self.config_manager.get('font.code_weight', 'normal')
            code_inline_color = self.config_manager.get('font.code_inline_color')
            code_block_color = self.config_manager.get('font.code_block_color')
            
            # 获取保存的滚动位置
            saved_scroll = self.config_manager.get_file_scroll_position(str(file_path))
            
            # 渲染文件
            renderer = self._get_markdown_renderer()
            html = renderer.render_file(
                file_path, theme, body_size, code_size,
                code_family, code_weight, code_inline_color, code_block_color
            )
            
            # 如果有关闭前保存的滚动位置，在HTML中添加JavaScript来恢复
            if saved_scroll > 0:
                # 在HTML末尾添加恢复滚动位置的脚本
                scroll_script = f"""
                <script>
                    window.addEventListener('load', function() {{
                        window.scrollTo(0, {saved_scroll});
                    }});
                    document.addEventListener('DOMContentLoaded', function() {{
                        window.scrollTo(0, {saved_scroll});
                    }});
                </script>
                """
                html = html.replace('</body>', scroll_script + '</body>')
            
            # 显示HTML
            web_view = self._ensure_web_view()
            web_view.setHtml(html)
            
            # 延迟恢复滚动位置（确保页面已加载）
            if saved_scroll > 0:
                QTimer.singleShot(300, lambda: self._restore_scroll_position(str(file_path), saved_scroll))
            
            # 更新状态栏
            self.status_label.setText(f'已加载: {file_path.name}')
            self.setWindowTitle(f'{file_path.name} - Markdown Reader')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'渲染文件失败: {e}')
            self.status_label.setText('加载失败')
    
    def _restore_scroll_position(self, file_path: str, position: int):
        """恢复滚动位置"""
        if self.web_view:
            # 使用JavaScript恢复滚动位置
            self.web_view.page().runJavaScript(f'window.scrollTo(0, {position});')
    
    def _save_scroll_position(self):
        """保存当前文件的滚动位置"""
        if self.current_file and self.web_view:
            # 使用JavaScript获取滚动位置
            self.web_view.page().runJavaScript(
                'window.pageYOffset || document.documentElement.scrollTop',
                lambda pos: self._on_scroll_position_received(str(self.current_file), int(pos or 0))
            )
    
    def _on_scroll_position_received(self, file_path: str, position: int):
        """接收到滚动位置后的回调"""
        if position > 0:
            self.config_manager.set_file_scroll_position(file_path, position)
            self.config_manager.save()
    
    def _refresh_file_tree(self):
        """刷新文件树"""
        if self.file_tree:
            self.file_tree.refresh()
            self.status_label.setText('已刷新')
    
    def _set_theme(self, theme: str):
        """设置主题"""
        self.config_manager.set('theme', theme)
        self.config_manager.save()
        self._apply_theme()
        
        # 重新渲染当前文件或显示欢迎页面
        if self.current_file:
            self._render_file(self.current_file)
        else:
            self._show_welcome_page()
    
    def _apply_theme(self):
        """应用主题"""
        theme_begin = perf_counter()
        theme = self.config_manager.get('theme', 'auto')
        
        # 获取实际主题
        if theme == 'auto':
            actual_theme = WindowsIntegration.get_system_theme()
        else:
            actual_theme = theme
        
        is_dark = (actual_theme == 'dark')
        
        # 应用文件树主题
        if self.file_tree:
            self.file_tree.apply_theme(is_dark)
        
        # 设置窗口属性（用于样式表）
        if is_dark:
            self.setProperty('dark', True)
        else:
            self.setProperty('dark', False)
        
        # 重新加载样式表
        self._load_stylesheet()
        self.style().unpolish(self)
        self.style().polish(self)
        self._logger.debug(
            "启动诊断: 主题应用耗时 %.1f ms",
            (perf_counter() - theme_begin) * 1000,
        )
    
    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec_() == SettingsDialog.Accepted:
            # 重新应用主题
            self._apply_theme()
            
            # 重新渲染当前文件
            if self.current_file:
                self._render_file(self.current_file)
            else:
                self._show_welcome_page()
    
    def _show_recent_files(self):
        """显示最近文件菜单"""
        recent_files = self.config_manager.get_recent_files()
        if not recent_files:
            QMessageBox.information(self, '提示', '没有最近打开的文件')
            return
        
        # 创建菜单
        menu = QMenu(self)
        for file_path in recent_files[:10]:  # 最多显示10个
            path = Path(file_path)
            if path.exists():
                menu.addAction(path.name, lambda p=file_path: self._open_file_path(p))
        
        # 显示菜单
        menu.exec_(self.mapToGlobal(self.menuBar().pos()))
    
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, '关于',
            '<h2>Markdown Reader</h2>'
            '<p>一个现代化的 Markdown 阅读器</p>'
            '<p>基于 PyQt5 开发</p>'
            '<p>版本: 1.0.0</p>'
        )
    
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        
        # 恢复窗口最大化状态（在显示后立即执行）
        window_config = self.config_manager.get_window_config()
        if window_config.get('maximized', False):
            self.showMaximized()
        
        # 设置分割器位置（延迟执行，确保窗口已完全显示）
        QTimer.singleShot(50, self._restore_splitter_position)
        
        # 延迟初始化Windows集成（非关键功能）
        QTimer.singleShot(200, self._init_windows_integration)
    
    def _restore_splitter_position(self):
        """恢复分割器位置"""
        splitter_pos = self.config_manager.get_splitter_position()
        if splitter_pos <= 0:
            return

        total_width = max(self.splitter.width(), 1)
        max_tree_width = max(total_width // 3, 1)
        target_pos = min(splitter_pos, max_tree_width)
        other_pane = max(total_width - target_pos, 1)
        self.splitter.setSizes([target_pos, other_pane])
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存当前文件的滚动位置
        if self.current_file:
            self._save_scroll_position()
        
        # 保存文件树的展开状态
        if self.file_tree and self.file_tree.root_path:
            self.file_tree._save_expanded_state()
        
        # 保存配置
        self._save_config()
        event.accept()

