from rest_framework import serializers
from apps.common.serializers import BaseSerializer


class GoogleAuthSerializer(BaseSerializer):
    """
    ユーザーがGoogle認証を行うためのシリアライザー。
    """

    email = serializers.EmailField(max_length=256, required=True)  # メールアドレス
    username = serializers.CharField(max_length=15, required=False)  # ユーザー名

    def validate(self, attrs):
        """
        リクエストデータに対してバリデーションを実行します。
        """
        attrs = self.check_email(attrs)
        attrs = self.check_username(attrs)
        return attrs
