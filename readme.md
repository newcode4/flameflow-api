# FrameFlow GA4 API

GA4 데이터를 AI로 분석하는 API 서버 + 텔레그램 봇 제어 시스템

## 🚀 로컬 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/frameflow-api.git
cd frameflow-api
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어서 실제 값 입력
```

### 4. GA4 서비스 계정 키 추가
- Google Cloud에서 서비스 계정 JSON 다운로드
- `credentials/service-account.json` 으로 저장

### 5. 로컬 서버 실행
```bash
python app.py
```

## 🖥️ 서버 배포 (Vultr/Ubuntu)

### 1. 서버에서 저장소 클론
```bash
git clone https://github.com/your-username/frameflow-api.git
cd frameflow-api
```

### 2. 자동 배포 스크립트 실행
```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. 환경변수 설정
```bash
nano .env
# 실제 값으로 수정 후 저장
```

### 4. GA4 서비스 계정 키 업로드
```bash
# credentials/service-account.json 파일 업로드
```

### 5. 텔레그램에서 서버 제어
- 텔레그램 봇에게 `/start` 명령으로 Flask 앱 시작
- `/status`로 상태 확인
- `/logs`로 로그 확인

## 📱 텔레그램 봇 명령어

### 기본 제어
- `/start` - Flask 서버 시작
- `/stop` - Flask 서버 중지  
- `/restart` - Flask 서버 재시작
- `/status` - 서버 상태 확인

### 모니터링
- `/logs` - 최근 로그 보기 (30줄)
- `/errors` - 에러 로그만 보기
- `/monitor` - 실시간 에러 알림 on/off
- `/ping` - API 응답 테스트

### 관리
- `/update` - Git pull + 패키지 업데이트 + 재시작
- `/help` - 도움말

### 🚨 자동 에러 알림
- Flask 앱에서 에러 발생 시 자동으로 텔레그램 알림
- 30초마다 에러 로그 모니터링
- 새로운 에러만 알림 (중복 방지)

## 📡 API 엔드포인트

### POST /api/chat
AI 챗봇 질문
```json
{
  "user_id": 1,
  "question": "어제 방문자 몇 명?"
}
```

### POST /api/ga4/sync
GA4 데이터 동기화
```json
{
  "user_id": 1,
  "days": 30
}
```

## 🛠️ 서버 관리 스크립트

### 배포
```bash
./deploy.sh          # 서버 배포 및 텔레그램 봇 시작
```

### 상태 확인
```bash
./server_status.sh   # 전체 서버 상태 확인
```

### 중지
```bash
./stop_server.sh     # 모든 서비스 중지
```

### 수동 제어
```bash
# Flask 앱만 제어
python3 process_manager.py start
python3 process_manager.py stop
python3 process_manager.py status
python3 process_manager.py logs

# 텔레그램 봇 수동 실행
python3 telegram_bot.py
```

## 📁 로그 파일 위치

- Flask 앱 로그: `/tmp/frameflow_app.log`
- 에러 로그: `/tmp/frameflow_error.log`  
- 텔레그램 봇 로그: `/tmp/frameflow_logs/telegram_bot.log`

## 🔒 보안

- `.env` 파일은 절대 Git에 올리지 마세요
- `service-account.json`도 Git에 올리지 마세요
- 텔레그램 봇은 지정된 사용자 ID만 접근 가능
- 프로덕션에선 환경변수로 관리하세요

## 🔧 환경변수 설정

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# GA4
GA4_PROPERTY_ID=your-property-id

# AI
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 텔레그램
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_USER_ID=your-user-id

# 서버
ENVIRONMENT=production
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```