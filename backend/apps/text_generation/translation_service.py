import logging
from pathlib import Path

import google.generativeai as genai
import yaml
from django.conf import settings
from django.db import transaction

from apps.text_generation.models import EnglishText

logger = logging.getLogger("app")


class EnglishTranslationService:
    """
    英語文章の和訳を生成し、DBに保存するサービスクラス。
    """

    PROMPT_KEY = "translation_prompt"

    def __init__(self) -> None:
        if not settings.API_KEY:
            raise ValueError("API_KEY が設定されていません。")
        if not settings.AI_MODEL:
            raise ValueError("AI_MODEL が設定されていません。")

        genai.configure(api_key=settings.API_KEY)
        self.model = genai.GenerativeModel(settings.AI_MODEL)
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """
        プロンプト YAML を読み込み、翻訳用プロンプトを取得する。
        """
        prompts_path = Path(__file__).resolve().parent / "prompts.yaml"
        if not prompts_path.exists():
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompts_path}")

        with prompts_path.open("r", encoding="utf-8") as f:
            prompts = yaml.safe_load(f)

        prompt = prompts.get(self.PROMPT_KEY)
        if not prompt:
            # フォールバック用のプロンプト
            return "Translate the following English sentence into Japanese. Output only the Japanese translation."
        return prompt

    def translate_pending_texts(self, limit=100) -> dict:
        """
        未翻訳の英語文章を取得し、翻訳して保存する。
        """
        pending_texts = EnglishText.objects.filter(is_translated=False)[:limit]
        count = len(pending_texts)
        
        if count == 0:
            logger.info("未翻訳の英語文章はありません。")
            return {"count": 0}

        logger.info(f"{count}件の英語文章の翻訳を開始します。")
        
        success_count = 0
        
        for text in pending_texts:
            try:
                prompt = f"{self.prompt_template}\n\n{text.content}"
                response = self.model.generate_content(prompt)
                
                if response.text:
                    # 翻訳結果をクリーニング（改行や余計な空白を削除）
                    meaning = response.text.strip()
                    
                    # トランザクション内で更新
                    with transaction.atomic():
                        text.meaning = meaning
                        text.is_translated = True
                        text.save()
                    
                    success_count += 1
                else:
                    logger.warning(f"ID {text.id} の翻訳に失敗しました（空の応答）。")
                    
            except Exception as e:
                logger.error(f"ID {text.id} の翻訳中にエラーが発生しました: {e}")
                continue

        logger.info(f"翻訳完了: {success_count}/{count} 件")
        return {"count": success_count}

