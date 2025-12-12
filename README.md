# Markdown Reader

一个基于 PyQt5 开发的现代化 Markdown 阅读器，专为 Windows 系统设计，提供流畅的阅读体验和丰富的功能。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)

## 功能特性

- 📁 **智能文件管理**
  - 目录树文件浏览（支持 Markdown 文件过滤）
  - 文件标记功能（绿色/红色标记重要文件）
  - 文件和目录的创建、重命名、删除操作
  
- 👁️ **优质阅读体验**
  - 实时 Markdown 预览（GitHub Flavored Markdown）
  - 代码语法高亮显示
  - 滚动位置记忆功能
  - 文件展开状态保存

- 🎨 **个性化定制**
  - 主题切换（浅色/深色/自动跟随系统）
  - 字体大小自定义（正文和代码分别设置）
  - 代码字体和颜色个性化配置
  - 自定义JetBrains Mono等宽字体

- 🪟 **Windows深度集成**
  - 任务栏进度显示
  - 系统主题自动检测
  - 在文件资源管理器中显示文件

- 💾 **智能配置管理**
  - 窗口位置和大小记忆
  - 最近文件和目录历史记录
  - 配置持久化存储

## 系统要求

- **操作系统**: Windows 10/11
- **Python版本**: Python 3.8+
- **依赖库**: 
  - PyQt5 5.15.9
  - PyQtWebEngine 5.15.6
  - markdown 3.5
  - pywin32 306

## 使用方法

### 启动应用

```bash
# 运行程序
python main.py

# 或打开指定文件
python main.py path/to/file.md

# Windows用户可以直接双击运行 run.bat
```

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 打开文件 |
| Ctrl+K | 打开文件夹 |
| F5 | 刷新文件树 |
| Ctrl+, | 打开设置 |
| Alt+F4 | 退出程序 |

### 界面操作

1. **文件管理**:
   - 右键点击文件或目录可进行重命名、删除等操作
   - 右键点击文件可进行标记（绿色/红色）
   - 双击文件即可在右侧预览

2. **主题切换**:
   - 通过"视图"菜单选择浅色、深色或自动主题
   - 自动主题会根据Windows系统主题自动切换

3. **个性化设置**:
   - 通过"设置"菜单调整字体大小、代码字体等
   - 可以为行内代码和代码块设置不同的颜色

## 项目结构

```
MDTool/
├── main.py                 # 应用程序入口
├── core/                   # 核心模块
│   ├── main_window.py      # 主窗口
│   ├── config_manager.py   # 配置管理
│   ├── markdown_renderer.py # Markdown渲染器
│   ├── file_tree.py        # 文件树
│   ├── windows_integration.py # Windows集成
│   ├── resource_path.py    # 资源路径
│   ├── settings_dialog.py  # 设置对话框
│   ├── logger_util.py      # 日志工具
│   └── __init__.py         # 包初始化
├── assets/                 # 资源文件
│   ├── css/                # CSS样式
│   │   ├── light.css       # 浅色主题
│   │   └── dark.css        # 深色主题
│   ├── styles.qss          # Qt样式表
│   └── icons/              # 图标文件
├── ttf/                    # 字体文件
│   └── jetbrains-mono-regular.ttf # 等宽字体
├── logs/                   # 日志文件
├── requirements.txt        # 依赖列表
├── run.bat                # Windows启动脚本
└── README.md              # 项目说明
```

## 技术架构

### 核心组件

- **GUI框架**: PyQt5 提供跨平台的图形界面
- **Web引擎**: PyQtWebEngine 用于渲染Markdown内容
- **Markdown解析**: python-markdown 库提供标准Markdown解析
- **代码高亮**: highlight.js 提供在线代码语法高亮
- **Windows集成**: pywin32 实现与Windows系统的深度集成

### 设计特点

1. **模块化设计**: 核心功能分离到独立模块，便于维护和扩展
2. **配置驱动**: 所有用户设置通过ConfigManager统一管理
3. **主题适配**: 支持浅色和深色两套完整主题
4. **性能优化**: 延迟加载、防抖处理等技术提升响应速度

## 开发指南

### 代码规范

- 遵循PEP 8 Python编码规范
- 使用类型提示增强代码可读性
- 详细的docstring文档说明

### 扩展开发

1. **添加新的Markdown扩展**:
   - 修改 `core/markdown_renderer.py` 中的 `_get_markdown_extensions` 方法

2. **自定义主题**:
   - 修改 `assets/css/` 目录下的CSS文件
   - 调整 `assets/styles.qss` 中的Qt样式

3. **新增功能模块**:
   - 在 `core/` 目录下创建新的模块文件
   - 在 `main_window.py` 中集成新功能

## 常见问题

### 启动时报错
- 确保已安装所有依赖包
- 检查Python版本是否符合要求

### 字体显示异常
- 程序内置JetBrains Mono字体，确保 `ttf/` 目录存在
- 可在设置中更换其他系统字体

### 主题未正确切换
- 检查Windows系统主题设置
- 重启应用使主题更改生效

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证，详情请见 [LICENSE](LICENSE) 文件。

## 致谢
- [JetBrains Mono](https://www.jetbrains.com/lp/mono/) - 等宽字体
