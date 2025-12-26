#!/bin/bash

# FrameFlow 서버 중지 스크립트

echo "🛑 FrameFlow 서버 중지 중..."

# 1. 텔레그램 봇 중지
if [ -f "/tmp/telegram_bot.pid" ]; then
    PID=$(cat /tmp/telegram_bot.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "🤖 텔레그램 봇 중지됨 (PID: $PID)"
    else
        echo "🤖 텔레그램 봇이 이미 중지되어 있습니다."
    fi
    rm -f /tmp/telegram_bot.pid
else
    echo "🤖 텔레그램 봇 PID 파일을 찾을 수 없습니다."
fi

# 2. Flask 앱 중지
python3 process_manager.py stop

# 3. 임시 파일 정리
rm -f /tmp/frameflow_*.pid
rm -f /tmp/frameflow_last_check.txt

echo "✅ 모든 서비스가 중지되었습니다."