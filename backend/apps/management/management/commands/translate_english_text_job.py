import logging

from django.core.management.base import BaseCommand

from apps.text_generation.translation_service import EnglishTranslationService

logger = logging.getLogger("app")


class Command(BaseCommand):
    help = "未翻訳の英語文章を翻訳して保存するジョブ"
    command_name = "translate_english_text_job"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("英語翻訳ジョブを開始します"))
        logger.info("英語翻訳ジョブ開始")

        try:
            service = EnglishTranslationService()
            result = service.translate_pending_texts()

            count = result.get("count", 0)
            logger.info(f"英語翻訳ジョブ完了: {count}件翻訳")
            self.stdout.write(
                self.style.SUCCESS(f"ジョブ完了: {count}件の英語文章を翻訳しました")
            )

        except Exception as e:
            logger.error(f"英語翻訳ジョブエラー: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"ジョブエラー: {str(e)}"))

