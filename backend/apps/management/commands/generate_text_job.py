import logging

from django.core.management.base import BaseCommand

from apps.text_generation.generator import TextGenerator

logger = logging.getLogger("app")


class Command(BaseCommand):
    help = "AIAPIを使用して漢字を含む文章を100文生成し、テーブルのkanjiカラムに格納するジョブ"
    command_name = "generate_text_job"

    def handle(self, *args, **options):
        """
        AIAPIジョブの実行
        10分に1回 (0,10,20,30,40,50分) で動作
        """
        self.stdout.write(self.style.SUCCESS("AIテキスト生成ジョブを開始します"))
        logger.info("AIテキスト生成ジョブ開始")

        try:
            # TextGeneratorを使用して文章生成
            generator = TextGenerator()
            result = generator.generate_text()

            if "error" in result:
                logger.error(f"AIテキスト生成ジョブ失敗: {result['error']}")
                self.stdout.write(self.style.ERROR(f"ジョブ失敗: {result['error']}"))
                return

            if "sentences" not in result:
                logger.error("sentencesフィールドが見つかりません")
                self.stdout.write(
                    self.style.ERROR("ジョブ失敗: sentencesフィールドが見つかりません")
                )
                return

            sentences_count = len(result["sentences"])
            logger.info(f"AIテキスト生成ジョブ完了: {sentences_count}件生成")
            self.stdout.write(
                self.style.SUCCESS(
                    f"ジョブ完了: {sentences_count}件の文章を生成しました"
                )
            )

        except Exception as e:
            logger.error(f"AIテキスト生成ジョブエラー: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"ジョブエラー: {str(e)}"))
