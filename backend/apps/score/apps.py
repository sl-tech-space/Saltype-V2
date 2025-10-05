from django.apps import AppConfig
from django.conf import settings


class ScoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.score"

    def ready(self):
        """
        Djangoアプリケーションの準備完了時に日次スコア送信スケジューラーを開始
        """
        # マイグレーション実行中やテスト実行中はスケジューラーを開始しない
        import sys

        if "migrate" in sys.argv or "test" in sys.argv:
            return

        # 設定で自動開始が有効な場合のみスケジューラーを開始
        if getattr(settings, "SCHEDULER_AUTOSTART", False):
            from .scheduler import start_daily_scheduler

            start_daily_scheduler()
