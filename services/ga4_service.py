"""
GA4 데이터 동기화 서비스
사용자별 GA4 데이터 추출 및 증분 업데이트
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database.supabase_client import db, supabase
from ga4_extractor_template import GA4TemplateExtractor
from config.settings import get_config
from utils.logger import app_logger, error_logger

config = get_config()

class GA4Service:
    """GA4 데이터 관리 서비스"""

    @staticmethod
    def sync_user_data(user_id: int, days: int = None) -> Dict:
        """
        사용자의 GA4 데이터 동기화 (전체)

        Args:
            user_id: 사용자 ID
            days: 조회할 일수 (기본값: 설정파일)

        Returns:
            {"success": bool, "data_id": int, "message": str}
        """
        try:
            # 사용자의 GA4 계정 정보 조회
            ga4_account = db.get_ga4_account(user_id)
            if not ga4_account:
                return {"success": False, "message": "GA4 계정 정보가 없습니다"}

            property_id = ga4_account["property_id"]
            credentials = ga4_account.get("credentials") or config.GA4_CREDENTIALS_PATH
            days = days or config.GA4_DEFAULT_DAYS

            # GA4 데이터 추출
            extractor = GA4TemplateExtractor(property_id, credentials)
            all_data = extractor.extract_data(days)

            # Supabase에 저장 (날짜별)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            # 전체 데이터를 최신 날짜로 저장
            result = db.save_ga4_data(user_id, str(end_date), all_data)

            if result:
                app_logger.info(
                    f"GA4 data synced: user_id={user_id}, property_id={property_id}, "
                    f"days={days}, api_calls={all_data['info']['api_calls']}"
                )

                return {
                    "success": True,
                    "data_id": result.get("id"),
                    "property_id": property_id,
                    "date_range": f"{start_date} ~ {end_date}",
                    "summary": all_data.get("summary", {}),
                    "api_calls": all_data["info"]["api_calls"]
                }
            else:
                return {"success": False, "message": "데이터 저장 실패"}

        except Exception as e:
            error_logger.error(f"Error in sync_user_data: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def sync_incremental(user_id: int) -> Dict:
        """
        증분 데이터 동기화 (이전 날짜만 추가)
        - 기존 데이터의 마지막 날짜 이후 데이터만 가져옴
        - API 호출 최소화

        Returns:
            {"success": bool, "days_added": int, "message": str}
        """
        try:
            # 사용자의 GA4 계정 정보 조회
            ga4_account = db.get_ga4_account(user_id)
            if not ga4_account:
                return {"success": False, "message": "GA4 계정 정보가 없습니다"}

            property_id = ga4_account["property_id"]
            credentials = ga4_account.get("credentials") or config.GA4_CREDENTIALS_PATH

            # 최근 데이터 조회
            latest_data = db.get_latest_ga4_data(user_id)

            if latest_data:
                # 마지막 동기화 날짜 확인
                last_sync_date = datetime.strptime(latest_data["date"], "%Y-%m-%d").date()
                today = datetime.now().date()

                # 동기화할 일수 계산
                days_to_sync = (today - last_sync_date).days

                if days_to_sync <= 0:
                    return {
                        "success": True,
                        "days_added": 0,
                        "message": "이미 최신 데이터입니다"
                    }
            else:
                # 최초 동기화
                days_to_sync = config.GA4_DEFAULT_DAYS

            # 데이터 추출 (최소 일수만)
            extractor = GA4TemplateExtractor(property_id, credentials)
            all_data = extractor.extract_data(days_to_sync)

            # 저장
            today = datetime.now().date()
            result = db.save_ga4_data(user_id, str(today), all_data)

            if result:
                app_logger.info(
                    f"Incremental sync completed: user_id={user_id}, days_added={days_to_sync}"
                )

                return {
                    "success": True,
                    "days_added": days_to_sync,
                    "data_id": result.get("id"),
                    "message": f"{days_to_sync}일간의 데이터 추가됨"
                }
            else:
                return {"success": False, "message": "데이터 저장 실패"}

        except Exception as e:
            error_logger.error(f"Error in sync_incremental: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_user_ga4_summary(user_id: int) -> Optional[Dict]:
        """사용자의 GA4 데이터 요약 조회"""
        try:
            latest_data = db.get_latest_ga4_data(user_id)

            if not latest_data:
                return None

            raw_data = latest_data["raw_data"]

            return {
                "date_range": raw_data["info"]["date_range"],
                "summary": raw_data.get("summary", {}),
                "top_pages": raw_data.get("pages", [])[:5],
                "traffic_sources": raw_data.get("traffic_sources", [])[:5],
                "last_updated": latest_data["created_at"]
            }

        except Exception as e:
            error_logger.error(f"Error in get_user_ga4_summary: {e}")
            return None

    @staticmethod
    def get_property_id(user_id: int) -> Optional[str]:
        """사용자의 GA4 Property ID 조회"""
        try:
            ga4_account = db.get_ga4_account(user_id)
            return ga4_account["property_id"] if ga4_account else None
        except Exception as e:
            error_logger.error(f"Error in get_property_id: {e}")
            return None

    @staticmethod
    def update_property_id(user_id: int, new_property_id: str) -> Dict:
        """사용자의 GA4 Property ID 변경"""
        try:
            # 기존 계정 비활성화
            supabase.table("ga4_accounts")\
                .update({"is_active": False})\
                .eq("user_id", user_id)\
                .execute()

            # 새 계정 생성
            new_account = db.create_ga4_account(user_id, new_property_id)

            if new_account:
                app_logger.info(f"Property ID updated: user_id={user_id}, new_property_id={new_property_id}")
                return {
                    "success": True,
                    "message": "Property ID 변경 완료",
                    "new_property_id": new_property_id
                }
            else:
                return {"success": False, "message": "Property ID 변경 실패"}

        except Exception as e:
            error_logger.error(f"Error in update_property_id: {e}")
            return {"success": False, "message": str(e)}
