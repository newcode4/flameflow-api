#!/bin/bash

echo "🔍 FrameFlow 봇 상태 확인"
echo "========================"

# 1. 텔레그램 봇 프로세스 확인
echo "🤖 텔레그램 봇 프로세스:"
BOT_PROCESSES=$(ps aux | grep telegram_bot.py | grep -v grep)
if [ -z "$BOT_PROCESSES" ]; then
    echo "   ❌ 실행 중인 봇이 없습니다."
else
    echo "   ✅ 실행 중:"
    echo "$BOT_PROCESSES" | while read line; do
        echo "      $line"
    done
fi

# 2. PID 파일 확인
echo ""
echo "📄 PID 파일:"
if [ -f "/tmp/telegram_bot.pid" ]; then
    PID=$(cat /tmp/telegram_bot.pid)
    if ps -p $PID > /dev/null; then
        echo "   ✅ PID 파일 존재하고 프로세스 실행 중 (PID: $PID)"
    else
        echo "   ⚠️ PID 파일은 있지만 프로세스가 없음 (PID: $PID)"
    fi
else
    echo "   ❌ PID 파일이 없습니다."
fi

# 3. Flask 앱 상태
echo ""
echo "🌐 Flask 앱 상태:"
if [ -f "process_manager.py" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
        python process_manager.py status
    else
        python3 process_manager.py status
    fi
else
    echo "   ⚠️ process_manager.py를 찾을 수 없습니다."
fi

# 4. 포트 사용 상태
echo ""
echo "🔌 포트 상태:"
if netstat -tuln 2>/dev/null | grep -q ":5000 "; then
    echo "   ✅ 포트 5000 사용 중"
else
    echo "   ❌ 포트 5000 사용 안함"
fi

# 5. 최근 로그 (마지막 5줄)
echo ""
echo "📋 최근 봇 로그 (마지막 5줄):"
if [ -f "/tmp/frameflow_logs/telegram_bot.log" ]; then
    tail -5 /tmp/frameflow_logs/telegram_bot.log
else
    echo "   ❌ 로그 파일이 없습니다."
fi

echo ""
echo "========================"