from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TextPair",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("kanji", models.TextField(help_text="生成された漢字文章")),
                (
                    "hiragana",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="漢字文章をひらがな化した結果",
                    ),
                ),
                (
                    "is_converted",
                    models.BooleanField(
                        default=False, help_text="ひらがな変換済みかどうか"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "text_pairs",
                "ordering": ["-created_at"],
            },
        ),
    ]


