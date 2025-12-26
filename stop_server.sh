#!/bin/bash

# FrameFlow 서버 중지 스크립트

echo "🛑 FrameFlow 서버 중지 중..."

# 1. 텔레그램 봇 중지 (여러 방법으로)
echo "🤖 텔레그램 봇 중지..."

# PID 파일로 중지
if [ -f "/tmp/telegram_bot.pid" ]; then
    PID=$(cat /tmp/telegram_bot.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "   ✅ 텔레그램 봇 중지됨 (PID: $PID)"
    else
        echo "   ⚠️ PID 파일은 있지만 프로세스가 없습니다."
    fi
    rm -f /tmp/telegram_bot.pid
else
    echo "   ⚠️ PID 파일을 찾을 수 없습니다."
fi

# 프로세스 이름으로 강제 종료
pkill -f telegram_bot.py
echo "   🔄 telegram_bot.py 프로세스 강제 종료 시도"

# 2. Flask 앱 중지
echo "🌐 Flask 앱 중지..."
if [ -f "process_manager.py" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
        python process_manager.py stop
    else
        python3 process_manager.py stop
    fi
else
    echo "   ⚠️ process_manager.py를 찾을 수 없습니다."
fi

# 3. 임시 파일 정리
echo "🧹 임시 파일 정리..."
rm -f /tmp/frameflow_*.pid
rm -f /tmp/frameflow_last_check.txt
rm -f /tmp/telegram_bot.pid

echo "✅ 모든 서비스가 중지되었습니다."

# 4. 남은 프로세스 확인
echo ""
echo "📊 남은 프로세스 확인:"
REMAINING=$(ps aux | grep -E "(telegram_bot|app\.py)" | grep -v grep)
if [ -z "$REMAINING" ]; then
    echo "   ✅ 관련 프로세스가 모두 정리되었습니다."
else
    echo "   ⚠️ 남은 프로세스:"
    echo "$REMAINING"
    echo ""
    echo "   수동 정리가 필요할 수 있습니다:"
    echo "   pkill -9 -f telegram_bot.py"
    echo "   pkill -9 -f app.py"
fi