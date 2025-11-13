import logging
import random

from django.db.models import Min, Max

from apps.common.views import BaseView
from apps.text_generation.models import TextPair
from apps.text_generation.serializers import GetRandomTextPairSerializer

logger = logging.getLogger("app")


def _get_random_converted_text_pairs(count=30):
    """変換済みTextPairから指定された数の完全ランダムなペアを取得する。
    ORDER BY ? を避け、IDレンジベースのランダム選択で効率的に取得。
    """
    # 変換済みレコードの総数を取得
    total_count = TextPair.objects.filter(is_converted=True).count()
    if total_count == 0:
        return []

    if total_count <= count:
        # 総数が要求数以下の場合は全件返す
        return list(TextPair.objects.filter(is_converted=True))

    # IDレンジを取得
    agg = TextPair.objects.filter(is_converted=True).aggregate(
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
        if TextPair.objects.filter(id=candidate_id, is_converted=True).exists():
            selected_ids.add(candidate_id)
        attempts += 1

    # 選択されたIDのTextPairを取得
    text_pairs = list(
        TextPair.objects.filter(id__in=selected_ids, is_converted=True).order_by("id")
    )

    # 要求数に満たない場合は追加取得
    if len(text_pairs) < count:
        remaining = count - len(text_pairs)
        # まだ選択されていないIDから追加取得
        remaining_pairs = list(
            TextPair.objects.filter(is_converted=True)
            .exclude(id__in=selected_ids)
            .order_by("?")[:remaining]
        )
        text_pairs.extend(remaining_pairs)

    return text_pairs[:count]


class GetRandomTextPairView(BaseView):
    """
    変換済みのTextPairをランダムに取得するAPIビュークラス。
    """

    def post(self, request, *args, **kwargs):
        return super().post(request, GetRandomTextPairSerializer, *args, **kwargs)

    def handle_post_request(self, validated_data: dict) -> dict:
        """
        リクエストデータに基づいてランダムなTextPairを取得します。
        Args:
            validated_data (dict): 検証済みのリクエストデータ。
                - count (int, optional): 取得件数（デフォルト: 30、最大: 100）
        Returns:
            dict: TextPairデータを含むレスポンス
                - status (str): 処理結果のステータス
                - success (bool): 成功フラグ
                - data (list): TextPairデータのリスト
                    - id (int): TextPairのID
                    - kanji (str): 漢字文章
                    - hiragana (str): ひらがな文章
        """
        count = validated_data.get("count", 30)
        logger.info(f"ランダムTextPairペア{count}件取得開始")

        try:
            # 変換済み（is_converted=True）のレコードからランダムに取得（高効率）
            text_pairs = _get_random_converted_text_pairs(count=count)

            if not text_pairs:
                logger.warning("変換済みのTextPairが見つかりませんでした")
                return {
                    "status": "success",
                    "success": False,
                    "data": [],
                }

            logger.info(f"ランダムTextPairペア{count}件取得完了: count={len(text_pairs)}")
            return {
                "status": "success",
                "success": True,
                "data": [
                    {
                        "id": text_pair.id,
                        "kanji": text_pair.kanji,
                        "hiragana": text_pair.hiragana,
                    }
                    for text_pair in text_pairs
                ],
            }

        except Exception as e:
            logger.error(f"ランダムTextPairペア取得エラー: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "success": False,
                "data": [],
            }

