from django.urls import path

from apps.lesson_plans.views import LessonPlanBatchListCreateAPIView, LessonPlanBatchRetrieveAPIView


urlpatterns = [
    path("", LessonPlanBatchListCreateAPIView.as_view(), name="batch-list-create"),
    path("<uuid:pk>/", LessonPlanBatchRetrieveAPIView.as_view(), name="batch-detail"),
]
