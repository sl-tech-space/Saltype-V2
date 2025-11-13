from rest_framework import serializers
from apps.common.serializers import BaseSerializer


class GetRandomTextPairSerializer(BaseSerializer):
    """
    ランダムTextPair取得に関連するリクエストデータを検証するシリアライザクラス
    """

    count = serializers.IntegerField(
        required=False, min_value=1, max_value=100, default=30
    )

    def validate(self, attrs):
        """
        リクエストデータに対してバリデーションを実行します。
        """
        return attrs
