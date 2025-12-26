#!/bin/bash

# FrameFlow 서버 배포 스크립트

echo "🚀 FrameFlow 서버 배포 시작..."

# 1. 가상환경 생성 및 활성화
echo "🐍 Python 가상환경 설정..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
fi

source venv/bin/activate
echo "✅ 가상환경 활성화 완료"

# 2. pip 업그레이드 및 패키지 설치
echo "📦 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. 실행 권한 부여
chmod +x process_manager.py
chmod +x telegram_bot.py

# 4. 로그 디렉토리 생성
mkdir -p /tmp/frameflow_logs

# 5. 환경변수 파일 체크
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 참고하여 생성하세요."
    cp .env.example .env
    echo "📝 .env 파일을 생성했습니다. 실제 값으로 수정하세요."
fi

# 6. 서비스 계정 키 체크
if [ ! -f "credentials/service-account.json" ]; then
    echo "⚠️  GA4 서비스 계정 키가 없습니다."
    echo "📁 credentials/service-account.json 파일을 추가하세요."
fi

# 7. 기존 봇 프로세스 정리
echo "🧹 기존 프로세스 정리..."
pkill -f telegram_bot.py 2>/dev/null || true
sleep 2

# 8. 가상환경 경로 저장
echo "$(pwd)/venv/bin/python" > /tmp/frameflow_python_path

# 9. 텔레그램 봇을 백그라운드에서 실행 (가상환경 사용)
echo "🤖 텔레그램 봇 시작..."

# 중복 실행 방지 체크
if [ -f "/tmp/telegram_bot.pid" ]; then
    OLD_PID=$(cat /tmp/telegram_bot.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️ 기존 봇이 실행 중입니다. 종료 후 재시작..."
        kill $OLD_PID 2>/dev/null || true
        sleep 3
    fi
fi

nohup ./venv/bin/python telegram_bot.py > /tmp/frameflow_logs/telegram_bot.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > /tmp/telegram_bot.pid

# 시작 확인
sleep 2
if ps -p $NEW_PID > /dev/null; then
    echo "✅ 텔레그램 봇이 성공적으로 시작되었습니다 (PID: $NEW_PID)"
else
    echo "❌ 텔레그램 봇 시작에 실패했습니다"
    echo "로그 확인: tail -f /tmp/frameflow_logs/telegram_bot.log"
fi

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
echo ""
echo "🔧 수동 실행 (가상환경):"
echo "  source venv/bin/activate"
echo "  python telegram_bot.py"