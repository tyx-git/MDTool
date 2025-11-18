"""
文件树模块
提供VSCode风格的文件系统浏览和文件管理功能
"""
import subprocess
import sys
from pathlib import Path
from typing import Optional
from PyQt5.QtCore import (
    QDir, QModelIndex, Qt, pyqtSignal, QFileSystemWatcher, QTimer
)
from PyQt5.QtWidgets import (
    QTreeView, QMenu, QInputDialog, QMessageBox, QFileDialog, QFileSystemModel,
    QStyledItemDelegate, QStyle
)
from PyQt5.QtGui import QColor, QPainter, QPalette


class FileTreeItemDelegate(QStyledItemDelegate):
    """文件树项委托（用于显示标记文件的彩色文字）"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
    
    def initStyleOption(self, option, index: QModelIndex):
        """初始化样式选项（在绘制前调用）"""
        super().initStyleOption(option, index)
        
        # 获取文件路径
        file_model = index.model()
        if not isinstance(file_model, QFileSystemModel):
            return
        
        file_path = file_model.filePath(index)
        path = Path(file_path)
        
        # 如果是文件，检查是否有标记
        if path.is_file():
            mark_type = self.config_manager.get_file_mark(file_path)
            
            if mark_type == 'green':
                # 绿色标记 - 设置文本颜色
                # 注意：选中状态时，样式表会设置白色，我们需要在未选中时显示绿色
                if not (option.state & QStyle.State_Selected):
                    # 未选中状态：使用绿色文本
                    self._set_text_color(option.palette, QColor('#28a745'))
            elif mark_type == 'red':
                # 红色标记
                if not (option.state & QStyle.State_Selected):
                    # 未选中状态：使用红色文本
                    self._set_text_color(option.palette, QColor('#dc3545'))

    @staticmethod
    def _set_text_color(palette: QPalette, color: QColor):
        """同时更新Active/Inactive状态下的文本颜色"""
        for state in (QPalette.Active, QPalette.Inactive, QPalette.Disabled):
            palette.setColor(state, QPalette.Text, color)
    
    def paint(self, painter: QPainter, option, index: QModelIndex):
        """绘制文件树项，根据标记显示不同颜色"""
        # 先初始化样式选项（这会设置颜色）
        self.initStyleOption(option, index)
        
        # 调用父类方法绘制
        super().paint(painter, option, index)


class FileTree(QTreeView):
    """文件树视图（VSCode风格）"""
    
    # 信号定义
    file_selected = pyqtSignal(str)  # 文件路径
    folder_selected = pyqtSignal(str)  # 文件夹路径
    file_marked_changed = pyqtSignal(str, object)  # 文件路径, 标记类型 (str or None)
    
    def __init__(self, config_manager, parent=None):
        """
        初始化文件树
        
        Args:
            config_manager: 配置管理器实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.root_path: Optional[Path] = None
        self.file_model = QFileSystemModel()
        self.file_watcher = QFileSystemWatcher()
        
        self._init_model()
        self._init_ui()
        self._connect_signals()
        
        # 设置自定义委托（用于显示标记颜色）
        self.setItemDelegate(FileTreeItemDelegate(config_manager, self))
    
    def _init_model(self):
        """初始化文件系统模型"""
        # 设置过滤器：只显示目录和Markdown文件
        self.file_model.setFilter(
            QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot | QDir.Hidden
        )
        
        # 设置名称过滤器
        self.file_model.setNameFilters(['*.md', '*.markdown'])
        self.file_model.setNameFilterDisables(False)
        
        # 设置根路径（暂时为空）
        self.setModel(self.file_model)
        
        # 隐藏除名称外的其他列
        self.hideColumn(1)  # 大小
        self.hideColumn(2)  # 类型
        self.hideColumn(3)  # 修改日期
    
    def _init_ui(self):
        """初始化UI"""
        # 设置VSCode风格的样式
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(False)
        self.setAnimated(True)
        self.setIndentation(8)
        
        # 设置紧凑的行高
        self.setStyleSheet("""
            QTreeView {
                font-size: 13px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                background-color: #ffffff;
                border: none;
                outline: none;
            }
            QTreeView::item {
                height: 22px;
                padding: 2px;
            }
            QTreeView::item:hover {
                background-color: #f3f3f3;
            }
            QTreeView::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
            QTreeView::branch {
                background: transparent;
            }
            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: none;
                border: none;
            }
            QTreeView::branch:has-siblings:adjoins-item {
                border-image: none;
                border: none;
            }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: none;
                border: none;
            }
        """)
    
    def _connect_signals(self):
        """连接信号"""
        self.doubleClicked.connect(self._on_item_double_clicked)
        self.file_watcher.directoryChanged.connect(self._on_directory_changed)
    
    def set_root_path(self, path: str):
        """
        设置根路径
        
        Args:
            path: 根目录路径
        """
        root = Path(path)
        if not root.exists() or not root.is_dir():
            return
        
        # 保存当前根目录的展开状态
        if self.root_path:
            self._save_expanded_state()
        
        self.root_path = root
        
        # 设置模型根路径
        self.file_model.setRootPath(str(root))
        self.setRootIndex(self.file_model.index(str(root)))
        
        # 恢复展开状态
        self._restore_expanded_state()
        
        # 监控目录变化
        if self.file_watcher.directories():
            self.file_watcher.removePaths(self.file_watcher.directories())
        self.file_watcher.addPath(str(root))
        self._add_watcher_recursive(root)
    
    def _add_watcher_recursive(self, path: Path, max_depth: int = 3):
        """递归添加文件监控（限制深度）"""
        if max_depth <= 0:
            return
        
        try:
            for item in path.iterdir():
                if item.is_dir():
                    self.file_watcher.addPath(str(item))
                    self._add_watcher_recursive(item, max_depth - 1)
        except PermissionError:
            pass
    
    def select_file(self, file_path: str):
        """
        选中指定文件
        
        Args:
            file_path: 文件路径
        """
        path = Path(file_path)
        if not path.exists():
            return
        
        # 确保文件在树中可见
        index = self.file_model.index(str(path))
        if index.isValid():
            self.setCurrentIndex(index)
            self.scrollTo(index)
    
    def refresh(self):
        """刷新视图"""
        if self.root_path:
            # 保存展开状态
            self._save_expanded_state()
            
            # 刷新模型
            self.file_model.setRootPath(str(self.root_path))
            self.setRootIndex(self.file_model.index(str(self.root_path)))
            
            # 恢复展开状态
            self._restore_expanded_state()
    
    def _save_expanded_state(self):
        """保存当前根目录的展开状态到配置"""
        if not self.root_path:
            return
        
        expanded_paths = []
        for i in range(self.model().rowCount()):
            self._collect_expanded(self.model().index(i, 0), expanded_paths)
        
        root_str = str(self.root_path)
        self.config_manager.set_expanded_paths(root_str, expanded_paths)
        self.config_manager.save()
    
    def _restore_expanded_state(self):
        """从配置恢复展开状态"""
        if not self.root_path:
            return
        
        root_str = str(self.root_path)
        expanded_paths = self.config_manager.get_expanded_paths(root_str)
        
        if expanded_paths:
            # 使用定时器延迟恢复，确保模型已完全加载
            QTimer.singleShot(100, lambda: self._do_restore_expanded(set(expanded_paths)))
    
    def _do_restore_expanded(self, expanded_paths: set):
        """执行展开状态恢复"""
        for i in range(self.model().rowCount()):
            self._restore_expanded(self.model().index(i, 0), expanded_paths)
    
    def _collect_expanded(self, index: QModelIndex, expanded: list):
        """递归收集展开的路径"""
        if self.isExpanded(index):
            path = self.file_model.filePath(index)
            if path not in expanded:
                expanded.append(path)
            for i in range(self.model().rowCount(index)):
                self._collect_expanded(self.model().index(i, 0, index), expanded)
    
    def _restore_expanded(self, index: QModelIndex, expanded_paths: set):
        """递归恢复展开状态"""
        path = self.file_model.filePath(index)
        if path in expanded_paths:
            self.expand(index)
            for i in range(self.model().rowCount(index)):
                self._restore_expanded(self.model().index(i, 0, index), expanded_paths)
    
    def _on_item_double_clicked(self, index: QModelIndex):
        """处理双击事件"""
        path = self.file_model.filePath(index)
        file_path = Path(path)
        
        if file_path.is_file():
            self.file_selected.emit(str(file_path))
        elif file_path.is_dir():
            self.folder_selected.emit(str(file_path))
    
    def _on_directory_changed(self, path: str):
        """处理目录变化事件"""
        # 延迟刷新，避免频繁刷新
        if not hasattr(self, '_refresh_timer'):
            self._refresh_timer = QTimer()
            self._refresh_timer.setSingleShot(True)
            self._refresh_timer.timeout.connect(self.refresh)
        else:
            self._refresh_timer.stop()
        
        self._refresh_timer.start(300)  # 300ms延迟
    
    def contextMenuEvent(self, event):
        """显示右键菜单"""
        index = self.indexAt(event.pos())
        if not index.isValid():
            return
        
        path = self.file_model.filePath(index)
        file_path = Path(path)
        
        menu = QMenu(self)
        
        if file_path.is_file():
            # 文件操作
            mark_type = self.config_manager.get_file_mark(str(file_path))
            
            if mark_type != 'green':
                menu.addAction('标记（绿色）', lambda: self._mark_file(file_path, 'green'))
            if mark_type != 'red':
                menu.addAction('标记（红色）', lambda: self._mark_file(file_path, 'red'))
            if mark_type:
                menu.addAction('取消标记', lambda: self._mark_file(file_path, None))
            
            menu.addSeparator()
            menu.addAction('在文件夹中显示', lambda: self._show_in_folder(file_path))
            menu.addSeparator()
            menu.addAction('重命名', lambda: self._rename_item(file_path))
            menu.addAction('删除', lambda: self._delete_item(file_path))
        else:
            # 目录操作
            menu.addAction('在文件夹中显示', lambda: self._show_in_folder(file_path))
            menu.addSeparator()
            menu.addAction('新建文件夹', lambda: self._create_folder(file_path))
            menu.addAction('新建Markdown文件', lambda: self._create_file(file_path))
            menu.addSeparator()
            menu.addAction('重命名', lambda: self._rename_item(file_path))
            menu.addAction('删除', lambda: self._delete_item(file_path))
        
        menu.exec_(event.globalPos())
    
    def _mark_file(self, file_path: Path, mark_type: Optional[str]):
        """标记文件"""
        self.config_manager.set_file_mark(str(file_path), mark_type)
        self.config_manager.save()
        self.file_marked_changed.emit(str(file_path), mark_type)
        
        # 如果文件在树中，更新该索引（强制重绘）
        index = self.file_model.index(str(file_path))
        if index.isValid():
            # 使用dataChanged信号触发重绘
            self.file_model.dataChanged.emit(index, index)
            # 同时更新视图
            self.update(index)
            # 更新整个视口以确保颜色正确显示
            self.viewport().update()
    
    def _rename_item(self, item_path: Path):
        """重命名文件/目录"""
        old_name = item_path.name
        new_name, ok = QInputDialog.getText(
            self, '重命名', '新名称:', text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            try:
                new_path = item_path.parent / new_name
                if new_path.exists():
                    QMessageBox.warning(self, '错误', '文件或目录已存在')
                    return
                
                # 如果是文件，先获取旧标记（在重命名前）
                old_mark = None
                if item_path.is_file():
                    old_mark = self.config_manager.get_file_mark(str(item_path))
                
                item_path.rename(new_path)
                self.refresh()
                
                # 如果是文件，更新标记
                if old_mark:
                    self.config_manager.set_file_mark(str(new_path), old_mark)
                    self.config_manager.save()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'重命名失败: {e}')
    
    def _delete_item(self, item_path: Path):
        """删除文件/目录"""
        item_type = '目录' if item_path.is_dir() else '文件'
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除{item_type} "{item_path.name}" 吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if item_path.is_file():
                    item_path.unlink()
                    # 移除标记
                    self.config_manager.set_file_mark(str(item_path), None)
                    self.config_manager.save()
                else:
                    import shutil
                    shutil.rmtree(item_path)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除失败: {e}')
    
    def _create_folder(self, parent_path: Path):
        """创建文件夹"""
        name, ok = QInputDialog.getText(self, '新建文件夹', '文件夹名称:')
        
        if ok and name:
            try:
                new_folder = parent_path / name
                if new_folder.exists():
                    QMessageBox.warning(self, '错误', '文件夹已存在')
                    return
                
                new_folder.mkdir(parents=True, exist_ok=True)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'创建文件夹失败: {e}')
    
    def _create_file(self, parent_path: Path):
        """创建Markdown文件"""
        name, ok = QInputDialog.getText(self, '新建文件', '文件名称:')
        
        if ok and name:
            # 确保有.md扩展名
            if not name.endswith(('.md', '.markdown')):
                name += '.md'
            
            try:
                new_file = parent_path / name
                if new_file.exists():
                    QMessageBox.warning(self, '错误', '文件已存在')
                    return
                
                new_file.write_text('', encoding='utf-8')
                self.refresh()
                self.select_file(str(new_file))
            except Exception as e:
                QMessageBox.critical(self, '错误', f'创建文件失败: {e}')
    
    def apply_theme(self, is_dark: bool):
        """应用主题"""
        if is_dark:
            self.setStyleSheet("""
                QTreeView {
                    font-size: 13px;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                    outline: none;
                }
                QTreeView::item {
                    height: 22px;
                    padding: 2px;
                }
                QTreeView::item:hover {
                    background-color: #2a2d2e;
                }
                QTreeView::item:selected {
                    background-color: #094771;
                    color: #ffffff;
                }
                QTreeView::branch {
                    background: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                QTreeView {
                    font-size: 13px;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                    background-color: #ffffff;
                    border: none;
                    outline: none;
                }
                QTreeView::item {
                    height: 22px;
                    padding: 2px;
                }
                QTreeView::item:hover {
                    background-color: #f3f3f3;
                }
                QTreeView::item:selected {
                    background-color: #007acc;
                    color: #ffffff;
                }
                QTreeView::branch {
                    background: transparent;
                }
            """)
        
        # 刷新视图以更新标记颜色
        self.viewport().update()
    
    def _show_in_folder(self, item_path: Path):
        """在文件夹中显示（Windows资源管理器）"""
        try:
            if sys.platform == 'win32':
                # Windows系统：使用explorer.exe打开并选中文件/文件夹
                path_str = str(item_path.resolve())
                # 使用 /select, 参数选中文件
                subprocess.run(['explorer.exe', '/select,', path_str], check=False)
            elif sys.platform == 'darwin':
                # macOS系统：使用open命令
                subprocess.run(['open', '-R', str(item_path.resolve())], check=False)
            else:
                # Linux系统：使用文件管理器打开父目录
                parent_dir = str(item_path.parent.resolve())
                # 尝试使用常见的文件管理器
                file_managers = ['nautilus', 'dolphin', 'thunar', 'pcmanfm', 'nemo']
                for fm in file_managers:
                    try:
                        subprocess.run([fm, parent_dir], check=False)
                        break
                    except FileNotFoundError:
                        continue
                else:
                    QMessageBox.information(
                        self, '提示',
                        f'无法打开文件管理器。\n文件路径: {item_path}'
                    )
        except Exception as e:
            QMessageBox.warning(self, '错误', f'在文件夹中显示失败: {e}')

