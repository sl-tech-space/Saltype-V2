import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger("app")


class Command(BaseCommand):
    help = "textpairsテーブルのパーティション管理（作成・削除）を行うジョブ"
    command_name = "partition_textpairs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-partitions",
            action="store_true",
            help="新しいパーティションを作成",
        )
        parser.add_argument(
            "--cleanup-old-partitions",
            action="store_true",
            help="3日より古いパーティションを削除",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="パーティション作成とクリーンアップの両方を実行",
        )

    def create_partition_for_date(self, date):
        """指定日のパーティションを作成"""
        partition_name = f"text_pairs_{date.strftime('%Y%m%d')}"
        start_date = date.strftime("%Y-%m-%d")
        end_date = (date + timedelta(days=1)).strftime("%Y-%m-%d")

        with connection.cursor() as cursor:
            # パーティションが既に存在するかチェック
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """,
                [partition_name],
            )

            if cursor.fetchone()[0]:
                self.stdout.write(f"パーティション {partition_name} は既に存在します")
                return False

            try:
                # パーティションを作成
                cursor.execute(f"""
                    CREATE TABLE {partition_name} PARTITION OF text_pairs
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                """)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"パーティション {partition_name} を作成しました"
                    )
                )
                logger.info(f"パーティション作成: {partition_name}")
                return True

            except Exception as e:
                error_msg = str(e)
                # デフォルトパーティションの制約エラーの場合は警告のみ
                if (
                    (
                        "text_pairs_default" in error_msg
                        and "would be violated" in error_msg
                    )
                    or ("CheckViolation" in error_msg)
                    or ("constraint" in error_msg)
                ):
                    self.stdout.write(
                        self.style.WARNING(
                            f"パーティション {partition_name} の作成をスキップ: デフォルトパーティションに既存データあり"
                        )
                    )
                    logger.warning(
                        f"パーティション作成スキップ: {partition_name} - {error_msg}"
                    )
                    return False
                # その他のエラーは再発生させる
                raise e

    def cleanup_old_partitions(self):
        """3日より古いパーティションを削除"""
        cutoff_date = datetime.now().date() - timedelta(days=3)

        with connection.cursor() as cursor:
            # text_pairsのパーティション一覧を取得
            cursor.execute("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE tablename LIKE 'text_pairs_%'
                AND schemaname = 'public'
            """)

            partitions = cursor.fetchall()
            deleted_count = 0

            for schema, table_name in partitions:
                # テーブル名から日付を抽出
                try:
                    date_str = table_name.replace("text_pairs_", "")
                    partition_date = datetime.strptime(date_str, "%Y%m%d").date()

                    if partition_date < cutoff_date:
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"古いパーティション {table_name} を削除しました"
                            )
                        )
                        logger.info(f"パーティション削除: {table_name}")
                        deleted_count += 1

                except ValueError:
                    # 日付形式でない場合はスキップ
                    continue

            self.stdout.write(f"削除したパーティション数: {deleted_count}")
            return deleted_count

    def handle(self, *args, **options):
        """パーティション管理ジョブの実行"""
        self.stdout.write(
            self.style.SUCCESS("textpairsパーティション管理ジョブを開始します")
        )
        logger.info("textpairsパーティション管理ジョブ開始")

        try:
            if options["all"] or options["create_partitions"]:
                # 今日と明日のパーティションを作成
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)

                self.create_partition_for_date(today)
                self.create_partition_for_date(tomorrow)

            if options["all"] or options["cleanup_old_partitions"]:
                # 古いパーティションをクリーンアップ
                deleted_count = self.cleanup_old_partitions()

            self.stdout.write(
                self.style.SUCCESS("パーティション管理ジョブが完了しました")
            )
            logger.info("textpairsパーティション管理ジョブ完了")

        except Exception as e:
            logger.error(f"パーティション管理ジョブエラー: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"ジョブエラー: {str(e)}"))
