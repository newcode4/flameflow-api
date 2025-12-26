# FrameFlow GA4 API

GA4 데이터를 AI로 분석하는 API 서버

## 🚀 설치 방법

### 1. 저장소 클론
\`\`\`bash
git clone https://github.com/your-username/frameflow-api.git
cd frameflow-api
\`\`\`

### 2. 패키지 설치
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 3. 환경변수 설정
\`\`\`bash
cp .env.example .env
# .env 파일을 열어서 실제 값 입력
\`\`\`

### 4. GA4 서비스 계정 키 추가
- Google Cloud에서 서비스 계정 JSON 다운로드
- `credentials/service-account.json` 으로 저장

### 5. 서버 실행
\`\`\`bash
python app.py
\`\`\`

## 📡 API 엔드포인트

### POST /api/chat
AI 챗봇 질문
\`\`\`json
{
  "user_id": 1,
  "question": "어제 방문자 몇 명?"
}
\`\`\`

### POST /api/ga4/sync
GA4 데이터 동기화
\`\`\`json
{
  "user_id": 1,
  "days": 30
}
\`\`\`

## 🔒 보안

- `.env` 파일은 절대 Git에 올리지 마세요
- `service-account.json`도 Git에 올리지 마세요
- 프로덕션에선 환경변수로 관리하세요