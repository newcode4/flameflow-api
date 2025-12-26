from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# 디버깅: 환경변수 확인
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_SERVICE_KEY:", os.getenv("SUPABASE_SERVICE_KEY")[:20] + "...")
print()

# 값이 None이면 .env 파일 못 읽은 것
if not os.getenv("SUPABASE_URL"):
    print("[ERROR] .env 파일을 찾을 수 없거나 잘못되었습니다")
    exit()

# Supabase 클라이언트
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


# 테스트 1: 사용자 생성
try:
    result = supabase.table("users").insert({
        "wp_user_id": 999,
        "email": "test@frameflow.com",
        "token_balance": 10000,
        "plan": "beta"
    }).execute()
    
    print("[OK] 사용자 생성 성공")
    print(f"     User ID: {result.data[0]['id']}")
    user_id = result.data[0]['id']
except Exception as e:
    print(f"[ERROR] {e}")
    exit()

# 테스트 2: GA4 데이터 저장
try:
    result = supabase.table("ga4_data").insert({
        "user_id": user_id,
        "data_type": "summary",
        "date_range_start": "2024-12-01",
        "date_range_end": "2024-12-25",
        "raw_data": {
            "active_users": 2943,
            "sessions": 4065,
            "revenue": 2264000
        }
    }).execute()
    
    print("[OK] GA4 데이터 저장 성공")
except Exception as e:
    print(f"[ERROR] {e}")

# 테스트 3: 데이터 조회
try:
    result = supabase.table("ga4_data")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("date_range_end", desc=True)\
        .limit(1)\
        .execute()
    
    if result.data:
        print("[OK] 데이터 조회 성공")
        print(f"     활성 사용자: {result.data[0]['raw_data']['active_users']}")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n=== 테스트 완료 ===")