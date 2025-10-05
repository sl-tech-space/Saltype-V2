"""
APSchedulerを使用した日次スコアメール送信機能
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.core.management import call_command

logger = logging.getLogger(__name__)

# スケジューラーのインスタンス
scheduler = None


def start_daily_scheduler():
    """
    日次スコア送信のスケジューラーを開始
    """
    global scheduler

    if scheduler and scheduler.running:
        logger.info("日次スコア送信スケジューラーは既に実行中です")
        return

    # スケジューラーの設定
    scheduler_config = getattr(settings, "SCHEDULER_CONFIG", {})
    scheduler = BackgroundScheduler(**scheduler_config)

    # 毎日19時に実行
    trigger = CronTrigger(hour=19, minute=0, timezone="Asia/Tokyo")

    scheduler.add_job(
        func=send_daily_scores_job,
        trigger=trigger,
        id="daily_scores_email",
        name="日次スコアメール送信",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # スケジューラーを開始
    scheduler.start()
    logger.info("日次スコア送信スケジューラーが開始されました（毎日19:00実行）")


def send_daily_scores_job():
    """
    日次スコア送信のジョブ実行関数
    """
    try:
        logger.info("日次スコア送信ジョブを開始します")
        call_command("send_daily_scores")
        logger.info("日次スコア送信ジョブが正常に完了しました")
    except Exception as e:
        logger.error(f"日次スコア送信ジョブでエラーが発生しました: {str(e)}")
