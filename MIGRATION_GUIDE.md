# FrameFlow v1.0 → v2.0 마이그레이션 가이드

## 📌 개요

이 문서는 기존 FrameFlow API를 v2.0 모듈화 버전으로 업그레이드하는 방법을 안내합니다.

---

## 🎯 v2.0 주요 변경사항

### 1. 파일 구조 변경
```
기존: app.py 하나에 모든 코드
v2.0: 모듈별로 분리
  ├── api/          # API 엔드포인트
  ├── services/     # 비즈니스 로직
  ├── database/     # DB 작업
  ├── config/       # 설정
  └── utils/        # 유틸리티
```

### 2. 새로운 기능
- ✅ 증분 데이터 동기화
- ✅ 일일 자동 갱신 스케줄러
- ✅ 체계적인 로깅 시스템
- ✅ 사용자별 AI 컨텍스트
- ✅ 토큰 거래 내역 추적

### 3. 데이터베이스 변경
- ✅ 새 테이블: `ga4_accounts`
- ✅ 새 테이블: `token_transactions`
- ✅ `ga4_data` 구조 변경 (날짜별 저장)
- ✅ `users` 테이블에 `user_context` 컬럼 추가

---

## 🚀 마이그레이션 절차

### Step 1: 백업

```bash
# 전체 프로젝트 백업
cp -r frameflow-api frameflow-api-backup

# 데이터베이스 백업 (Supabase Dashboard)
# 1. Settings → Database → Database Backups
# 2. Create Backup
```

### Step 2: 코드 업데이트

```bash
cd frameflow-api

# 기존 코드 스태시
git stash

# 최신 코드 가져오기
git pull origin main

# 필요 시 스태시 적용
git stash pop
```

### Step 3: 패키지 설치

```bash
# 새로운 패키지 설치
pip install -r requirements.txt

# 주요 추가 패키지:
# - APScheduler==3.10.4  (스케줄러)
```

### Step 4: 환경변수 업데이트

```bash
# 새 .env.example 확인
cat .env.example

# 기존 .env에 새 변수 추가
nano .env
```

**추가해야 할 환경변수:**

```env
# Flask 설정
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# Claude 모델 설정
CLAUDE_MODEL=claude-3-haiku-20240307
CLAUDE_MAX_TOKENS=1000

# GA4 설정
GA4_DEFAULT_DAYS=30

# 스케줄러 설정 (NEW!)
SCHEDULER_ENABLED=True
DAILY_SYNC_TIME=03:00

# 로깅 설정 (NEW!)
LOG_LEVEL=INFO

# 토큰 설정 (NEW!)
DEFAULT_TOKEN_BALANCE=10000
TOKEN_COST_PER_1K=0.001

# 페이지네이션 (NEW!)
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

### Step 5: 데이터베이스 마이그레이션

Supabase SQL Editor에서 다음 SQL 실행:

#### 5-1. ga4_accounts 테이블 생성

```sql
-- migrations/001_create_ga4_accounts.sql 내용
CREATE TABLE IF NOT EXISTS ga4_accounts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    credentials TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ga4_accounts_user_id ON ga4_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_ga4_accounts_is_active ON ga4_accounts(is_active);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ga4_accounts_user_active
ON ga4_accounts(user_id)
WHERE is_active = true;
```

#### 5-2. users 테이블 업데이트

```sql
-- user_context 컬럼 추가
ALTER TABLE users
ADD COLUMN IF NOT EXISTS user_context JSONB;

-- updated_at 컬럼 추가
ALTER TABLE users
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
```

#### 5-3. token_transactions 테이블 생성

```sql
CREATE TABLE IF NOT EXISTS token_transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    transaction_type TEXT CHECK (transaction_type IN ('charge', 'consume', 'refund')),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_token_transactions_user_id ON token_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_token_transactions_created_at ON token_transactions(created_at);
```

#### 5-4. ga4_data 테이블 업데이트

```sql
-- date 컬럼 추가 (날짜별 저장)
ALTER TABLE ga4_data
ADD COLUMN IF NOT EXISTS date DATE;

-- 기존 데이터 마이그레이션 (선택적)
-- date_range_end를 date로 복사
UPDATE ga4_data
SET date = date_range_end::DATE
WHERE date IS NULL AND date_range_end IS NOT NULL;

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_ga4_data_date ON ga4_data(user_id, date);
```

#### 5-5. 기존 사용자 데이터 마이그레이션

```sql
-- 기존 사용자들의 GA4 계정 정보 생성
-- (기존에 ga4_data가 있는 경우)
INSERT INTO ga4_accounts (user_id, property_id, credentials, is_active)
SELECT DISTINCT
    u.id,
    '488770841',  -- 기본 Property ID (필요시 수정)
    'credentials/ga4-credentials.json',
    true
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM ga4_accounts ga WHERE ga.user_id = u.id
);
```

### Step 6: 서버 테스트

```bash
# v2.0 서버 실행
python app_new.py

# 로그 확인
tail -f logs/app.log

# 다른 터미널에서 API 테스트
curl http://localhost:5000/
curl http://localhost:5000/health
```

### Step 7: API 엔드포인트 업데이트

#### 기존 → v2.0 엔드포인트 매핑

| 기존 | v2.0 | 비고 |
|------|------|------|
| `/api/chat` | `/api/chat/{user_id}` | user_id를 URL에 포함 |
| `/api/ga4/sync` | `/api/ga4/sync/{user_id}` | user_id를 URL에 포함 |
| - | `/api/ga4/sync/{user_id}/incremental` | 🆕 증분 동기화 |
| `/api/user/register` | `/api/user/register` | 동일 |
| - | `/api/user/context/{user_id}` | 🆕 AI 컨텍스트 |
| - | `/api/user/tokens/{user_id}/charge` | 🆕 토큰 충전 |

#### WordPress/Frontend 코드 예시

**기존:**
```javascript
// 기존 방식
fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 1,
    question: "질문"
  })
})
```

**v2.0:**
```javascript
// v2.0 방식
fetch('/api/chat/1', {
  method: 'POST',
  body: JSON.stringify({
    question: "질문",
    include_history: true
  })
})
```

### Step 8: 스케줄러 확인

```bash
# 스케줄러 로그 확인
tail -f logs/scheduler.log

# 수동으로 스케줄러 작업 테스트
# Python 콘솔에서:
python
>>> from services.scheduler_service import scheduler_service
>>> scheduler_service.daily_ga4_sync()
```

### Step 9: 프로덕션 배포

```bash
# 1. 환경변수를 production으로 변경
sed -i 's/FLASK_ENV=development/FLASK_ENV=production/' .env

# 2. 디버그 모드 비활성화
sed -i 's/DEBUG=True/DEBUG=False/' .env

# 3. 로그 레벨 조정
sed -i 's/LOG_LEVEL=DEBUG/LOG_LEVEL=WARNING/' .env

# 4. 서버 재시작
# systemd 사용 시:
sudo systemctl restart frameflow

# 수동 실행 시:
./stop_server.sh
nohup python app_new.py > logs/app.log 2>&1 &
```

---

## 🔄 롤백 절차

문제 발생 시 기존 버전으로 롤백:

```bash
# 1. 새 서버 중지
./stop_server.sh

# 2. 백업으로 복원
rm -rf frameflow-api
mv frameflow-api-backup frameflow-api
cd frameflow-api

# 3. 기존 서버 실행
python app.py
```

---

## ✅ 마이그레이션 체크리스트

- [ ] 전체 프로젝트 백업 완료
- [ ] Supabase 데이터베이스 백업 완료
- [ ] 최신 코드 가져오기
- [ ] 새 패키지 설치 (`pip install -r requirements.txt`)
- [ ] .env 파일 업데이트 (새 환경변수 추가)
- [ ] 데이터베이스 마이그레이션 SQL 실행
  - [ ] ga4_accounts 테이블 생성
  - [ ] users 테이블 업데이트
  - [ ] token_transactions 테이블 생성
  - [ ] ga4_data 테이블 업데이트
  - [ ] 기존 데이터 마이그레이션
- [ ] 로컬에서 v2.0 서버 테스트
- [ ] API 엔드포인트 확인
- [ ] 스케줄러 작동 확인
- [ ] WordPress/Frontend 코드 업데이트
- [ ] 프로덕션 배포
- [ ] 모니터링 및 로그 확인

---

## 🆘 문제 해결

### 문제 1: 패키지 설치 실패

```bash
# 가상환경 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 문제 2: 데이터베이스 마이그레이션 에러

```sql
-- 테이블 존재 여부 확인
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

-- 컬럼 존재 여부 확인
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'users';
```

### 문제 3: 스케줄러 작동 안 함

```env
# .env 확인
SCHEDULER_ENABLED=True
DAILY_SYNC_TIME=03:00

# 로그 확인
tail -f logs/scheduler.log
```

### 문제 4: Import 에러

```bash
# Python 경로 확인
export PYTHONPATH="${PYTHONPATH}:/path/to/frameflow-api"

# 또는 app_new.py에서 확인
import sys
print(sys.path)
```

---

## 📞 지원

마이그레이션 중 문제 발생 시:
1. `logs/error.log` 확인
2. GitHub Issues에 문의
3. Telegram 관리자에게 연락

---

**마이그레이션 완료 후 v2.0의 강력한 기능들을 활용하세요!** 🚀
