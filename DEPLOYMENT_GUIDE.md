# 🚀 FrameFlow 서버 배포 가이드

## 1️⃣ Git에 푸시 (로컬에서)

```bash
git add .
git commit -m "텔레그램 봇 제어 시스템 추가 - 자동 에러 알림 포함"
git push origin main
```

## 2️⃣ 서버에서 배포 (Vultr)

### SSH로 서버 접속
```bash
ssh root@your-server-ip
```

### 프로젝트 클론 또는 업데이트
```bash
# 처음 배포하는 경우
git clone https://github.com/your-username/frameflow-api.git
cd frameflow-api

# 이미 있는 경우 업데이트
cd frameflow-api
git pull origin main
```

### 자동 배포 실행
```bash
chmod +x deploy.sh
./deploy.sh
```

### 환경변수 설정
```bash
nano .env
```

다음 내용을 실제 값으로 수정:
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-actual-service-key

# GA4
GA4_PROPERTY_ID=488770841

# AI
ANTHROPIC_API_KEY=sk-ant-your-actual-key

# 텔레그램 (중요!)
TELEGRAM_BOT_TOKEN=your-actual-bot-token
TELEGRAM_USER_ID=your-actual-user-id

# 서버
ENVIRONMENT=production
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```

### GA4 서비스 계정 키 업로드
```bash
# credentials/service-account.json 파일을 서버에 업로드
# scp 또는 nano로 직접 생성
nano credentials/service-account.json
```

## 3️⃣ 텔레그램 봇 사용법

### 봇 시작 확인
배포 스크립트 실행 후 텔레그램에서 봇에게 메시지를 보내보세요:

```
/help
```

### Flask 앱 시작
```
/start
```

### 상태 확인
```
/status
```

### 로그 확인
```
/logs
```

## 4️⃣ 문제 해결

### 텔레그램 봇이 응답하지 않는 경우
```bash
# 봇 로그 확인
tail -f /tmp/frameflow_logs/telegram_bot.log

# 봇 재시작
./stop_server.sh
./deploy.sh
```

### Flask 앱이 시작되지 않는 경우
```bash
# 에러 로그 확인
tail -f /tmp/frameflow_error.log

# 수동으로 테스트
python3 app.py
```

### 전체 상태 확인
```bash
./server_status.sh
```

## 5️⃣ 주요 기능

✅ **텔레그램으로 서버 제어**
- `/start` - Flask 앱 시작
- `/stop` - Flask 앱 중지
- `/restart` - Flask 앱 재시작

✅ **실시간 에러 모니터링**
- 에러 발생 시 자동 텔레그램 알림
- 30초마다 에러 로그 체크
- 중복 알림 방지

✅ **원격 업데이트**
- `/update` - Git pull + 패키지 업데이트 + 재시작

✅ **로그 모니터링**
- `/logs` - 일반 로그
- `/errors` - 에러 로그만
- `/status` - 서버 상태

## 6️⃣ 보안 주의사항

🔒 **환경변수 보안**
- `.env` 파일은 절대 Git에 올리지 마세요
- 텔레그램 봇 토큰과 사용자 ID를 정확히 설정하세요

🔒 **서비스 계정 키**
- `credentials/service-account.json`은 Git에 올리지 마세요
- 파일 권한을 600으로 설정하세요: `chmod 600 credentials/service-account.json`

🔒 **방화벽 설정**
- 포트 5000은 내부에서만 접근 가능하도록 설정
- 필요시 nginx 리버스 프록시 사용

---

이제 텔레그램으로 서버를 완전히 제어할 수 있습니다! 🎉