-- GA4 계정 정보 테이블 생성
-- 각 사용자별로 GA4 Property ID를 저장

CREATE TABLE IF NOT EXISTS ga4_accounts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    credentials TEXT,  -- 파일 경로 또는 null (공통 사용 시)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_ga4_accounts_user_id ON ga4_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_ga4_accounts_is_active ON ga4_accounts(is_active);

-- 사용자당 하나의 활성 GA4 계정만 가질 수 있도록 제약 조건 추가
CREATE UNIQUE INDEX IF NOT EXISTS idx_ga4_accounts_user_active
ON ga4_accounts(user_id)
WHERE is_active = true;

-- 코멘트 추가
COMMENT ON TABLE ga4_accounts IS '사용자별 GA4 Property 정보를 저장하는 테이블';
COMMENT ON COLUMN ga4_accounts.user_id IS 'users 테이블의 사용자 ID';
COMMENT ON COLUMN ga4_accounts.property_id IS 'GA4 Property ID (예: 488770841)';
COMMENT ON COLUMN ga4_accounts.credentials IS 'GA4 인증 파일 경로 (공통 사용 시 null 또는 공통 경로)';
COMMENT ON COLUMN ga4_accounts.is_active IS '활성화 여부 (사용자당 하나만 활성화 가능)';
