"""
스케줄러 서비스
일일 자동 데이터 갱신 및 정기 작업 관리
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from database.supabase_client import supabase
from services.ga4_service import GA4Service
from config.settings import get_config
from utils.logger import scheduler_logger, error_logger

config = get_config()

class SchedulerService:
    """스케줄러 관리 서비스"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.ga4_service = GA4Service()

    def start(self):
        """스케줄러 시작"""
        if not config.SCHEDULER_ENABLED:
            scheduler_logger.info("Scheduler is disabled in config")
            return

        # 일일 GA4 데이터 동기화 작업 등록
        sync_time = config.DAILY_SYNC_TIME.split(":")
        hour, minute = int(sync_time[0]), int(sync_time[1])

        self.scheduler.add_job(
            self.daily_ga4_sync,
            CronTrigger(hour=hour, minute=minute),
            id="daily_ga4_sync",
            name="Daily GA4 Data Sync",
            replace_existing=True
        )

        # 스케줄러 시작
        self.scheduler.start()
        scheduler_logger.info(
            f"Scheduler started - Daily sync at {config.DAILY_SYNC_TIME}"
        )

    def stop(self):
        """스케줄러 중지"""
        self.scheduler.shutdown()
        scheduler_logger.info("Scheduler stopped")

    def daily_ga4_sync(self):
        """
        모든 활성 사용자의 GA4 데이터 증분 동기화
        - 이전 날짜 이후의 데이터만 추가
        - 실패 시 재시도 및 로깅
        """
        scheduler_logger.info("Starting daily GA4 sync job")
        start_time = datetime.now()

        try:
            # 활성 GA4 계정이 있는 모든 사용자 조회
            result = supabase.table("ga4_accounts")\
                .select("user_id, property_id")\
                .eq("is_active", True)\
                .execute()

            users = result.data
            scheduler_logger.info(f"Found {len(users)} users to sync")

            success_count = 0
            fail_count = 0
            total_days_added = 0

            for user in users:
                user_id = user["user_id"]
                property_id = user["property_id"]

                try:
                    # 증분 동기화 실행
                    sync_result = self.ga4_service.sync_incremental(user_id)

                    if sync_result.get("success"):
                        success_count += 1
                        days_added = sync_result.get("days_added", 0)
                        total_days_added += days_added

                        scheduler_logger.info(
                            f"Synced user {user_id} (property: {property_id}): "
                            f"+{days_added} days"
                        )
                    else:
                        fail_count += 1
                        error_msg = sync_result.get("message", "Unknown error")
                        scheduler_logger.warning(
                            f"Failed to sync user {user_id}: {error_msg}"
                        )

                except Exception as e:
                    fail_count += 1
                    error_logger.error(f"Error syncing user {user_id}: {e}")

            # 작업 완료 요약
            duration = (datetime.now() - start_time).total_seconds()
            scheduler_logger.info(
                f"Daily sync completed: "
                f"Success={success_count}, Failed={fail_count}, "
                f"Total days added={total_days_added}, "
                f"Duration={duration:.2f}s"
            )

            # 텔레그램 알림 (선택적)
            if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_ADMIN_CHAT_ID:
                self._send_telegram_notification(
                    f"📊 일일 GA4 동기화 완료\n\n"
                    f"✅ 성공: {success_count}명\n"
                    f"❌ 실패: {fail_count}명\n"
                    f"📈 추가된 데이터: {total_days_added}일\n"
                    f"⏱️ 소요시간: {duration:.2f}초"
                )

        except Exception as e:
            error_logger.error(f"Critical error in daily_ga4_sync: {e}")
            scheduler_logger.error(f"Daily sync failed: {e}")

    def _send_telegram_notification(self, message: str):
        """텔레그램 알림 전송"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": config.TELEGRAM_ADMIN_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            requests.post(url, data=data, timeout=5)
        except Exception as e:
            scheduler_logger.warning(f"Failed to send Telegram notification: {e}")

    def manual_sync_all(self):
        """수동으로 전체 사용자 동기화 실행"""
        scheduler_logger.info("Manual sync triggered")
        self.daily_ga4_sync()

# 전역 스케줄러 인스턴스
scheduler_service = SchedulerService()
