#!/bin/bash

# FrameFlow 서버 상태 확인 스크립트

echo "📊 FrameFlow 서버 상태"
echo "========================"

# 1. 텔레그램 봇 상태
echo "🤖 텔레그램 봇:"
if [ -f "/tmp/telegram_bot.pid" ]; then
    PID=$(cat /tmp/telegram_bot.pid)
    if ps -p $PID > /dev/null; then
        echo "  ✅ 실행 중 (PID: $PID)"
    else
        echo "  ❌ 중지됨 (PID 파일 존재하지만 프로세스 없음)"
    fi
else
    echo "  ❌ 중지됨 (PID 파일 없음)"
fi

# 2. Flask 앱 상태
echo ""
echo "🌐 Flask 앱:"
python3 process_manager.py status

# 3. 로그 파일 상태
echo ""
echo "📋 로그 파일:"
if [ -f "/tmp/frameflow_app.log" ]; then
    SIZE=$(du -h /tmp/frameflow_app.log | cut -f1)
    echo "  📄 앱 로그: $SIZE"
else
    echo "  📄 앱 로그: 없음"
fi

if [ -f "/tmp/frameflow_error.log" ]; then
    SIZE=$(du -h /tmp/frameflow_error.log | cut -f1)
    LINES=$(wc -l < /tmp/frameflow_error.log)
    echo "  🚨 에러 로그: $SIZE ($LINES 줄)"
else
    echo "  🚨 에러 로그: 없음"
fi

if [ -f "/tmp/frameflow_logs/telegram_bot.log" ]; then
    SIZE=$(du -h /tmp/frameflow_logs/telegram_bot.log | cut -f1)
    echo "  🤖 봇 로그: $SIZE"
else
    echo "  🤖 봇 로그: 없음"
fi

# 4. 포트 사용 상태
echo ""
echo "🔌 포트 5000 상태:"
if netstat -tuln | grep -q ":5000 "; then
    echo "  ✅ 포트 5000 사용 중"
else
    echo "  ❌ 포트 5000 사용 안함"
fi

# 5. 디스크 사용량
echo ""
echo "💾 디스크 사용량:"
df -h . | tail -1 | awk '{print "  사용량: " $3 "/" $2 " (" $5 ")"}'

echo ""
echo "========================"