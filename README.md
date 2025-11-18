# Markdown Reader

一个基于 PyQt5 开发的现代化 Markdown 阅读器，专为 Windows 系统设计。

## 功能特性

- 📁 目录树文件浏览（支持 Markdown 文件过滤）
- 👁️ 实时 Markdown 预览（GitHub Flavored Markdown）
- 🎨 代码语法高亮
- 🌓 主题切换（浅色/深色/自动）
- 🪟 Windows 系统集成（任务栏进度、主题检测）
- 💾 配置持久化（窗口位置、最近文件、标记文件等）
- 📝 文件管理（重命名、删除、创建目录/文件）
- 🏷️ 文件标记（绿色/红色标记）

## 系统要求

- Windows 10/11
- Python 3.8+

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## 使用方法

```bash
# 运行程序
python main.py

# 或打开指定文件
python main.py path/to/file.md
```

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
│   └── settings_dialog.py  # 设置对话框
├── assets/                 # 资源文件
│   ├── css/               # CSS样式
│   └── icons/             # 图标
├── logs/                   # 日志文件
├── requirements.txt        # 依赖列表
└── README.md              # 项目说明
```

## 技术栈

- **GUI框架**: PyQt5 5.15.9
- **Web引擎**: PyQtWebEngine 5.15.6
- **Markdown解析**: markdown 3.5
- **代码高亮**: Pygments 2.15
- **Windows集成**: pywin32 306

## 许可证

MIT License
