from django.urls import include, path

from .views import CheckTokenView, GoogleAuthView

urlpatterns = [
    path("auth-token/", CheckTokenView.as_view(), name="token_login"),
    path("google-auth/", GoogleAuthView.as_view(), name="google_login"),
    path("auth/", include("drf_social_oauth2.urls", namespace="drf")),
]
