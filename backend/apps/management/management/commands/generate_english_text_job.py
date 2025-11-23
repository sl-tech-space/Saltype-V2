import logging

from django.core.management.base import BaseCommand

from apps.text_generation.generator import TextGenerator

logger = logging.getLogger("app")


class Command(BaseCommand):
    help = "AIAPIを使用して英語の文章を100文生成し、テーブルに格納するジョブ"
    command_name = "generate_english_text_job"

    def handle(self, *args, **options):
        """
        英語AIAPIジョブの実行
        """
        self.stdout.write(self.style.SUCCESS("英語AIテキスト生成ジョブを開始します"))
        logger.info("英語AIテキスト生成ジョブ開始")

        try:
            # TextGeneratorを使用して英語文章生成
            generator = TextGenerator(language="english")
            result = generator.generate_text()

            if "error" in result:
                logger.error(f"英語AIテキスト生成ジョブ失敗: {result['error']}")
                self.stdout.write(self.style.ERROR(f"ジョブ失敗: {result['error']}"))
                return

            if "sentences" not in result:
                logger.error("sentencesフィールドが見つかりません")
                self.stdout.write(
                    self.style.ERROR("ジョブ失敗: sentencesフィールドが見つかりません")
                )
                return

            sentences_count = len(result["sentences"])
            logger.info(f"英語AIテキスト生成ジョブ完了: {sentences_count}件生成")
            self.stdout.write(
                self.style.SUCCESS(
                    f"ジョブ完了: {sentences_count}件の英語文章を生成しました"
                )
            )

        except Exception as e:
            logger.error(f"英語AIテキスト生成ジョブエラー: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"ジョブエラー: {str(e)}"))

