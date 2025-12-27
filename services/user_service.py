"""
사용자 관리 서비스
사용자 등록, 조회, 업데이트 등의 비즈니스 로직
"""
from typing import Optional, Dict
from database.supabase_client import db, supabase
from utils.logger import app_logger, error_logger
from config.settings import get_config

config = get_config()

class UserService:
    """사용자 관리 서비스"""

    @staticmethod
    def register_user(wp_user_id: int, email: str, property_id: str, token_balance: int = None) -> Dict:
        """
        WordPress 사용자 등록 및 GA4 계정 연결

        Args:
            wp_user_id: WordPress 사용자 ID
            email: 이메일
            property_id: GA4 Property ID
            token_balance: 초기 토큰 잔액

        Returns:
            {"success": bool, "user_id": int, "message": str}
        """
        try:
            # 기존 사용자 확인
            existing_user = db.get_user_by_wp_id(wp_user_id)
            if existing_user:
                return {
                    "success": False,
                    "message": "이미 등록된 사용자입니다",
                    "user_id": existing_user["id"]
                }

            # 사용자 생성
            user = db.create_user(wp_user_id, email, token_balance)
            if not user:
                return {"success": False, "message": "사용자 생성 실패"}

            user_id = user["id"]

            # GA4 계정 연결
            ga4_account = db.create_ga4_account(user_id, property_id)
            if not ga4_account:
                return {"success": False, "message": "GA4 계정 연결 실패"}

            app_logger.info(f"User registered successfully: wp_id={wp_user_id}, user_id={user_id}")

            return {
                "success": True,
                "user_id": user_id,
                "message": "사용자 등록 완료",
                "token_balance": user["token_balance"]
            }

        except Exception as e:
            error_logger.error(f"Error in register_user: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_user_profile(user_id: int) -> Optional[Dict]:
        """사용자 프로필 조회"""
        try:
            user = db.get_user_by_id(user_id)
            if not user:
                return None

            ga4_account = db.get_ga4_account(user_id)

            return {
                "user_id": user["id"],
                "wp_user_id": user["wp_user_id"],
                "email": user["email"],
                "token_balance": user["token_balance"],
                "plan": user["plan"],
                "user_context": user.get("user_context"),
                "ga4_property_id": ga4_account["property_id"] if ga4_account else None,
                "created_at": user["created_at"]
            }

        except Exception as e:
            error_logger.error(f"Error in get_user_profile: {e}")
            return None

    @staticmethod
    def update_user_ai_context(user_id: int, context_data: Dict) -> Dict:
        """
        사용자 AI 학습 컨텍스트 업데이트

        Args:
            user_id: 사용자 ID
            context_data: {
                "business_type": "쇼핑몰",
                "kpi": ["매출", "전환율"],
                "goals": "월 매출 1000만원 달성",
                "target_audience": "20-30대 여성",
                "additional_info": "..."
            }
        """
        try:
            success = db.update_user_context(user_id, context_data)

            if success:
                app_logger.info(f"User AI context updated: user_id={user_id}")
                return {"success": True, "message": "AI 컨텍스트 업데이트 완료"}
            else:
                return {"success": False, "message": "업데이트 실패"}

        except Exception as e:
            error_logger.error(f"Error in update_user_ai_context: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def charge_tokens(user_id: int, amount: int, payment_method: str = "manual") -> Dict:
        """토큰 충전"""
        try:
            new_balance = db.add_tokens(
                user_id,
                amount,
                description=f"Token recharge via {payment_method}"
            )

            if new_balance is not None:
                return {
                    "success": True,
                    "new_balance": new_balance,
                    "message": f"{amount:,} 토큰 충전 완료"
                }
            else:
                return {"success": False, "message": "토큰 충전 실패"}

        except Exception as e:
            error_logger.error(f"Error in charge_tokens: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def check_token_balance(user_id: int) -> Optional[int]:
        """토큰 잔액 조회"""
        try:
            user = db.get_user_by_id(user_id)
            return user["token_balance"] if user else None
        except Exception as e:
            error_logger.error(f"Error in check_token_balance: {e}")
            return None
