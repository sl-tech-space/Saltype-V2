#!/usr/bin/env python3
"""
Saltype-V2 Django 管理コマンド用スケジューラー。
APScheduler を利用し、定期的に管理コマンドを実行する。
"""

import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = Path(os.getenv("DJANGO_SCHEDULER_LOG_DIR", BASE_DIR / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE_PATH = LOG_DIR / "scheduler.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class DjangoJobScheduler:
    def __init__(self) -> None:
        self.scheduler = BlockingScheduler()
        self.app_dir = Path(os.getenv("DJANGO_APP_DIR", BASE_DIR))
        self.python_path = os.getenv("DJANGO_PYTHON_PATH", sys.executable)
        self.manage_py = Path(os.getenv("DJANGO_MANAGE_PY", self.app_dir / "manage.py"))
        self.django_env_file = Path(
            os.getenv("DJANGO_ENV_FILE", Path(os.getenv("TMP", "/tmp")) / "django_env")
        )

    def load_environment(self) -> None:
        """環境変数ファイルを読み込み。"""
        if not self.django_env_file.exists():
            logger.warning("環境変数ファイルが見つかりません: %s", self.django_env_file)
            return

        logger.info("環境変数ファイルを読み込みます: %s", self.django_env_file)
        with self.django_env_file.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                key, value = stripped.split("=", 1)
                if key.startswith("export "):
                    key = key[7:]
                os.environ[key] = value.strip('"')

    def _log_command_result(
        self,
        job_name: str,
        returncode: int,
        stdout: str,
        stderr: str,
    ) -> None:
        log_path = LOG_DIR / f"{job_name}.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8") as file:
            file.write(f"\n=== {timestamp} ===\n")
            file.write(f"Exit code: {returncode}\n")
            if stdout:
                file.write("STDOUT:\n")
                file.write(stdout)
                if not stdout.endswith("\n"):
                    file.write("\n")
            if stderr:
                file.write("STDERR:\n")
                file.write(stderr)
                if not stderr.endswith("\n"):
                    file.write("\n")
            file.write("=" * 50 + "\n")

    def run_django_command(self, command_args: Iterable[str], job_name: str) -> None:
        """Django 管理コマンドを実行する。"""
        try:
            logger.info("%s ジョブを開始します", job_name)
            cmd = [self.python_path, str(self.manage_py), *command_args]
            result = subprocess.run(
                cmd,
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )

            self._log_command_result(
                job_name, result.returncode, result.stdout, result.stderr
            )

            if result.returncode == 0:
                logger.info("%s ジョブが正常に完了しました", job_name)
            else:
                logger.error(
                    "%s ジョブが失敗しました (Exit code: %s)",
                    job_name,
                    result.returncode,
                )

        except subprocess.TimeoutExpired:
            logger.error("%s ジョブがタイムアウトしました", job_name)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("%s ジョブでエラーが発生しました: %s", job_name, exc)

    def setup_jobs(self) -> None:
        """スケジュールジョブを登録する。"""
        self.scheduler.add_job(
            func=self.run_django_command,
            trigger=CronTrigger(minute="0,10,20,30,40,50"),
            args=(["generate_text_job"], "generate_text_job"),
            id="generate_text_job",
            name="AIテキスト生成ジョブ",
            replace_existing=True,
        )

        self.scheduler.add_job(
            func=self.run_django_command,
            trigger=CronTrigger(minute="5,15,25,35,45,55"),
            args=(["convert_hiragana_job"], "convert_hiragana_job"),
            id="convert_hiragana_job",
            name="ひらがな変換ジョブ",
            replace_existing=True,
        )

        self.scheduler.add_job(
            func=self.run_django_command,
            trigger=CronTrigger(hour=2, minute=0),
            args=(["partition_textpairs", "--all"], "partition_textpairs"),
            id="partition_textpairs",
            name="テキストペア分割ジョブ",
            replace_existing=True,
        )

        logger.info("スケジュールジョブを登録しました")

    def start(self) -> None:
        """スケジューラーを開始する。"""
        try:
            logger.info("スケジューラーを開始します")
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("スケジューラーを停止します")
            self.scheduler.shutdown()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("スケジューラーでエラーが発生しました: %s", exc)
            sys.exit(1)


def main() -> None:
    """エントリーポイント。"""
    logger.info("Saltype-V2 Django スケジューラーを起動します")
    scheduler = DjangoJobScheduler()
    scheduler.load_environment()
    scheduler.setup_jobs()

    logger.info("設定済みジョブ:")
    logger.info("  - AIテキスト生成ジョブ (generate_text_job) : 0,10,20,30,40,50分")
    logger.info("  - ひらがな変換ジョブ (convert_hiragana_job) : 5,15,25,35,45,55分")
    logger.info("  - テキストペア分割ジョブ (partition_textpairs) : 毎日 2:00")

    logger.info("スケジューラーの稼働を開始します…")
    scheduler.start()


if __name__ == "__main__":
    main()
