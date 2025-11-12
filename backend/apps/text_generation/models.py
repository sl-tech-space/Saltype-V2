from django.db import models


class TextPair(models.Model):
    """
    テキスト生成ジョブで作成される漢字・ひらがなペアを保持するモデル。
    """

    id = models.BigAutoField(primary_key=True)
    kanji = models.TextField(help_text="生成された漢字文章")
    hiragana = models.TextField(blank=True, default="", help_text="漢字文章をひらがな化した結果")
    is_converted = models.BooleanField(default=False, help_text="ひらがな変換済みかどうか")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "text_pairs"
        ordering = ["-created_at"]


