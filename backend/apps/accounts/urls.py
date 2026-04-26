from django.urls import path

from apps.accounts.views import LoginAPIView, MeAPIView, RefreshTokenAPIView, RegisterAPIView


urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("refresh/", RefreshTokenAPIView.as_view(), name="refresh"),
    path("me/", MeAPIView.as_view(), name="me"),
]
