"""
FrameFlow GA4 AI API - 메인 애플리케이션
모듈화된 구조로 리팩토링된 버전
"""
from flask import Flask, jsonify
from flask_cors import CORS
import atexit

# 설정 로드
from config.settings import get_config, Config

# 로거
from utils.logger import app_logger

# API 블루프린트
from api.users import users_bp
from api.ga4 import ga4_bp
from api.chat import chat_bp

# 서비스
from services.scheduler_service import scheduler_service

# 설정 초기화
config = get_config()

# 필수 환경변수 검증
try:
    Config.validate()
except ValueError as e:
    app_logger.error(f"Configuration error: {e}")
    raise

# Flask 앱 생성
app = Flask(__name__)
app.config.from_object(config)

# CORS 활성화
CORS(app)

# 블루프린트 등록
app.register_blueprint(users_bp)
app.register_blueprint(ga4_bp)
app.register_blueprint(chat_bp)

# 스케줄러 시작
scheduler_service.start()

# 애플리케이션 종료 시 스케줄러 중지
atexit.register(scheduler_service.stop)

@app.route("/")
def home():
    """서버 상태 확인"""
    return jsonify({
        "service": "FrameFlow GA4 AI API",
        "version": "2.0",
        "status": "running",
        "message": "서버가 정상적으로 작동 중입니다.",
        "features": [
            "사용자 관리",
            "GA4 데이터 동기화 (전체/증분)",
            "AI 챗봇",
            "일일 자동 데이터 갱신",
            "토큰 관리"
        ]
    })

@app.route("/health")
def health():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "scheduler": "running" if scheduler_service.scheduler.running else "stopped"
    })

@app.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({
        "success": False,
        "message": "요청한 엔드포인트를 찾을 수 없습니다"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    app_logger.error(f"Internal server error: {error}")
    return jsonify({
        "success": False,
        "message": "서버 내부 오류가 발생했습니다"
    }), 500

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 FrameFlow GA4 AI API 서버를 시작합니다.")
    print(f"   - 주소: http://{config.HOST}:{config.PORT}")
    print(f"   - 모드: {'Debug' if config.DEBUG else 'Production'}")
    print(f"   - 스케줄러: {'활성화' if config.SCHEDULER_ENABLED else '비활성화'}")
    if config.SCHEDULER_ENABLED:
        print(f"   - 일일 동기화 시간: {config.DAILY_SYNC_TIME}")
    print("="*60 + "\n")

    app_logger.info(f"Starting FrameFlow API on {config.HOST}:{config.PORT}")

    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )
