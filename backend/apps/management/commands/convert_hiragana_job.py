import logging

import MeCab
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.text_generation.models import TextPair

logger = logging.getLogger("app")


class Command(BaseCommand):
    help = "変換フラグが0のkanjiカラムの文章をMeCabでひらがな化し、変換フラグを1にするジョブ"
    command_name = "convert_hiragana_job"

    def _katakana_to_hiragana(self, katakana_text):
        """カタカナをひらがなに変換するヘルパーメソッド"""
        hiragana_text = ""
        for char in katakana_text:
            if "ァ" <= char <= "ヶ":
                # カタカナをひらがなに変換
                hiragana_text += chr(ord(char) - ord("ァ") + ord("ぁ"))
            else:
                hiragana_text += char
        return hiragana_text

    def handle(self, *args, **options):
        """
        ひらがな変換ジョブの実行
        10分に1回 (5,15,25,35,45,55分) で動作
        """
        self.stdout.write(self.style.SUCCESS("ひらがな変換ジョブを開始します"))
        logger.info("ひらがな変換ジョブ開始")

        try:
            # MeCabの初期化（複数の設定を試行）
            mecab = None
            mecab_available = False

            for tagger_option in [
                "",
                "-Owakati",
                "-d /usr/lib/mecab/dic/ipadic",
                "-d /var/lib/mecab/dic/ipadic",
            ]:
                try:
                    logger.info(f"MeCab初期化試行: {tagger_option or 'デフォルト'}")
                    mecab = MeCab.Tagger(tagger_option)
                    mecab_available = True
                    logger.info(f"MeCab初期化成功: {tagger_option or 'デフォルト'}")
                    break
                except RuntimeError as e:
                    logger.warning(
                        f"MeCab初期化失敗: {tagger_option or 'デフォルト'} - {str(e)}"
                    )
                    continue

            if not mecab_available:
                logger.error("MeCabの初期化に失敗しました。")
                self.stdout.write(
                    self.style.ERROR("ジョブ失敗: MeCabの初期化に失敗しました")
                )
                return

            # 未変換の文章を取得
            unconverted_pairs = TextPair.objects.filter(is_converted=False)

            if not unconverted_pairs.exists():
                logger.info("変換対象の文章が見つかりませんでした")
                self.stdout.write(self.style.WARNING("変換対象の文章がありません"))
                return

            converted_count = 0

            with transaction.atomic():
                for text_pair in unconverted_pairs:
                    try:
                        # MeCabで形態素解析
                        parsed = mecab.parse(text_pair.kanji)
                        lines = parsed.strip().split("\n")

                        # ひらがな部分を抽出
                        hiragana_parts = []
                        for line in lines:
                            if line == "EOS" or not line.strip():
                                break
                            parts = line.split("\t")
                            if len(parts) >= 2:
                                # 表層形（単語）
                                surface = parts[0]
                                # 品詞情報をカンマで分割
                                features = parts[1].split(",")

                                # 読み仮名はカンマ区切りの8番目（インデックス7）
                                if len(features) >= 8 and features[7] != "*":
                                    # カタカナをひらがなに変換
                                    katakana_reading = features[7]
                                    hiragana_reading = self._katakana_to_hiragana(
                                        katakana_reading
                                    )
                                    hiragana_parts.append(hiragana_reading)
                                else:
                                    # 読み仮名がない場合は表層形をそのまま使用
                                    hiragana_parts.append(surface)

                        # ひらがな文章を作成
                        hiragana_text = "".join(hiragana_parts)

                        # データベースを更新
                        text_pair.hiragana = hiragana_text
                        text_pair.is_converted = True
                        text_pair.save()

                        converted_count += 1

                    except Exception as e:
                        logger.error(f"個別変換エラー (ID: {text_pair.id}): {str(e)}")
                        continue

            logger.info(f"ひらがな変換ジョブ完了: {converted_count}件変換")
            self.stdout.write(
                self.style.SUCCESS(
                    f"ジョブ完了: {converted_count}件の文章をひらがなに変換しました"
                )
            )

        except Exception as e:
            logger.error(f"ひらがな変換ジョブエラー: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"ジョブエラー: {str(e)}"))
