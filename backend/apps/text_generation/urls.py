from django.urls import path

from .views import GetRandomTextPairView

urlpatterns = [
    path("random", GetRandomTextPairView.as_view(), name="get_random_text_pair"),
]

