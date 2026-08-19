import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """配置日志系统"""

    # 创建日志目录
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # 日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # 文件日志 - 普通日志
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10240000,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # 文件日志 - 错误日志
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10240000,
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # 配置Flask应用日志
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)

    # 记录启动日志
    app.logger.info('学籍管理系统启动')

    return app.logger