# FrameFlow GA4 AI API v2.0

WordPress 사용자를 위한 GA4 데이터 분석 및 AI 챗봇 서비스 (모듈화 완료 버전)

## 📋 목차

- [주요 기능](#주요-기능)
- [v2.0 주요 개선사항](#v20-주요-개선사항)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 설정](#설치-및-설정)
- [API 문서](#api-문서)
- [데이터베이스 스키마](#데이터베이스-스키마)
- [자동화 기능](#자동화-기능)
- [배포](#배포)
- [로그 및 모니터링](#로그-및-모니터링)

---

## 🎯 주요 기능

### 1. 사용자 관리
- ✅ WordPress 사용자 통합 가입
- ✅ 사용자별 GA4 Property ID 관리
- ✅ 토큰 잔액 관리 및 충전
- ✅ AI 학습 컨텍스트 설정 (비즈니스 정보, KPI, 목표 등)

### 2. GA4 데이터 동기화
- ✅ **전체 동기화**: 지정된 기간의 전체 데이터 수집
- ✅ **증분 동기화**: 마지막 동기화 이후 데이터만 추가 (API 절약)
- ✅ **일일 자동 갱신**: 매일 새벽 자동으로 모든 사용자 데이터 업데이트
- ✅ 사용자별 Property ID 관리

### 3. AI 챗봇
- ✅ 사용자 데이터 기반 맞춤형 대화
- ✅ 대화 히스토리 저장 및 컨텍스트 유지
- ✅ 토큰 기반 사용량 관리
- ✅ 비즈니스 목표 기반 인사이트 제공

### 4. 자동화
- ✅ APScheduler를 통한 일일 데이터 갱신
- ✅ 실패 시 자동 재시도
- ✅ Telegram 알림 (성공/실패 리포트)

### 5. 로깅 및 모니터링
- ✅ 파일별 로그 관리 (app.log, error.log, scheduler.log, api.log)
- ✅ 자동 로그 로테이션
- ✅ 컬러 콘솔 출력

---

## 🆕 v2.0 주요 개선사항

### 1. **완전한 모듈화**
```
기존: 모든 코드가 app.py 하나에 집중
개선: 기능별로 명확하게 분리
  - api/ - API 엔드포인트
  - services/ - 비즈니스 로직
  - database/ - DB 작업
  - utils/ - 유틸리티
```

### 2. **통합 설정 관리**
```python
# config/settings.py
# 모든 환경변수를 한 곳에서 관리
# 개발/프로덕션/테스트 환경 분리
```

### 3. **체계적인 로깅**
```
logs/
├── app.log        # 일반 로그
├── error.log      # 에러만
├── scheduler.log  # 스케줄러 작업
└── api.log        # API 요청
```

### 4. **증분 업데이트**
```
기존: 매번 전체 데이터 다시 가져옴 (API 낭비)
개선: 마지막 날짜 이후 데이터만 추가
```

### 5. **일일 자동 갱신**
```
매일 새벽 3시 자동으로:
- 모든 사용자 GA4 데이터 증분 업데이트
- Telegram으로 결과 알림
- 실패한 사용자 재시도
```

---

## 📁 프로젝트 구조

```
frameflow-api/
├── app_new.py                     # 🆕 메인 애플리케이션 (v2.0)
├── app.py                         # 기존 버전 (호환성 유지)
│
├── config/                        # ⚙️ 설정
│   ├── __init__.py
│   ├── settings.py               # 통합 설정 관리
│   └── ga4_config.py             # GA4 설정 (레거시)
│
├── api/                          # 🌐 API 엔드포인트
│   ├── __init__.py
│   ├── users.py                  # 사용자 관리 API
│   ├── ga4.py                    # GA4 동기화 API
│   └── chat.py                   # AI 챗봇 API
│
├── services/                     # 💼 비즈니스 로직
│   ├── __init__.py
│   ├── user_service.py           # 사용자 관리
│   ├── ga4_service.py            # GA4 데이터 처리 + 증분 업데이트
│   ├── chat_service.py           # AI 챗봇
│   └── scheduler_service.py      # 🆕 자동 스케줄러
│
├── database/                     # 🗄️ 데이터베이스
│   ├── __init__.py
│   └── supabase_client.py        # Supabase 클라이언트
│
├── utils/                        # 🛠️ 유틸리티
│   ├── __init__.py
│   └── logger.py                 # 🆕 로깅 시스템
│
├── integrations/                 # 🔌 외부 통합
│   ├── __init__.py
│   ├── ga4_extractor_template.py # GA4 데이터 추출
│   └── telegram_bot.py           # Telegram 봇
│
├── migrations/                   # 📝 DB 마이그레이션
│   └── 001_create_ga4_accounts.sql
│
├── logs/                         # 📊 로그 파일 (자동 생성)
├── credentials/                  # 🔐 GA4 인증 파일
├── scripts/                      # 📜 배포 스크립트
│
├── .env                          # 환경 변수 (비공개)
├── .env.example                  # 🆕 환경 변수 템플릿
├── requirements.txt              # 🆕 업데이트된 의존성
├── README.md                     # 기존 문서
├── README_v2.md                  # 🆕 v2.0 문서 (이 파일)
└── PROJECT_STRUCTURE.md          # 🆕 상세 구조 문서
```

---

## 🚀 설치 및 설정

### 1. 요구사항
- Python 3.8+
- Supabase 계정
- Claude API 키
- GA4 서비스 계정 인증 파일

### 2. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd frameflow-api

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**.env 필수 설정:**
```env
# Flask
FLASK_ENV=development
DEBUG=True
HOST=0.0.0.0
PORT=5000

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Claude AI
ANTHROPIC_API_KEY=sk-ant-xxxxx
CLAUDE_MODEL=claude-3-haiku-20240307

# GA4
GA4_DEFAULT_PROPERTY_ID=488770841
GA4_CREDENTIALS_PATH=credentials/ga4-credentials.json

# 스케줄러
SCHEDULER_ENABLED=True
DAILY_SYNC_TIME=03:00

# Telegram (선택)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ADMIN_CHAT_ID=your-chat-id
```

### 4. 데이터베이스 설정

Supabase SQL Editor에서 실행:

```sql
-- migrations/001_create_ga4_accounts.sql 내용 복사해서 실행
```

### 5. 서버 실행

```bash
# v2.0 서버 실행
python app_new.py

# 기존 서버 (호환성)
python app.py
```

---

## 📚 API 문서

### 기본 URL
```
http://your-server:5000
```

### 🆕 v2.0 API 구조
```
/api/user/*      - 사용자 관리
/api/ga4/*       - GA4 데이터
/api/chat/*      - AI 챗봇
```

### 1. 사용자 관리 (/api/user)

#### 사용자 등록
```http
POST /api/user/register

{
  "wp_user_id": 123,
  "email": "user@example.com",
  "ga4_property_id": "488770841",
  "token_balance": 10000
}
```

#### 프로필 조회
```http
GET /api/user/profile/{user_id}
```

#### AI 컨텍스트 설정 (마이페이지 기능)
```http
PUT /api/user/context/{user_id}

{
  "business_type": "쇼핑몰",
  "kpi": ["매출", "전환율", "ROAS"],
  "goals": "월 매출 1000만원 달성",
  "target_audience": "20-30대 여성",
  "additional_info": "프리미엄 화장품 판매"
}
```

#### 토큰 충전
```http
POST /api/user/tokens/{user_id}/charge

{
  "amount": 5000,
  "payment_method": "credit_card"
}
```

#### 토큰 잔액 조회
```http
GET /api/user/tokens/{user_id}
```

### 2. GA4 데이터 (/api/ga4)

#### 🆕 증분 동기화 (권장)
```http
POST /api/ga4/sync/{user_id}/incremental

# 마지막 동기화 이후 데이터만 추가
# API 호출 최소화
```

#### 전체 동기화
```http
POST /api/ga4/sync/{user_id}

{
  "days": 30  # 선택적
}
```

#### 데이터 요약 조회
```http
GET /api/ga4/summary/{user_id}
```

#### Property ID 변경
```http
PUT /api/ga4/property/{user_id}

{
  "property_id": "123456789"
}
```

### 3. AI 챗봇 (/api/chat)

#### 질문하기
```http
POST /api/chat/{user_id}

{
  "question": "어제 방문자 수는?",
  "include_history": true  # 대화 히스토리 포함
}
```

#### 대화 기록 조회
```http
GET /api/chat/history/{user_id}?limit=20
```

---

## 🗄️ 데이터베이스 스키마

### 🆕 주요 테이블

#### users
```sql
id, wp_user_id, email, token_balance, plan,
user_context (JSONB),  -- AI 학습 정보
created_at, updated_at
```

#### 🆕 ga4_accounts
```sql
id, user_id, property_id, credentials, is_active, created_at
-- 사용자별 GA4 계정 정보
```

#### ga4_data (날짜별 저장으로 변경)
```sql
id, user_id,
date (DATE),  -- 날짜별 저장
raw_data (JSONB), created_at
```

#### chat_history
```sql
id, user_id, question, answer, tokens_used, created_at
```

#### 🆕 token_transactions
```sql
id, user_id, amount, transaction_type, description, created_at
-- 토큰 거래 내역 추적
```

자세한 스키마는 `migrations/` 폴더 참고

---

## 🔄 자동화 기능

### 일일 자동 갱신

매일 새벽 3시 (설정 가능):
1. 모든 활성 사용자 조회
2. 각 사용자별 증분 동기화 실행
3. 성공/실패 집계
4. Telegram으로 결과 알림

**Telegram 알림 예시:**
```
📊 일일 GA4 동기화 완료

✅ 성공: 15명
❌ 실패: 1명
📈 추가된 데이터: 15일
⏱️ 소요시간: 23.45초
```

### 수동 동기화
```http
POST /api/ga4/sync/{user_id}/incremental
```

---

## 🔄 배포

### Vultr 서버 배포

```bash
# 1. 서버 접속
ssh root@your-server-ip

# 2. 저장소 클론
git clone <repository-url>
cd frameflow-api

# 3. 환경 설정
cp .env.example .env
nano .env

# 4. 패키지 설치
pip install -r requirements.txt

# 5. 데이터베이스 마이그레이션
# Supabase SQL Editor에서 실행

# 6. 서버 실행
python app_new.py

# 또는 백그라운드 실행
nohup python app_new.py > logs/app.log 2>&1 &
```

---

## 📊 로그 및 모니터링

### 로그 파일
```
logs/
├── app.log        # 일반 로그
├── error.log      # 에러만
├── scheduler.log  # 스케줄러 작업
└── api.log        # API 요청
```

### 로그 확인
```bash
# 실시간 로그
tail -f logs/app.log

# 에러만 확인
tail -f logs/error.log

# 스케줄러 확인
tail -f logs/scheduler.log
```

### 로그 레벨
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## 🛠️ 마이그레이션 가이드

### 기존 버전에서 v2.0으로

```bash
# 1. 백업
cp -r frameflow-api frameflow-api-backup

# 2. 새 코드 가져오기
git pull

# 3. 새 패키지 설치
pip install -r requirements.txt

# 4. 환경변수 업데이트
# .env.example 참고해서 .env 업데이트

# 5. 데이터베이스 마이그레이션
# migrations/001_create_ga4_accounts.sql 실행

# 6. 새 서버 실행
python app_new.py
```

### 기존 API 호환성
```
기존 엔드포인트는 app.py에서 계속 사용 가능
새 기능은 app_new.py 사용 권장
```

---

## 💡 사용 시나리오

### 1. 사용자 등록 및 설정
```
1. WordPress에서 회원가입
2. /api/user/register로 FrameFlow 등록
3. 마이페이지에서 AI 컨텍스트 설정
4. Property ID 등록 (또는 관리자에게 요청)
```

### 2. 데이터 확인
```
1. 버튼 클릭 → /api/ga4/sync/{user_id}/incremental
2. /api/ga4/summary/{user_id}로 요약 조회
3. 챗봇으로 질문
```

### 3. 자동 갱신
```
매일 새벽 자동으로 모든 사용자 데이터 업데이트
별도 작업 불필요
```

---

## 🔐 보안

- `.env` 파일은 절대 Git에 올리지 마세요
- `credentials/` 폴더도 `.gitignore`에 포함
- Telegram 봇은 지정된 사용자만 접근 가능
- API 키는 환경변수로 관리

---

## 📞 지원

문제 발생 시:
1. `logs/error.log` 확인
2. Telegram 봇으로 관리자에게 알림
3. GitHub Issues 등록

---

## 🎯 로드맵

- [ ] 리포트 생성 기능 (PDF/HTML)
- [ ] 웹 대시보드
- [ ] 다중 Property 지원
- [ ] 실시간 데이터 스트리밍
- [ ] API 사용량 통계

---

## 📄 라이선스

MIT License

---

**FrameFlow v2.0 - 모듈화되고 확장 가능한 GA4 AI 분석 플랫폼**
