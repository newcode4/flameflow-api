import telebot
import subprocess
import os
import platform
import time
import threading
import json
from datetime import datetime
from dotenv import load_dotenv
from process_manager import ProcessManager

load_dotenv()

# Telegram 설정
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))

# 실행 환경 감지
IS_WINDOWS = platform.system() == "Windows"
IS_LOCAL = os.getenv("ENVIRONMENT", "local") == "local"

bot = telebot.TeleBot(BOT_TOKEN)
process_manager = ProcessManager()

# 에러 모니터링 상태
monitoring_active = False
monitoring_thread = None

def run_command(cmd):
    """시스템 명령 실행"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"❌ 에러: {str(e)}"

def error_monitor():
    """백그라운드 에러 모니터링"""
    global monitoring_active
    
    while monitoring_active:
        try:
            # 새로운 에러 체크
            new_errors = process_manager.monitor_errors()
            
            if new_errors:
                # 에러 발생 시 텔레그램으로 알림
                error_message = f"🚨 FrameFlow 에러 발생!\n\n```\n{new_errors}\n```"
                
                try:
                    bot.send_message(
                        ALLOWED_USER_ID, 
                        error_message, 
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"텔레그램 에러 알림 실패: {e}")
            
            # 30초마다 체크
            time.sleep(30)
            
        except Exception as e:
            print(f"에러 모니터링 실패: {e}")
            time.sleep(60)  # 에러 시 1분 대기

def start_error_monitoring():
    """에러 모니터링 시작"""
    global monitoring_active, monitoring_thread
    
    if not monitoring_active:
        monitoring_active = True
        monitoring_thread = threading.Thread(target=error_monitor, daemon=True)
        monitoring_thread.start()
        return True
    return False

def stop_error_monitoring():
    """에러 모니터링 중지"""
    global monitoring_active
    monitoring_active = False
    return True

@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return

    if IS_LOCAL or IS_WINDOWS:
        bot.reply_to(message, "⚠️ 로컬 환경에서는 수동으로 app.py를 실행하세요.\n명령어: python app.py")
    else:
        bot.reply_to(message, "🚀 FrameFlow 시작 중...")
        
        result = process_manager.start()
        
        if result["status"] == "started":
            # 에러 모니터링도 함께 시작
            start_error_monitoring()
            bot.reply_to(message, f"✅ {result['message']}\n📊 에러 모니터링도 활성화되었습니다.")
        else:
            bot.reply_to(message, f"❌ {result['message']}")

@bot.message_handler(commands=['stop'])
def cmd_stop(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return

    if IS_LOCAL or IS_WINDOWS:
        bot.reply_to(message, "⚠️ 로컬 환경에서는 수동으로 app.py를 종료하세요.\n(Ctrl+C)")
    else:
        result = process_manager.stop()
        stop_error_monitoring()
        bot.reply_to(message, f"⏹️ {result['message']}")

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return

    if IS_LOCAL or IS_WINDOWS:
        bot.reply_to(message, "⚠️ 로컬 환경에서는 수동으로 app.py를 재시작하세요.")
    else:
        bot.reply_to(message, "🔄 FrameFlow 재시작 중...")
        
        result = process_manager.restart()
        
        # 재시작 후 에러 모니터링 다시 시작
        start_error_monitoring()
        bot.reply_to(message, f"✅ {result['message']}")

@bot.message_handler(commands=['status'])
def cmd_status(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return

    if IS_LOCAL or IS_WINDOWS:
        # 로컬에서는 Flask API 핑으로 상태 체크
        try:
            import requests
            response = requests.get('http://localhost:5000/', timeout=3)
            if response.status_code == 200:
                bot.reply_to(message, "🟢 FrameFlow 실행 중 (로컬)")
            else:
                bot.reply_to(message, "🟡 API 응답 이상")
        except:
            bot.reply_to(message, "🔴 FrameFlow 중지됨 (로컬)")
    else:
        result = process_manager.get_status()
        
        if result["status"] == "running":
            status_msg = f"""🟢 FrameFlow 실행 중

📊 상태 정보:
• PID: {result.get('pid', 'N/A')}
• 실행 시간: {result.get('uptime', 'N/A')}
• 메모리 사용량: {result.get('memory', 'N/A')}
• 에러 모니터링: {'🟢 활성' if monitoring_active else '🔴 비활성'}"""
        else:
            status_msg = f"🔴 {result['message']}"
        
        bot.reply_to(message, status_msg)

@bot.message_handler(commands=['logs'])
def cmd_logs(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return

    if IS_LOCAL or IS_WINDOWS:
        bot.reply_to(message, "⚠️ 로컬 환경에서는 콘솔 로그를 확인하세요.")
    else:
        logs = process_manager.get_logs(lines=30)

        if len(logs) > 4000:
            logs = logs[-4000:]

        bot.reply_to(message, f"📋 최근 로그:\n\n```\n{logs}\n```", parse_mode='Markdown')

@bot.message_handler(commands=['errors'])
def cmd_errors(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return

    if IS_LOCAL or IS_WINDOWS:
        bot.reply_to(message, "⚠️ 로컬 환경에서는 콘솔 에러를 확인하세요.")
    else:
        error_logs = process_manager.get_logs(lines=20, error_only=True)

        if not error_logs or error_logs.strip() == "":
            bot.reply_to(message, "✅ 최근 에러가 없습니다.")
        else:
            if len(error_logs) > 4000:
                error_logs = error_logs[-4000:]
            
            bot.reply_to(message, f"🚨 최근 에러 로그:\n\n```\n{error_logs}\n```", parse_mode='Markdown')

@bot.message_handler(commands=['monitor'])
def cmd_monitor(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    if IS_LOCAL or IS_WINDOWS:
        bot.reply_to(message, "⚠️ 로컬 환경에서는 에러 모니터링을 사용할 수 없습니다.")
        return
    
    # 모니터링 토글
    if monitoring_active:
        stop_error_monitoring()
        bot.reply_to(message, "🔴 에러 모니터링이 비활성화되었습니다.")
    else:
        start_error_monitoring()
        bot.reply_to(message, "🟢 에러 모니터링이 활성화되었습니다.\n새로운 에러 발생 시 자동으로 알림을 받습니다.")

@bot.message_handler(commands=['update'])
def cmd_update(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return

    if IS_LOCAL or IS_WINDOWS:
        bot.reply_to(message, "⚠️ 로컬 환경에서는 git pull을 수동으로 실행하세요.")
    else:
        bot.reply_to(message, "🔄 업데이트 시작...")

        # Git pull
        result = run_command("git pull")
        
        # 의존성 업데이트
        pip_result = run_command("pip3 install -r requirements.txt")
        
        # 앱 재시작
        restart_result = process_manager.restart()
        
        # 에러 모니터링 재시작
        start_error_monitoring()

        update_msg = f"""✅ 업데이트 완료

📥 Git Pull:
{result[:500]}

📦 패키지 업데이트:
{pip_result[:300]}

🔄 재시작: {restart_result['message']}"""

        bot.reply_to(message, update_msg)

@bot.message_handler(commands=['ping'])
def cmd_ping(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    try:
        import requests
        
        # 로컬과 서버 환경에 따라 URL 변경
        url = 'http://localhost:5000/' if (IS_LOCAL or IS_WINDOWS) else 'http://localhost:5000/'
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            bot.reply_to(message, 
                f"✅ Flask API 정상\n"
                f"서비스: {data.get('service')}\n"
                f"버전: {data.get('version')}\n"
                f"상태: {data.get('status')}"
            )
        else:
            bot.reply_to(message, f"⚠️ API 응답 코드: {response.status_code}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ API 연결 실패\n{str(e)}")

@bot.message_handler(commands=['help'])
def cmd_help(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    help_text = """
🤖 FrameFlow Control Bot

📱 기본 제어:
/start - 서비스 시작
/stop - 서비스 중지
/restart - 서비스 재시작
/status - 상태 확인

📊 모니터링:
/logs - 최근 로그 (30줄)
/errors - 에러 로그만 보기
/monitor - 실시간 에러 알림 on/off
/ping - API 상태 확인

🔧 관리:
/update - Git 업데이트 + 재시작
/help - 도움말

🚨 자동 알림:
에러 발생 시 실시간 텔레그램 알림
    """
    bot.reply_to(message, help_text)

# 봇 시작 시 자동으로 에러 모니터링 활성화
def initialize_bot():
    """봇 초기화"""
    if not (IS_LOCAL or IS_WINDOWS):
        # 서버 환경에서만 자동 모니터링 시작
        if process_manager.is_running():
            start_error_monitoring()
            print("✅ 에러 모니터링이 자동으로 시작되었습니다.")

if __name__ == "__main__":
    # Windows 콘솔 인코딩 설정
    if IS_WINDOWS:
        import sys
        if sys.stdout.encoding != 'utf-8':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("🤖 FrameFlow Telegram Bot 시작...")
    print(f"👤 허용된 사용자 ID: {ALLOWED_USER_ID}")
    print(f"🖥️ 실행 환경: {'Windows (로컬)' if IS_WINDOWS else 'Linux (서버)'}")
    print("="*50)

    # 봇 초기화
    initialize_bot()

    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n\n🛑 봇이 종료되었습니다.")
        stop_error_monitoring()
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        stop_error_monitoring()