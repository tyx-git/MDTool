"""
Markdown Reader 应用程序入口
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter

from PyQt5.QtCore import Qt, QTimer, qInstallMessageHandler, QtMsgType
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from core.main_window import MainWindow
from core.resource_path import get_logs_dir, get_resource_path


def setup_logging():
    """配置日志系统"""
    logs_dir = get_logs_dir()
    log_file = logs_dir / f'markdown_reader_{datetime.now().strftime("%Y%m%d")}.log'
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout) if sys.stdout else logging.NullHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info('=' * 50)
    logger.info('Markdown Reader 启动')
    logger.info(f'日志文件: {log_file}')
    
    return logger


def qt_message_handler(msg_type, context, message):
    """Qt消息处理器，过滤掉字体相关的警告"""
    # 过滤掉DirectWrite字体相关的警告
    if 'DirectWrite' in message or 'CreateFontFaceFromHDC' in message:
        return
    # 其他消息正常处理
    if msg_type == QtMsgType.QtDebugMsg:
        logging.debug(message)
    elif msg_type == QtMsgType.QtWarningMsg:
        logging.warning(message)
    elif msg_type == QtMsgType.QtCriticalMsg:
        logging.critical(message)
    elif msg_type == QtMsgType.QtFatalMsg:
        logging.critical(message)


def exception_hook(exc_type, exc_value, exc_traceback):
    """全局异常处理"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(__name__)
    logger.critical(
        '未捕获的异常',
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def main():
    """主函数"""
    startup_begin = perf_counter()
    # 设置全局异常处理
    sys.excepthook = exception_hook
    
    # 高DPI支持（必须在创建QApplication之前设置）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 配置日志
    log_stage_begin = perf_counter()
    logger = setup_logging()
    logger.info(
        "启动阶段: 日志系统初始化耗时 %.1f ms",
        (perf_counter() - log_stage_begin) * 1000,
    )
    
    # 创建应用程序
    log_stage_begin = perf_counter()
    app = QApplication(sys.argv)
    logger.info(
        "启动阶段: QApplication 创建耗时 %.1f ms",
        (perf_counter() - log_stage_begin) * 1000,
    )
    
    # 安装Qt消息处理器，过滤字体警告（必须在创建QApplication之后）
    qInstallMessageHandler(qt_message_handler)
    app.setApplicationName('Markdown Reader')
    app.setOrganizationName('MarkdownReader')
    
    # 设置应用程序图标
    icon_path = get_resource_path('assets/icons/ca.jpg')
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    try:
        # 预先加载配置（在创建窗口前）
        from core.config_manager import ConfigManager
        log_stage_begin = perf_counter()
        config_manager = ConfigManager()
        logger.info(
            "启动阶段: 配置加载耗时 %.1f ms",
            (perf_counter() - log_stage_begin) * 1000,
        )
        
        # 创建主窗口（传入配置管理器，避免重复加载）
        log_stage_begin = perf_counter()
        window = MainWindow(config_manager)
        logger.info(
            "启动阶段: 主窗口初始化耗时 %.1f ms",
            (perf_counter() - log_stage_begin) * 1000,
        )
        
        # 显示窗口（此时窗口大小和位置已根据配置设置好）
        window.show()
        
        # 处理命令行参数
        if len(sys.argv) > 1:
            file_path = Path(sys.argv[1])
            if file_path.exists() and file_path.is_file():
                # 延迟打开，确保窗口已完全显示
                QTimer.singleShot(100, lambda: window._open_file_path(str(file_path)))
        
        logger.info(
            '应用程序启动成功，总耗时 %.1f ms',
            (perf_counter() - startup_begin) * 1000,
        )
        
        # 运行应用程序
        exit_code = app.exec_()
        logger.info(f'应用程序退出，退出码: {exit_code}')
        return exit_code
        
    except Exception as e:
        logger.critical(f'应用程序启动失败: {e}', exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

