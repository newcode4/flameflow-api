"""
전역 설정 파일
환경변수와 애플리케이션 설정을 관리합니다.
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """기본 설정"""
    # Flask 설정
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "True") == "True"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))

    # Supabase 설정
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

    # Claude API 설정
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
    CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", 1000))

    # GA4 설정
    GA4_DEFAULT_PROPERTY_ID = os.getenv("GA4_DEFAULT_PROPERTY_ID")
    GA4_CREDENTIALS_PATH = os.getenv("GA4_CREDENTIALS_PATH", "credentials/ga4-credentials.json")
    GA4_DEFAULT_DAYS = int(os.getenv("GA4_DEFAULT_DAYS", 30))

    # Telegram 설정
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

    # 토큰 관련 설정
    DEFAULT_TOKEN_BALANCE = int(os.getenv("DEFAULT_TOKEN_BALANCE", 10000))
    TOKEN_COST_PER_1K = float(os.getenv("TOKEN_COST_PER_1K", 0.001))  # 1000토큰당 비용

    # 스케줄러 설정
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "True") == "True"
    DAILY_SYNC_TIME = os.getenv("DAILY_SYNC_TIME", "03:00")  # 새벽 3시

    # 로깅 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = "logs"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # 페이지네이션
    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", 20))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", 100))

    @staticmethod
    def validate():
        """필수 환경변수 검증"""
        required = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_KEY",
            "ANTHROPIC_API_KEY"
        ]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    DEBUG = False
    LOG_LEVEL = "WARNING"

class TestConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    DEBUG = True

# 환경별 설정 선택
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "test": TestConfig
}

def get_config():
    """현재 환경의 설정 반환"""
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
