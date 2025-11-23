from django.db import models


class TextPair(models.Model):
    """
    テキスト生成ジョブで作成される漢字・ひらがなペアを保持するモデル（日本語用）。
    """

    id = models.BigAutoField(primary_key=True)
    kanji = models.TextField(help_text="生成された漢字文章")
    hiragana = models.TextField(
        blank=True, default="", help_text="漢字文章をひらがな化した結果"
    )
    is_converted = models.BooleanField(
        default=False, help_text="ひらがな変換済みかどうか"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "text_pairs"
        ordering = ["-created_at"]


class EnglishText(models.Model):
    """
    テキスト生成ジョブで作成される英語文章を保持するモデル。
    """

    id = models.BigAutoField(primary_key=True)
    content = models.TextField(help_text="生成された英語文章")
    meaning = models.TextField(blank=True, default="", help_text="英語文章の和訳")
    is_translated = models.BooleanField(default=False, help_text="翻訳済みかどうか")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "english_texts"
        ordering = ["-created_at"]
