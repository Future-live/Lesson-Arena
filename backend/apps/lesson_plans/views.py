from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.lesson_plans.models import LessonPlanBatch
from apps.lesson_plans.serializers import (
    LessonPlanBatchCreateSerializer,
    LessonPlanBatchDetailSerializer,
    LessonPlanBatchListSerializer,
)


class LessonPlanBatchListCreateAPIView(generics.ListCreateAPIView):
    queryset = LessonPlanBatch.objects.select_related("uploader").prefetch_related("documents")
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "subject", "grade_level"]
    search_fields = ["title", "subject", "grade_level", "teaching_theme", "uploader__display_name"]
    ordering_fields = ["created_at", "average_total_score", "review_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        scope = self.request.query_params.get("scope")
        if scope == "mine":
            queryset = queryset.filter(uploader=self.request.user)
        elif scope == "pending_review":
            queryset = queryset.filter(status=LessonPlanBatch.Status.READY).exclude(
                uploader=self.request.user
            ).exclude(reviews__reviewer=self.request.user)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LessonPlanBatchCreateSerializer
        return LessonPlanBatchListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = serializer.save()
        response_serializer = LessonPlanBatchDetailSerializer(batch, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class LessonPlanBatchRetrieveAPIView(generics.RetrieveAPIView):
    queryset = LessonPlanBatch.objects.select_related("uploader").prefetch_related(
        "documents",
        "reviews__dimension_scores",
        "reviews__reviewer",
    )
    serializer_class = LessonPlanBatchDetailSerializer
