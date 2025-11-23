import logging
import random

from django.db.models import Min, Max

from apps.common.views import BaseView
from apps.text_generation.models import TextPair, EnglishText
from apps.text_generation.serializers import GetRandomTextPairSerializer

logger = logging.getLogger("app")


def _get_random_records(model_class, count=30, filter_kwargs=None):
    """指定されたモデルから指定された数の完全ランダムなレコードを取得する。
    ORDER BY ? を避け、IDレンジベースのランダム選択で効率的に取得。
    """
    if filter_kwargs is None:
        filter_kwargs = {}

    # レコードの総数を取得
    total_count = model_class.objects.filter(**filter_kwargs).count()
    if total_count == 0:
        return []

    if total_count <= count:
        # 総数が要求数以下の場合は全件返す
        return list(model_class.objects.filter(**filter_kwargs))

    # IDレンジを取得
    agg = model_class.objects.filter(**filter_kwargs).aggregate(
        min_id=Min("id"), max_id=Max("id")
    )
    min_id = agg.get("min_id")
    max_id = agg.get("max_id")

    if min_id is None or max_id is None:
        return []

    # 重複を避けてランダムなIDを生成
    selected_ids = set()
    attempts = 0
    max_attempts = count * 10  # 無限ループ防止

    while len(selected_ids) < count and attempts < max_attempts:
        candidate_id = random.randint(min_id, max_id)
        # そのIDが実際に存在するかチェック
        if model_class.objects.filter(id=candidate_id, **filter_kwargs).exists():
            selected_ids.add(candidate_id)
        attempts += 1

    # 選択されたIDのレコードを取得
    records = list(
        model_class.objects.filter(id__in=selected_ids, **filter_kwargs).order_by("id")
    )

    # 要求数に満たない場合は追加取得
    if len(records) < count:
        remaining = count - len(records)
        # まだ選択されていないIDから追加取得
        remaining_records = list(
            model_class.objects.filter(**filter_kwargs)
            .exclude(id__in=selected_ids)
            .order_by("?")[:remaining]
        )
        records.extend(remaining_records)

    return records[:count]


class GetRandomTextPairView(BaseView):
    """
    文章をランダムに取得するAPIビュークラス。
    """

    def post(self, request, *args, **kwargs):
        return super().post(request, GetRandomTextPairSerializer, *args, **kwargs)

    def handle_post_request(self, validated_data: dict) -> dict:
        """
        リクエストデータに基づいてランダムな文章ペアを取得します。
        Args:
            validated_data (dict): 検証済みのリクエストデータ。
                - count (int, optional): 取得件数（デフォルト: 30、最大: 100）
                - lang_id (int, optional): 言語ID (1: 日本語, 2: 英語)
        Returns:
            dict: データを含むレスポンス
                - status (str): 処理結果のステータス
                - success (bool): 成功フラグ
                - data (list): 文章データのリスト
                    - id (int): ID
                    - kanji (str): 漢字文章/英語文章
                    - hiragana (str): ひらがな文章/英語文章（英語の場合はkanjiと同じ）
        """
        count = validated_data.get("count", 30)
        lang_id = validated_data.get("lang_id", 1)
        logger.info(f"ランダム文章ペア取得開始: count={count}, lang_id={lang_id}")

        try:
            data_list = []
            if str(lang_id) == "2":  # 英語
                # 翻訳済みの英語文章を取得
                english_texts = _get_random_records(
                    EnglishText, count=count, filter_kwargs={"is_translated": True}
                )
                data_list = [
                    {
                        "id": text.id,
                        "kanji": text.content,
                        "hiragana": text.content,
                        "meaning": text.meaning,
                    }
                    for text in english_texts
                ]
            else:  # 日本語 (デフォルト)
                text_pairs = _get_random_records(
                    TextPair, count=count, filter_kwargs={"is_converted": True}
                )
                data_list = [
                    {
                        "id": text_pair.id,
                        "kanji": text_pair.kanji,
                        "hiragana": text_pair.hiragana,
                    }
                    for text_pair in text_pairs
                ]

            if not data_list:
                logger.warning(f"文章データが見つかりませんでした: lang_id={lang_id}")
                return {
                    "status": "success",
                    "success": False,
                    "data": [],
                }

            logger.info(
                f"ランダム文章ペア取得完了: count={len(data_list)}, lang_id={lang_id}"
            )
            return {
                "status": "success",
                "success": True,
                "data": data_list,
            }

        except Exception as e:
            logger.error(f"ランダム文章ペア取得エラー: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "success": False,
                "data": [],
            }
