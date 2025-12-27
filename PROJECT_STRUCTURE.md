# FrameFlow API 프로젝트 구조

## 📁 디렉토리 구조
```
frameflow-api/
├── app.py                          # 메인 Flask 애플리케이션 (엔트리포인트)
├── config/                         # 설정 파일
│   ├── __init__.py
│   ├── settings.py                 # 전역 설정
│   ├── ga4_config.py              # GA4 관련 설정
│   └── logging_config.py          # 로깅 설정
├── api/                           # API 라우터 (엔드포인트)
│   ├── __init__.py
│   ├── users.py                   # 사용자 관리 API
│   ├── ga4.py                     # GA4 데이터 동기화 API
│   ├── chat.py                    # AI 챗봇 API
│   ├── reports.py                 # 리포트 생성 API
│   └── payments.py                # 결제/토큰 관리 API
├── services/                      # 비즈니스 로직 (서비스 레이어)
│   ├── __init__.py
│   ├── user_service.py            # 사용자 관련 비즈니스 로직
│   ├── ga4_service.py             # GA4 데이터 처리
│   ├── chat_service.py            # AI 챗봇 로직
│   ├── report_service.py          # 리포트 생성 로직
│   └── scheduler_service.py       # 스케줄러 (일일 갱신)
├── models/                        # 데이터 모델
│   ├── __init__.py
│   ├── user.py                    # User 모델
│   ├── ga4_account.py             # GA4Account 모델
│   └── chat_history.py            # ChatHistory 모델
├── database/                      # 데이터베이스 클라이언트
│   ├── __init__.py
│   └── supabase_client.py         # Supabase 클라이언트
├── utils/                         # 유틸리티 함수
│   ├── __init__.py
│   ├── logger.py                  # 로깅 유틸
│   ├── validators.py              # 데이터 검증
│   └── formatters.py              # 데이터 포맷팅
├── integrations/                  # 외부 통합
│   ├── __init__.py
│   ├── ga4_extractor.py           # GA4 데이터 추출
│   ├── claude_client.py           # Claude AI 클라이언트
│   └── telegram_bot.py            # Telegram 봇
├── migrations/                    # 데이터베이스 마이그레이션
│   └── 001_create_ga4_accounts.sql
├── scripts/                       # 관리 스크립트
│   ├── deploy.sh
│   ├── check_bot.sh
│   └── stop_server.sh
├── logs/                          # 로그 파일
│   ├── app.log
│   ├── error.log
│   └── scheduler.log
├── credentials/                   # GA4 인증 파일
├── .env                          # 환경 변수
├── requirements.txt              # Python 패키지
└── README.md                     # 프로젝트 문서
```

## 🔄 데이터 흐름

### 1. 사용자 등록
```
WordPress → /api/user/register → UserService → Supabase
```

### 2. GA4 데이터 동기화
```
사용자 요청 → /api/ga4/sync-user → GA4Service → GA4Extractor → Supabase
스케줄러 → (매일 자동) → GA4Service (증분 업데이트)
```

### 3. AI 챗봇
```
사용자 질문 → /api/chat → ChatService → Claude API → Supabase (히스토리 저장)
```

### 4. 리포트 생성
```
사용자 요청 → /api/reports/generate → ReportService → Supabase → PDF/HTML
```

## 🎯 주요 개선 사항

### 1. **모듈화**
- API 라우터와 비즈니스 로직 분리
- 각 기능별로 독립적인 모듈
- 재사용 가능한 서비스 레이어

### 2. **로깅**
- 파일별 로깅 (app.log, error.log, scheduler.log)
- 레벨별 로깅 (DEBUG, INFO, WARNING, ERROR)
- 자동 로그 로테이션

### 3. **에러 핸들링**
- 중앙집중식 에러 처리
- 사용자 친화적인 에러 메시지
- 자동 에러 알림 (Telegram)

### 4. **스케줄러**
- APScheduler를 사용한 자동 데이터 갱신
- 증분 업데이트 (이전 날짜만 추가)
- 실패 시 재시도 로직

### 5. **보안**
- API 키 환경변수 관리
- 사용자 인증/권한 검증
- SQL Injection 방지

## 📊 데이터베이스 스키마

### users
- id (PK)
- wp_user_id (Unique)
- email
- token_balance
- plan (free/beta/pro)
- user_context (JSONB) - AI 사전 학습 정보
- created_at, updated_at

### ga4_accounts
- id (PK)
- user_id (FK → users)
- property_id
- credentials
- is_active
- created_at, updated_at

### ga4_data
- id (PK)
- user_id (FK → users)
- date (날짜별 저장)
- raw_data (JSONB)
- created_at

### chat_history
- id (PK)
- user_id (FK → users)
- question
- answer
- tokens_used
- created_at

### reports
- id (PK)
- user_id (FK → users)
- report_type
- parameters (JSONB)
- file_path
- created_at

### token_transactions
- id (PK)
- user_id (FK → users)
- amount
- transaction_type (charge/consume/refund)
- description
- created_at

## 🚀 배포 전략

1. **개발 환경**: 로컬 Flask 서버
2. **스테이징**: Vultr 테스트 서버
3. **프로덕션**: Vultr 프로덕션 서버
4. **모니터링**: Telegram 알림 + 로그 파일
