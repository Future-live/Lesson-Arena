from django.urls import path

from apps.core.views import DashboardStatsAPIView, HealthCheckAPIView


urlpatterns = [
    path("health/", HealthCheckAPIView.as_view(), name="health-check"),
    path("dashboard/", DashboardStatsAPIView.as_view(), name="dashboard-stats"),
]
