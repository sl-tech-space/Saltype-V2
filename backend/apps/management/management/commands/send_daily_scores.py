import logging
from collections import OrderedDict
from datetime import date

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from apps.common.models import User
from apps.common.util.score_util import ScoreUtil

logger = logging.getLogger("app")


class Command(BaseCommand):
    help = "本日のベストスコアをメールで送信する"
    command_name = "send_daily_scores"

    def handle(self, *args, **options):
        get_score_user_emails = settings.GET_SCORES_EMAILS
        to_sending_emails = settings.TO_SEND_EMAILS
        host_email = settings.EMAIL_HOST_USER

        today = date.today()
        scores_by_diff_and_lang = {}

        for email in get_score_user_emails:
            user = User.objects.get(email=email)

            diff_lang_scores = (
                ScoreUtil.get_today_highest_scores_by_difficulty_and_lang(user)
            )

            for (difficulty, language), score in diff_lang_scores.items():
                if score is None:
                    continue

                key = f"{difficulty}_{language}"
                scores_by_diff_and_lang.setdefault(key, []).append(
                    {
                        "user__username": user.username,
                        "max_score": score,
                        "difficulty": difficulty,
                        "language": language,
                    }
                )

        for key in scores_by_diff_and_lang:
            scores_by_diff_and_lang[key].sort(
                key=lambda x: x["max_score"], reverse=True
            )
            scores_by_diff_and_lang[key] = list(
                enumerate(scores_by_diff_and_lang[key], start=1)
            )

        language_order = ["日本語", "英語"]
        difficulty_order = ["イージー", "ノーマル", "ハード"]

        scores_by_language = OrderedDict()
        for lang in language_order:
            scores_by_language[lang] = OrderedDict(
                (diff, []) for diff in difficulty_order
            )

        for scores in scores_by_diff_and_lang.values():
            if not scores:
                continue

            language = scores[0][1]["language"]
            difficulty = scores[0][1]["difficulty"]

            if language not in scores_by_language:
                scores_by_language[language] = OrderedDict(
                    (diff, []) for diff in difficulty_order
                )

            if difficulty not in scores_by_language[language]:
                scores_by_language[language][difficulty] = []

            scores_by_language[language][difficulty] = scores

        today_str = today.strftime("%m/%d")
        subject = f"{today_str} - 新卒タイピングスコアランキング"

        html_message = render_to_string(
            "management/best_score_email_template.html",
            {"today_str": today_str, "scores_by_language": scores_by_language},
        )

        send_mail(
            subject,
            "",
            host_email,
            to_sending_emails,
            html_message=html_message,
        )
        logger.info("日次スコアメールを送信しました")
