"""
로깅 유틸리티
파일별, 레벨별 로깅을 관리합니다.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config.settings import get_config

config = get_config()

# 로그 디렉토리 생성
os.makedirs(config.LOG_DIR, exist_ok=True)

class ColoredFormatter(logging.Formatter):
    """컬러 출력을 위한 포매터"""
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)

def setup_logger(name, log_file=None, level=None):
    """
    로거 설정

    Args:
        name: 로거 이름
        log_file: 로그 파일 이름 (없으면 콘솔만)
        level: 로그 레벨

    Returns:
        Logger 객체
    """
    logger = logging.getLogger(name)
    logger.setLevel(level or config.LOG_LEVEL)

    # 기존 핸들러 제거 (중복 방지)
    logger.handlers = []

    # 포맷 정의
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = ColoredFormatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (지정된 경우)
    if log_file:
        log_path = os.path.join(config.LOG_DIR, log_file)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

# 전역 로거들
app_logger = setup_logger('app', 'app.log')
error_logger = setup_logger('error', 'error.log', level='ERROR')
scheduler_logger = setup_logger('scheduler', 'scheduler.log')
api_logger = setup_logger('api', 'api.log')

def log_api_call(endpoint, method, user_id=None, status_code=None, duration=None):
    """API 호출 로그"""
    api_logger.info(
        f"{method} {endpoint} | User: {user_id or 'Anonymous'} | "
        f"Status: {status_code} | Duration: {duration:.3f}s"
    )

def log_error(error, context=None):
    """에러 로그"""
    error_logger.error(f"Error: {str(error)}")
    if context:
        error_logger.error(f"Context: {context}")

def log_scheduler_job(job_name, status, message=None):
    """스케줄러 작업 로그"""
    scheduler_logger.info(f"Job: {job_name} | Status: {status} | {message or ''}")
