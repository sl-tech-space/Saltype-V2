import logging
from pathlib import Path
from typing import Dict, List

import google.generativeai as genai
import yaml
from django.conf import settings
from django.db import transaction

from apps.text_generation.models import TextPair

logger = logging.getLogger("app")


class TextGenerator:
    """
    Google Generative AI を利用してタイピング用の文章を生成し、text_pairs テーブルに保存する。
    """

    PROMPT_KEY = "typing_prompt"

    def __init__(self) -> None:
        if not settings.API_KEY:
            raise ValueError("API_KEY が設定されていません。")
        if not settings.AI_MODEL:
            raise ValueError("AI_MODEL が設定されていません。")

        genai.configure(api_key=settings.API_KEY)
        self.model = genai.GenerativeModel(settings.AI_MODEL)
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """
        プロンプト YAML を読み込み、typing_prompt を取得する。
        """
        prompts_path = Path(__file__).resolve().parent / "prompts.yaml"
        if not prompts_path.exists():
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompts_path}")

        with prompts_path.open("r", encoding="utf-8") as f:
            prompts = yaml.safe_load(f)

        prompt = prompts.get(self.PROMPT_KEY)
        if not prompt:
            raise KeyError(f"プロンプトファイルにキー '{self.PROMPT_KEY}' が存在しません。")
        return prompt

    def _parse_sentences(self, response_text: str) -> List[str]:
        """
        生成結果を行単位に分割し、空行を除外する。
        """
        sentences = [
            line.strip()
            for line in response_text.splitlines()
            if line.strip()
        ]
        return sentences

    def generate_text(self) -> Dict[str, List[str]]:
        """
        プロンプトを送信して文章を生成し、TextPair に保存する。
        """
        try:
            logger.info("AI テキスト生成を開始します")
            response = self.model.generate_content(self.prompt)
            response_text = getattr(response, "text", None)
            if not response_text:
                error_message = "AI 応答にテキストが含まれていません。"
                logger.error(error_message)
                return {"error": error_message}

            sentences = self._parse_sentences(response_text)
            if not sentences:
                error_message = "生成結果が空でした。"
                logger.error(error_message)
                return {"error": error_message}

            with transaction.atomic():
                TextPair.objects.bulk_create(
                    [
                        TextPair(kanji=sentence, hiragana="", is_converted=False)
                        for sentence in sentences
                    ]
                )

            logger.info("AI テキスト生成が完了しました: %s 件", len(sentences))
            return {"sentences": sentences}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("AI テキスト生成でエラーが発生しました: %s", exc, exc_info=True)
            return {"error": str(exc)}


