"""
Supabase 데이터베이스 클라이언트
모든 데이터베이스 작업을 관리합니다.
"""
from supabase import create_client, Client
from typing import Optional, Dict, List, Any
from config.settings import get_config
from utils.logger import app_logger, error_logger

config = get_config()

# Supabase 클라이언트 초기화
try:
    supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    app_logger.info("Supabase client initialized successfully")
except Exception as e:
    error_logger.error(f"Failed to initialize Supabase client: {e}")
    raise

class SupabaseClient:
    """Supabase 데이터베이스 작업을 위한 클래스"""

    @staticmethod
    def get_user_by_wp_id(wp_user_id: int) -> Optional[Dict]:
        """WordPress 사용자 ID로 조회"""
        try:
            result = supabase.table("users")\
                .select("*")\
                .eq("wp_user_id", wp_user_id)\
                .limit(1)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            error_logger.error(f"Error fetching user by wp_id {wp_user_id}: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """사용자 ID로 조회"""
        try:
            result = supabase.table("users")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            error_logger.error(f"Error fetching user {user_id}: {e}")
            return None

    @staticmethod
    def create_user(wp_user_id: int, email: str, token_balance: int = None) -> Optional[Dict]:
        """새 사용자 생성"""
        try:
            result = supabase.table("users").insert({
                "wp_user_id": wp_user_id,
                "email": email,
                "token_balance": token_balance or config.DEFAULT_TOKEN_BALANCE,
                "plan": "beta"
            }).execute()
            app_logger.info(f"User created: wp_id={wp_user_id}, email={email}")
            return result.data[0] if result.data else None
        except Exception as e:
            error_logger.error(f"Error creating user: {e}")
            return None

    @staticmethod
    def update_user_context(user_id: int, context: Dict) -> bool:
        """사용자 AI 컨텍스트 업데이트"""
        try:
            supabase.table("users")\
                .update({"user_context": context})\
                .eq("id", user_id)\
                .execute()
            app_logger.info(f"User context updated: user_id={user_id}")
            return True
        except Exception as e:
            error_logger.error(f"Error updating user context: {e}")
            return False

    @staticmethod
    def get_ga4_account(user_id: int) -> Optional[Dict]:
        """사용자의 활성 GA4 계정 조회"""
        try:
            result = supabase.table("ga4_accounts")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            error_logger.error(f"Error fetching GA4 account for user {user_id}: {e}")
            return None

    @staticmethod
    def create_ga4_account(user_id: int, property_id: str, credentials: str = None) -> Optional[Dict]:
        """GA4 계정 생성"""
        try:
            result = supabase.table("ga4_accounts").insert({
                "user_id": user_id,
                "property_id": property_id,
                "credentials": credentials or config.GA4_CREDENTIALS_PATH,
                "is_active": True
            }).execute()
            app_logger.info(f"GA4 account created: user_id={user_id}, property_id={property_id}")
            return result.data[0] if result.data else None
        except Exception as e:
            error_logger.error(f"Error creating GA4 account: {e}")
            return None

    @staticmethod
    def get_latest_ga4_data(user_id: int) -> Optional[Dict]:
        """최근 GA4 데이터 조회"""
        try:
            result = supabase.table("ga4_data")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            error_logger.error(f"Error fetching latest GA4 data for user {user_id}: {e}")
            return None

    @staticmethod
    def get_ga4_data_by_date(user_id: int, date: str) -> Optional[Dict]:
        """특정 날짜의 GA4 데이터 조회"""
        try:
            result = supabase.table("ga4_data")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("date", date)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            return None

    @staticmethod
    def save_ga4_data(user_id: int, date: str, raw_data: Dict) -> Optional[Dict]:
        """GA4 데이터 저장 (날짜별)"""
        try:
            # 기존 데이터 확인
            existing = SupabaseClient.get_ga4_data_by_date(user_id, date)

            if existing:
                # 업데이트
                result = supabase.table("ga4_data")\
                    .update({"raw_data": raw_data})\
                    .eq("id", existing["id"])\
                    .execute()
                app_logger.info(f"GA4 data updated: user_id={user_id}, date={date}")
            else:
                # 삽입
                result = supabase.table("ga4_data").insert({
                    "user_id": user_id,
                    "date": date,
                    "raw_data": raw_data
                }).execute()
                app_logger.info(f"GA4 data saved: user_id={user_id}, date={date}")

            return result.data[0] if result.data else None
        except Exception as e:
            error_logger.error(f"Error saving GA4 data: {e}")
            return None

    @staticmethod
    def save_chat_history(user_id: int, question: str, answer: str, tokens_used: int) -> Optional[Dict]:
        """챗봇 대화 기록 저장"""
        try:
            result = supabase.table("chat_history").insert({
                "user_id": user_id,
                "question": question,
                "answer": answer,
                "tokens_used": tokens_used
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            error_logger.error(f"Error saving chat history: {e}")
            return None

    @staticmethod
    def get_chat_history(user_id: int, limit: int = 10) -> List[Dict]:
        """사용자의 최근 대화 기록 조회"""
        try:
            result = supabase.table("chat_history")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception as e:
            error_logger.error(f"Error fetching chat history: {e}")
            return []

    @staticmethod
    def update_token_balance(user_id: int, tokens_consumed: int) -> Optional[int]:
        """토큰 차감"""
        try:
            # 현재 잔액 조회
            user = supabase.table("users")\
                .select("token_balance")\
                .eq("id", user_id)\
                .single()\
                .execute()

            current_balance = user.data["token_balance"]
            new_balance = current_balance - tokens_consumed

            if new_balance < 0:
                error_logger.warning(f"Insufficient token balance for user {user_id}")
                return None

            # 잔액 업데이트
            supabase.table("users")\
                .update({"token_balance": new_balance})\
                .eq("id", user_id)\
                .execute()

            # 토큰 사용 로그 저장
            supabase.table("token_transactions").insert({
                "user_id": user_id,
                "amount": -tokens_consumed,
                "transaction_type": "consume",
                "description": "AI Chat usage"
            }).execute()

            app_logger.info(f"Token deducted: user_id={user_id}, consumed={tokens_consumed}, balance={new_balance}")
            return new_balance
        except Exception as e:
            error_logger.error(f"Error updating token balance: {e}")
            return None

    @staticmethod
    def add_tokens(user_id: int, amount: int, description: str = "Token recharge") -> Optional[int]:
        """토큰 충전"""
        try:
            # 현재 잔액 조회
            user = supabase.table("users")\
                .select("token_balance")\
                .eq("id", user_id)\
                .single()\
                .execute()

            current_balance = user.data["token_balance"]
            new_balance = current_balance + amount

            # 잔액 업데이트
            supabase.table("users")\
                .update({"token_balance": new_balance})\
                .eq("id", user_id)\
                .execute()

            # 토큰 충전 로그 저장
            supabase.table("token_transactions").insert({
                "user_id": user_id,
                "amount": amount,
                "transaction_type": "charge",
                "description": description
            }).execute()

            app_logger.info(f"Token added: user_id={user_id}, amount={amount}, balance={new_balance}")
            return new_balance
        except Exception as e:
            error_logger.error(f"Error adding tokens: {e}")
            return None

# 전역 인스턴스
db = SupabaseClient()

# 하위 호환성을 위한 함수들 (기존 코드와 호환)
def get_user_by_wp_id(wp_user_id: int):
    return db.get_user_by_wp_id(wp_user_id)

def get_latest_ga4_data(user_id: int):
    return db.get_latest_ga4_data(user_id)

def save_chat_history(user_id: int, question: str, answer: str, tokens_used: int):
    return db.save_chat_history(user_id, question, answer, tokens_used)

def update_token_balance(user_id: int, tokens_consumed: int):
    return db.update_token_balance(user_id, tokens_consumed)

def save_ga4_data(user_id: int, date: str, raw_data: Dict):
    return db.save_ga4_data(user_id, date, raw_data)
