"""
Markdown渲染器模块
负责将Markdown文本转换为HTML，应用CSS样式和主题
"""
import re
import markdown
from pathlib import Path
from typing import Tuple
from .resource_path import get_assets_dir, get_resource_path
from .windows_integration import WindowsIntegration
from .logger_util import get_logger, log_error


class MarkdownRenderer:
    """Markdown渲染器"""
    
    def __init__(self):
        self._css_cache = {}
        self._logger = get_logger(__name__)
    
    def _load_css(self, theme: str) -> str:
        """
        加载CSS样式（带缓存）
        
        Args:
            theme: 主题名称（'light' 或 'dark'）
            
        Returns:
            CSS样式内容
        """
        if theme in self._css_cache:
            return self._css_cache[theme]
        
        css_file = get_assets_dir() / 'css' / f'{theme}.css'
        
        if css_file.exists():
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                    self._css_cache[theme] = css_content
                    return css_content
            except IOError as e:
                log_error("加载CSS文件失败", e, self._logger)
        
        return ''

    def _build_code_font_css(self) -> str:
        """
        构建代码字体的@font-face定义，使用ttf目录中的字体文件
        Returns:
            CSS字符串，如果字体文件不存在则返回空字符串
        """
        font_path = get_resource_path('ttf/jetbrains-mono-regular.ttf')
        if not font_path.exists():
            self._logger.warning("代码字体文件不存在: %s", font_path)
            return ''
        try:
            font_uri = font_path.resolve().as_uri()
        except ValueError as exc:
            self._logger.error("无法解析代码字体路径: %s", exc)
            return ''

        return f"""
@font-face {{
    font-family: 'MDToolCode';
    src: url('{font_uri}') format('truetype');
    font-weight: 400;
    font-style: normal;
}}
pre,
pre code {{
    font-family: 'MDToolCode', Consolas, 'Courier New', monospace !important;
}}
"""
    
    def _get_actual_theme(self, theme_setting: str) -> str:
        """
        获取实际主题（处理auto模式）
        
        Args:
            theme_setting: 主题设置（'light'/'dark'/'auto'）
            
        Returns:
            实际主题（'light' 或 'dark'）
        """
        if theme_setting == 'auto':
            return WindowsIntegration.get_system_theme()
        return theme_setting
    
    def _apply_code_styles(self, css_content: str, body_font_size: int,
                          code_font_size: int, code_font_family: str = None,
                          code_font_weight: str = None, code_inline_color: str = None,
                          code_block_color: str = None) -> str:
        """
        应用代码样式设置到CSS
        
        Args:
            css_content: 原始CSS内容
            body_font_size: 正文字体大小
            code_font_size: 代码字体大小
            code_font_family: 代码字体族
            code_font_weight: 代码字体粗细
            code_inline_color: 行内代码颜色
            code_block_color: 代码块颜色
            
        Returns:
            应用样式后的CSS内容
        """
        # 替换body字体大小
        css_content = re.sub(
            r'font-size:\s*16px',
            f'font-size: {body_font_size}px',
            css_content
        )
        
        # 应用代码字体族
        if code_font_family:
            # 替换所有code的font-family
            css_content = re.sub(
                r'(code\s*\{[^}]*font-family:\s*)[^;]+',
                rf'\1{code_font_family}',
                css_content
            )
            css_content = re.sub(
                r'(pre code\s*\{[^}]*font-family:\s*)[^;]+',
                rf'\1{code_font_family}',
                css_content
            )
            css_content = re.sub(
                r'(p code[^}]*\{[^}]*font-family:\s*)[^;]+',
                rf'\1{code_font_family}',
                css_content
            )
        
        # 应用代码字体粗细
        if code_font_weight:
            # 替换所有code的font-weight（如果已存在）
            css_content = re.sub(
                r'(code\s*\{[^}]*font-weight:\s*)[^;]+',
                rf'\1{code_font_weight}',
                css_content
            )
            css_content = re.sub(
                r'(pre code\s*\{[^}]*font-weight:\s*)[^;]+',
                rf'\1{code_font_weight}',
                css_content
            )
            css_content = re.sub(
                r'(p code[^}]*\{[^}]*font-weight:\s*)[^;]+',
                rf'\1{code_font_weight}',
                css_content
            )
            css_content = re.sub(
                r'(li code[^}]*\{[^}]*font-weight:\s*)[^;]+',
                rf'\1{code_font_weight}',
                css_content
            )
            css_content = re.sub(
                r'(td code[^}]*\{[^}]*font-weight:\s*)[^;]+',
                rf'\1{code_font_weight}',
                css_content
            )
            css_content = re.sub(
                r'(th code[^}]*\{[^}]*font-weight:\s*)[^;]+',
                rf'\1{code_font_weight}',
                css_content
            )
            
            # 确保所有code选择器都有font-weight（如果不存在则添加）
            # code { ... }
            if not re.search(r'code\s*\{[^}]*font-weight:', css_content):
                css_content = re.sub(
                    r'(code\s*\{[^}]*?)(;)',
                    rf'\1    font-weight: {code_font_weight};\2',
                    css_content,
                    count=1,
                    flags=re.DOTALL
                )
            
            # pre code { ... }（如果不存在font-weight）
            if not re.search(r'pre code\s*\{[^}]*font-weight:', css_content):
                css_content = re.sub(
                    r'(pre code\s*\{[^}]*?)(;)',
                    rf'\1    font-weight: {code_font_weight};\2',
                    css_content,
                    flags=re.DOTALL
                )
        
        # 替换代码字体大小
        css_content = re.sub(
            r'(code\s*\{[^}]*font-size:\s*)14px',
            rf'\1{code_font_size}px',
            css_content
        )
        css_content = re.sub(
            r'(pre code\s*\{[^}]*font-size:\s*)14px',
            rf'\1{code_font_size}px',
            css_content
        )
        css_content = re.sub(
            r'(p code[^}]*\{[^}]*font-size:\s*)14px',
            rf'\1{code_font_size}px',
            css_content
        )
        
        # 应用代码颜色
        if code_inline_color:
            # 替换行内代码颜色
            css_content = re.sub(
                r'(code\s*\{[^}]*color:\s*)[^;]+',
                rf'\1{code_inline_color}',
                css_content
            )
            css_content = re.sub(
                r'(p code[^}]*\{[^}]*color:\s*)[^;]+',
                rf'\1{code_inline_color}',
                css_content
            )
            css_content = re.sub(
                r'(li code[^}]*\{[^}]*color:\s*)[^;]+',
                rf'\1{code_inline_color}',
                css_content
            )
        
        if code_block_color:
            # 替换代码块颜色
            css_content = re.sub(
                r'(pre code\s*\{[^}]*color:\s*)[^;]+',
                rf'\1{code_block_color}',
                css_content
            )
        
        return css_content
    
    def _get_markdown_extensions(self):
        """
        获取Markdown扩展配置（扩展接口：可被子类重写以自定义扩展）
        
        Returns:
            (extensions, extension_configs) 元组
        """
        extensions = [
            'fenced_code',  # 支持 ``` 代码块
            'tables',
            'toc',
            'nl2br',
            'sane_lists',
            'attr_list',
            'def_list',
            'footnotes',
            'md_in_html'
        ]
        
        extension_configs = {
            'fenced_code': {
                'lang_prefix': 'language-'  # 语言前缀
            }
        }
        
        return extensions, extension_configs
    
    def _convert_markdown_to_html(self, text: str) -> str:
        """
        将Markdown文本转换为HTML（扩展接口：可被子类重写以自定义转换逻辑）
        
        Args:
            text: Markdown文本
            
        Returns:
            HTML内容
        """
        extensions, extension_configs = self._get_markdown_extensions()
        
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs
        )
        return md.convert(text)
    
    def _get_highlight_assets(self, theme: str) -> Tuple[str, str]:
        """
        获取highlight.js静态资源
        
        Args:
            theme: 实际主题（light/dark）
        
        Returns:
            (css_url, js_url)
        """
        base_url = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0"
        css_theme = "styles/github.min.css" if theme == 'light' else "styles/github-dark.min.css"
        css_url = f"{base_url}/{css_theme}"
        js_url = f"{base_url}/highlight.min.js"
        return css_url, js_url
    
    def _generate_html_document(self, html_body: str, css_content: str,
                                highlight_assets: Tuple[str, str]) -> str:
        """
        生成完整的HTML文档（扩展接口：可被子类重写以自定义HTML结构）
        
        Args:
            html_body: HTML主体内容
            css_content: CSS样式内容
            
        Returns:
            完整的HTML文档
        """
        highlight_css, highlight_js = highlight_assets
        highlight_head = f"""
    <link rel="stylesheet" href="{highlight_css}">
    <script src="{highlight_js}" defer></script>
""" if highlight_assets else ""
        highlight_bootstrap = """
    <script>
        window.addEventListener('DOMContentLoaded', function () {
            if (window.hljs && window.hljs.highlightAll) {
                window.hljs.highlightAll();
            }
        });
    </script>
""" if highlight_assets else ""
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        {css_content}
    </style>
{highlight_head}
</head>
<body>
    {html_body}
{highlight_bootstrap}
</body>
</html>"""
    
    def render_text(self, text: str, theme_setting: str = 'auto',
                   body_font_size: int = 16, code_font_size: int = 14,
                   code_font_family: str = None, code_font_weight: str = None,
                   code_inline_color: str = None, code_block_color: str = None) -> str:
        """
        渲染Markdown文本
        
        Args:
            text: Markdown文本
            theme_setting: 主题设置（'light'/'dark'/'auto'）
            body_font_size: 正文字体大小
            code_font_size: 代码字体大小
            code_font_family: 代码字体族
            code_font_weight: 代码字体粗细
            code_inline_color: 行内代码颜色
            code_block_color: 代码块颜色
            
        Returns:
            完整的HTML文档
        """
        # 获取实际主题
        theme = self._get_actual_theme(theme_setting)
        
        # 转换为HTML
        html_body = self._convert_markdown_to_html(text)
        
        # 加载CSS
        css_content = self._load_css(theme)
        
        # 应用字体和样式设置
        css_content = self._apply_code_styles(
            css_content, body_font_size, code_font_size,
            code_font_family, code_font_weight,
            code_inline_color, code_block_color
        )

        custom_code_font_css = self._build_code_font_css()
        if custom_code_font_css:
            css_content = f"{custom_code_font_css}\n{css_content}"
        
        highlight_assets = self._get_highlight_assets(theme)
        
        # 生成完整HTML
        return self._generate_html_document(html_body, css_content, highlight_assets)
    
    def render_file(self, file_path: Path, theme_setting: str = 'auto', 
                   body_font_size: int = 16, code_font_size: int = 14,
                   code_font_family: str = None, code_font_weight: str = None,
                   code_inline_color: str = None, code_block_color: str = None) -> str:
        """
        渲染Markdown文件
        
        Args:
            file_path: Markdown文件路径
            theme_setting: 主题设置（'light'/'dark'/'auto'）
            body_font_size: 正文字体大小
            code_font_size: 代码字体大小
            code_font_family: 代码字体族
            code_font_weight: 代码字体粗细
            code_inline_color: 行内代码颜色
            code_block_color: 代码块颜色
            
        Returns:
            完整的HTML文档
        """
        if not file_path.exists():
            return self._render_error(f"文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except IOError as e:
            log_error(f"读取文件失败: {file_path}", e, self._logger)
            return self._render_error(f"读取文件失败: {e}")
        
        # 复用render_text的逻辑
        return self.render_text(
            text, theme_setting, body_font_size, code_font_size,
            code_font_family, code_font_weight,
            code_inline_color, code_block_color
        )
    
    def _render_error(self, message: str) -> str:
        """
        渲染错误页面
        
        Args:
            message: 错误消息
            
        Returns:
            错误页面的HTML
        """
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            padding: 40px;
            color: #d32f2f;
        }}
    </style>
</head>
<body>
    <h1>错误</h1>
    <p>{message}</p>
</body>
</html>"""

