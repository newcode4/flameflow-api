from supabase import create_client
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta

# 클래스 import로 변경
from ga4_extractor_template import GA4TemplateExtractor
from ga4_config import PROPERTY_ID, CREDENTIALS_PATH

load_dotenv()

# Supabase 클라이언트
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

def save_ga4_data_to_supabase(user_id, days=30):
    """
    GA4 데이터를 추출해서 Supabase에 저장
    """
    print(f"=== GA4 데이터 수집 시작 (최근 {days}일) ===\n")
    
    # 1. GA4 데이터 추출
    try:
        extractor = GA4TemplateExtractor(PROPERTY_ID, CREDENTIALS_PATH)
        all_data = extractor.extract_data(days)
        
        print(f"\n[OK] GA4 데이터 추출 완료")
        print(f"     API 호출: {all_data['info']['api_calls']}회")
        print(f"     에러: {len(all_data['info']['errors'])}건\n")
    except Exception as e:
        print(f"[ERROR] GA4 추출 실패: {e}")
        return
    
    # 2. 날짜 계산
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # 3. Supabase에 저장
    try:
        result = supabase.table("ga4_data").insert({
            "user_id": user_id,
            "data_type": "full",
            "date_range_start": str(start_date),
            "date_range_end": str(end_date),
            "raw_data": all_data
        }).execute()
        
        print(f"[OK] Supabase 저장 완료")
        print(f"     데이터 ID: {result.data[0]['id']}")
        
        # 요약 정보 출력
        summary = all_data.get('summary', {})
        if summary:
            print(f"\n=== 저장된 데이터 요약 ===")
            print(f"활성 사용자: {summary.get('activeUsers', 0):,.0f}명")
            print(f"세션: {summary.get('sessions', 0):,.0f}개")
            print(f"총 수익: ₩{summary.get('purchaseRevenue', 0):,.0f}")
        
    except Exception as e:
        print(f"[ERROR] Supabase 저장 실패: {e}")
        return
    
    print("\n=== 완료 ===")

if __name__ == "__main__":
    # 테스트용 user_id = 1 (아까 생성한 사용자)
    save_ga4_data_to_supabase(user_id=1, days=30)