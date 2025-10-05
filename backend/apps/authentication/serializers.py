from rest_framework import serializers
from apps.common.serializers import BaseSerializer
from django.conf import settings


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
        attrs = self.check_domain(attrs)
        return attrs

    def check_domain(self, attrs):
        """
        メールアドレスのドメインが許可されたドメインかチェックします。
        """
        email = attrs.get("email", "")
        allowed_domain = settings.ALLOWED_EMAIL_DOMAIN

        if email and not email.endswith(allowed_domain):
            domain_name = allowed_domain.lstrip("@")
            raise serializers.ValidationError(
                {"email": f"{domain_name}ドメインのメールアドレスのみ使用可能です。"}
            )
        return attrs
