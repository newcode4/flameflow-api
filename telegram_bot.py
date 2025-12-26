import telebot
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram 설정
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['ping'])
def cmd_ping(message):
    """API 서버 상태 확인"""
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    try:
        import requests
        
        # 로컬 Flask 확인
        response = requests.get('http://localhost:5000/', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            bot.reply_to(message, 
                f"✅ 로컬 Flask API 정상\n"
                f"서비스: {data.get('service')}\n"
                f"상태: {data.get('status')}\n"
                f"버전: {data.get('version')}"
            )
        else:
            bot.reply_to(message, f"⚠️ 응답 코드: {response.status_code}")
    
    except Exception as e:
        bot.reply_to(message, f"❌ Flask API 연결 실패\n{str(e)}")

@bot.message_handler(commands=['test'])
def cmd_test(message):
    """챗봇 테스트"""
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    try:
        import requests
        
        response = requests.post('http://localhost:5000/api/chat', 
            json={
                "user_id": 1,
                "question": "활성 사용자 몇 명?"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            bot.reply_to(message, 
                f"💬 AI 답변:\n\n{data['answer']}\n\n"
                f"토큰 사용: {data['tokens_used']}\n"
                f"잔액: {data['remaining_balance']}"
            )
        else:
            bot.reply_to(message, f"❌ 에러: {response.text}")
    
    except Exception as e:
        bot.reply_to(message, f"❌ 챗봇 호출 실패\n{str(e)}")

@bot.message_handler(commands=['help'])
def cmd_help(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ 권한 없음")
        return
    
    help_text = """
🤖 BerryEasy Bot (로컬 테스트)

/ping - Flask API 상태 확인
/test - AI 챗봇 테스트
/help - 도움말

ℹ️ 로컬 테스트 모드입니다.
Flask 서버가 실행 중이어야 합니다.
    """
    bot.reply_to(message, help_text)

print("🤖 Telegram Bot 시작...")
print(f"👤 허용된 사용자 ID: {ALLOWED_USER_ID}")
print("💡 사용 가능 명령: /ping, /test, /help")
bot.polling()