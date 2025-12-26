from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

# 환경변수 확인
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_by_wp_id(wp_user_id):
    """WordPress 사용자 ID로 조회"""
    result = supabase.table("users")\
        .select("*")\
        .eq("wp_user_id", wp_user_id)\
        .limit(1)\
        .execute()
    
    return result.data[0] if result.data else None

def get_latest_ga4_data(user_id, days=30):
    """최근 GA4 데이터 조회"""
    result = supabase.table("ga4_data")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("data_type", "full")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
    
    return result.data[0] if result.data else None

def save_chat_history(user_id, question, answer, tokens_used):
    """챗봇 대화 기록 저장"""
    result = supabase.table("chat_history").insert({
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "tokens_used": tokens_used
    }).execute()
    
    return result.data[0] if result.data else None

def update_token_balance(user_id, tokens_consumed):
    """토큰 차감"""
    # 현재 잔액 조회
    user = supabase.table("users")\
        .select("token_balance")\
        .eq("id", user_id)\
        .single()\
        .execute()
    
    current_balance = user.data["token_balance"]
    new_balance = current_balance - tokens_consumed
    
    # 잔액 업데이트
    supabase.table("users")\
        .update({"token_balance": new_balance})\
        .eq("id", user_id)\
        .execute()
    
    # 로그 저장
    supabase.table("token_usage").insert({
        "user_id": user_id,
        "action": "chat",
        "tokens_consumed": tokens_consumed,
        "balance_after": new_balance
    }).execute()
    
    return new_balance

def save_ga4_data(user_id, start_date, end_date, raw_data):
    """GA4 데이터 저장"""
    result = supabase.table("ga4_data").insert({
        "user_id": user_id,
        "data_type": "full",
        "date_range_start": start_date,
        "date_range_end": end_date,
        "raw_data": raw_data
    }).execute()
    
    return result.data[0] if result.data else None