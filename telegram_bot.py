import telebot
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram 설정
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

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

@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    run_command("sudo systemctl start frameflow")
    bot.reply_to(message, "✅ FrameFlow 시작됨")

@bot.message_handler(commands=['stop'])
def cmd_stop(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    run_command("sudo systemctl stop frameflow")
    bot.reply_to(message, "⏹️ FrameFlow 중지됨")

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    run_command("sudo systemctl restart frameflow")
    bot.reply_to(message, "🔄 FrameFlow 재시작됨")

@bot.message_handler(commands=['status'])
def cmd_status(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    status = run_command("systemctl is-active frameflow")
    
    if "active" in status:
        bot.reply_to(message, "🟢 FrameFlow 실행 중")
    else:
        bot.reply_to(message, "🔴 FrameFlow 중지됨")

@bot.message_handler(commands=['logs'])
def cmd_logs(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    logs = run_command("sudo journalctl -u frameflow -n 20 --no-pager")
    
    if len(logs) > 4000:
        logs = logs[-4000:]
    
    bot.reply_to(message, f"📋 최근 로그:\n\n```\n{logs}\n```", parse_mode='Markdown')

@bot.message_handler(commands=['update'])
def cmd_update(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    bot.reply_to(message, "🔄 업데이트 시작...")
    
    result = run_command("cd /home/berryeasy/htdocs/berryeasy.co.kr/flameflow-api && git pull")
    run_command("sudo systemctl restart frameflow")
    
    bot.reply_to(message, f"✅ 업데이트 완료\n\n{result}")

@bot.message_handler(commands=['ping'])
def cmd_ping(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    try:
        import requests
        response = requests.get('http://localhost:5000/', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            bot.reply_to(message, 
                f"✅ Flask API 정상\n"
                f"서비스: {data.get('service')}\n"
                f"버전: {data.get('version')}"
            )
    except Exception as e:
        bot.reply_to(message, f"❌ API 연결 실패\n{str(e)}")

@bot.message_handler(commands=['help'])
def cmd_help(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    help_text = """
🤖 BerryEasy Control Bot

/start - 서비스 시작
/stop - 서비스 중지
/restart - 서비스 재시작
/status - 상태 확인
/logs - 최근 로그
/update - Git 업데이트 + 재시작
/ping - API 상태 확인
/help - 도움말
    """
    bot.reply_to(message, help_text)

print("🤖 Telegram Bot 시작...")
print(f"👤 허용된 사용자 ID: {ALLOWED_USER_ID}")
bot.polling()