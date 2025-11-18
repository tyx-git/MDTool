"""
设置对话框模块
提供应用程序设置界面
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QPushButton, QGroupBox, QFormLayout, QFontComboBox,
    QColorDialog, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config_manager, parent=None):
        """
        初始化设置对话框
        
        Args:
            config_manager: 配置管理器实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self._init_ui()
        # 延迟过滤字体，确保字体列表已完全加载
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._filter_problematic_fonts)
        self._load_settings()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle('设置')
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        
        layout = QVBoxLayout(self)
        
        # 主题设置
        theme_group = QGroupBox('主题')
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['浅色', '深色', '自动'])
        theme_layout.addRow('主题:', self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # 正文字体设置
        font_group = QGroupBox('正文字体')
        font_layout = QFormLayout()
        
        self.body_font_spin = QSpinBox()
        self.body_font_spin.setRange(10, 30)
        self.body_font_spin.setSuffix(' px')
        font_layout.addRow('字体大小:', self.body_font_spin)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # 代码字体设置
        code_group = QGroupBox('代码字体')
        code_layout = QFormLayout()
        
        # 代码字体大小
        self.code_font_spin = QSpinBox()
        self.code_font_spin.setRange(8, 24)
        self.code_font_spin.setSuffix(' px')
        code_layout.addRow('字体大小:', self.code_font_spin)
        
        # 代码字体族
        self.code_font_combo = QFontComboBox()
        self.code_font_combo.setFontFilters(QFontComboBox.MonospacedFonts)  # 只显示等宽字体
        code_layout.addRow('字体:', self.code_font_combo)
        
        # 代码字体粗细
        self.code_weight_combo = QComboBox()
        self.code_weight_combo.addItems(['正常', '粗体'])
        code_layout.addRow('字体粗细:', self.code_weight_combo)
        
        # 行内代码颜色
        inline_color_layout = QHBoxLayout()
        self.code_inline_color_edit = QLineEdit()
        self.code_inline_color_edit.setPlaceholderText('使用主题默认颜色')
        self.code_inline_color_edit.setReadOnly(True)
        self.code_inline_color_btn = QPushButton('选择颜色')
        self.code_inline_color_btn.clicked.connect(lambda: self._choose_color('inline'))
        inline_color_layout.addWidget(self.code_inline_color_edit)
        inline_color_layout.addWidget(self.code_inline_color_btn)
        code_layout.addRow('行内代码颜色:', inline_color_layout)
        
        # 代码块颜色
        block_color_layout = QHBoxLayout()
        self.code_block_color_edit = QLineEdit()
        self.code_block_color_edit.setPlaceholderText('使用主题默认颜色')
        self.code_block_color_edit.setReadOnly(True)
        self.code_block_color_btn = QPushButton('选择颜色')
        self.code_block_color_btn.clicked.connect(lambda: self._choose_color('block'))
        block_color_layout.addWidget(self.code_block_color_edit)
        block_color_layout.addWidget(self.code_block_color_btn)
        code_layout.addRow('代码块颜色:', block_color_layout)
        
        code_group.setLayout(code_layout)
        layout.addWidget(code_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton('确定')
        self.ok_button.clicked.connect(self._on_ok)
        self.cancel_button = QPushButton('取消')
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _filter_problematic_fonts(self):
        """过滤掉有问题的字体（如Fixedsys、Terminal等）"""
        problematic_fonts = ['Fixedsys', 'Terminal', 'System']
        for i in range(self.code_font_combo.count() - 1, -1, -1):
            font_name = self.code_font_combo.itemText(i)
            if font_name in problematic_fonts:
                self.code_font_combo.removeItem(i)
    
    def _load_settings(self):
        """加载设置"""
        # 加载主题
        theme = self.config_manager.get('theme', 'auto')
        theme_map = {'light': 0, 'dark': 1, 'auto': 2}
        self.theme_combo.setCurrentIndex(theme_map.get(theme, 2))
        
        # 加载字体大小
        body_size = self.config_manager.get('font.body_size', 16)
        code_size = self.config_manager.get('font.code_size', 14)
        self.body_font_spin.setValue(body_size)
        self.code_font_spin.setValue(code_size)
        
        # 加载代码字体设置
        code_family = self.config_manager.get('font.code_family', 'Consolas, Monaco, "Courier New", monospace')
        # 从字体族字符串中提取第一个字体名
        first_font = code_family.split(',')[0].strip().strip('"\'')
        font_index = self.code_font_combo.findText(first_font)
        if font_index >= 0:
            self.code_font_combo.setCurrentIndex(font_index)
        
        code_weight = self.config_manager.get('font.code_weight', 'normal')
        self.code_weight_combo.setCurrentIndex(0 if code_weight == 'normal' else 1)
        
        # 加载代码颜色
        inline_color = self.config_manager.get('font.code_inline_color')
        if inline_color:
            self.code_inline_color_edit.setText(inline_color)
            self.code_inline_color_edit.setStyleSheet(f'background-color: {inline_color};')
        
        block_color = self.config_manager.get('font.code_block_color')
        if block_color:
            self.code_block_color_edit.setText(block_color)
            self.code_block_color_edit.setStyleSheet(f'background-color: {block_color};')
    
    def _choose_color(self, color_type: str):
        """选择颜色"""
        current_color = None
        if color_type == 'inline':
            current_text = self.code_inline_color_edit.text()
            if current_text:
                current_color = QColor(current_text)
        else:
            current_text = self.code_block_color_edit.text()
            if current_text:
                current_color = QColor(current_text)
        
        color = QColorDialog.getColor(current_color, self, '选择颜色')
        if color.isValid():
            color_str = color.name()
            if color_type == 'inline':
                self.code_inline_color_edit.setText(color_str)
                self.code_inline_color_edit.setStyleSheet(f'background-color: {color_str};')
            else:
                self.code_block_color_edit.setText(color_str)
                self.code_block_color_edit.setStyleSheet(f'background-color: {color_str};')
    
    def _on_ok(self):
        """确定按钮点击"""
        # 保存主题
        theme_map = {0: 'light', 1: 'dark', 2: 'auto'}
        theme = theme_map[self.theme_combo.currentIndex()]
        self.config_manager.set('theme', theme)
        
        # 保存字体大小
        self.config_manager.set('font.body_size', self.body_font_spin.value())
        self.config_manager.set('font.code_size', self.code_font_spin.value())
        
        # 保存代码字体设置
        selected_font = self.code_font_combo.currentFont().family()
        # 构建字体族字符串（包含备用字体）
        font_family = f'{selected_font}, "Courier New", Consolas, Monaco, monospace'
        self.config_manager.set('font.code_family', font_family)
        
        code_weight = 'normal' if self.code_weight_combo.currentIndex() == 0 else 'bold'
        self.config_manager.set('font.code_weight', code_weight)
        
        # 保存代码颜色
        inline_color = self.code_inline_color_edit.text() or None
        self.config_manager.set('font.code_inline_color', inline_color)
        
        block_color = self.code_block_color_edit.text() or None
        self.config_manager.set('font.code_block_color', block_color)
        
        # 保存配置
        self.config_manager.save()
        
        self.accept()

