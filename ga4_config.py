"""
GA4 데이터 추출 설정 파일
여기서 모든 항목을 on/off 할 수 있음
"""

# ============================================================
# 기본 설정
# ============================================================
PROPERTY_ID = "488770841"
CREDENTIALS_PATH = "credentials/service-account.json"  # ← 경로 수정
DEFAULT_DAYS = 30

# ============================================================
# 데이터 수집 범위 (True/False로 on/off)
# ============================================================
EXTRACT_CONFIG = {
    # 기본 데이터
    "summary": True,              # 전체 요약
    "pages": True,                # 페이지 데이터
    "events": True,               # 이벤트 데이터
    "transactions": True,         # 거래 데이터
    
    # 심화 데이터
    "traffic_sources": True,      # 유입경로
    "campaigns": True,            # 캠페인
    "devices": True,              # 기기
    "locations": True,            # 위치
    "content": True,              # 콘텐츠 그룹
    
    # 시간 분석
    "daily_trend": True,          # 일별 트렌드
    "hourly_traffic": True,       # 시간대별
    "day_of_week": True,          # 요일별
    
    # 사용자 분석
    "new_vs_returning": True,     # 신규/재방문
    "user_segments": False,        # 사용자 세그먼트
    
    # 행동 분석
    "search_terms": True,         # 검색어
    "scroll_depth": True,         # 스크롤
    "engagement": True,           # 참여도
    
    # 퍼널
    "conversion_funnel": True,    # 전환 퍼널
}

# ============================================================
# 수집 제한 (limit)
# ============================================================
LIMITS = {
    "pages": 100,                 # 페이지 최대 100개
    "events": 200,                # 이벤트 최대 200개
    "transactions": 1000,         # 거래 전체
    "sources": 100,               # 유입경로 100개
    "campaigns": 200,             # 캠페인 200개
    "devices": 50,                # 기기 조합 50개
    "locations": 100,             # 위치 100개
    "search_terms": 100,          # 검색어 100개
}

# ============================================================
# 기본 측정기준/항목
# ============================================================
DEFAULT_DIMENSIONS = {
    "page": "pagePath",
    "event": "eventName",
    "source": "sessionSource",
    "medium": "sessionMedium",
    "device": "deviceCategory",
    "city": "city",
    "date": "date",
    "hour": "hour",
}

DEFAULT_METRICS = {
    "users": "activeUsers",
    "sessions": "sessions",
    "pageviews": "screenPageViews",
    "bounceRate": "bounceRate",
    "events": "keyEvents",
    "revenue": "purchaseRevenue",
    "transactions": "transactions",
}

# ============================================================
# 맞춤 측정기준 (추가/수정 가능)
# ============================================================
CUSTOM_DIMENSIONS = {
    # 거래
    "transaction_id": "customEvent:transaction_id",
    "payment_type": "customEvent:payment_type",
    "payment_amount": "customEvent:payment_amount",
    
    # 캠페인
    "campaign": "customEvent:campaign",
    "utm_source": "customEvent:source",
    "utm_medium": "customEvent:medium",
    "utm_content": "customEvent:content",
    
    # 콘텐츠
    "content_group": "customEvent:content_group",
    "page_location": "customEvent:page_location",
    
    # 사용자
    "user_type": "customEvent:user_type",
    "membership_level": "customEvent:membership_level",
    
    # 행동
    "scroll_depth": "customEvent:scroll_depth",
    "search_term": "customEvent:search_term",
    "video_progress": "customEvent:video_progress",
    
    # 상품
    "product_id": "customEvent:product_id",
    "product_category": "customEvent:product_category",
}

# ============================================================
# 주요 이벤트 정의 (자동 필터링)
# ============================================================
KEY_EVENTS = [
    "purchase",              # 구매
    "purchase_subscription", # 구독 구매
    "form_submit",           # 폼 제출
    "sign_up",               # 회원가입
    "add_to_cart",           # 장바구니
    "begin_checkout",        # 결제 시작
    "view_item",             # 상품 조회
]

# ============================================================
# API 호출 전략
# ============================================================
API_STRATEGY = {
    "retry_count": 3,           # 에러 시 재시도 횟수
    "retry_delay": 2,           # 재시도 대기 시간 (초)
    "timeout": 30,              # 타임아웃 (초)
    "batch_size": 100,          # 배치 크기
}