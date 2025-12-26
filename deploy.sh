#!/bin/bash

# FrameFlow 서버 배포 스크립트

echo "🚀 FrameFlow 서버 배포 시작..."

# 1. 패키지 업데이트
echo "📦 패키지 설치 중..."
pip3 install -r requirements.txt

# 2. 실행 권한 부여
chmod +x process_manager.py
chmod +x telegram_bot.py

# 3. 로그 디렉토리 생성
mkdir -p /tmp/frameflow_logs

# 4. 환경변수 파일 체크
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 참고하여 생성하세요."
    cp .env.example .env
    echo "📝 .env 파일을 생성했습니다. 실제 값으로 수정하세요."
fi

# 5. 서비스 계정 키 체크
if [ ! -f "credentials/service-account.json" ]; then
    echo "⚠️  GA4 서비스 계정 키가 없습니다."
    echo "📁 credentials/service-account.json 파일을 추가하세요."
fi

# 6. 텔레그램 봇을 백그라운드에서 실행
echo "🤖 텔레그램 봇 시작..."
nohup python3 telegram_bot.py > /tmp/frameflow_logs/telegram_bot.log 2>&1 &
echo $! > /tmp/telegram_bot.pid

echo "✅ 배포 완료!"
echo ""
echo "📱 텔레그램 봇이 백그라운드에서 실행 중입니다."
echo "💬 텔레그램에서 /start 명령으로 Flask 앱을 시작하세요."
echo ""
echo "📊 상태 확인:"
echo "  - 텔레그램 봇 로그: tail -f /tmp/frameflow_logs/telegram_bot.log"
echo "  - Flask 앱 로그: tail -f /tmp/frameflow_app.log"
echo "  - 에러 로그: tail -f /tmp/frameflow_error.log"
echo ""
echo "🛑 중지 방법:"
echo "  - 텔레그램 봇: kill \$(cat /tmp/telegram_bot.pid)"
echo "  - Flask 앱: 텔레그램에서 /stop 명령 사용"