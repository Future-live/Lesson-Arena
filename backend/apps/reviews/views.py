from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lesson_plans.models import LessonPlanBatch
from apps.reviews.rubric import REVIEW_DIMENSIONS
from apps.reviews.serializers import (
    LessonPlanReviewSerializer,
    ReviewDimensionDefinitionSerializer,
    ReviewUpsertSerializer,
)


class ReviewDimensionListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ReviewDimensionDefinitionSerializer(REVIEW_DIMENSIONS, many=True)
        return Response(serializer.data)


class MyBatchReviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, batch_id):
        batch = get_object_or_404(LessonPlanBatch, pk=batch_id)
        if batch.status != LessonPlanBatch.Status.READY:
            return Response({"detail": "教案尚未解析完成，暂不可评价。"}, status=status.HTTP_400_BAD_REQUEST)
        exists = batch.reviews.filter(reviewer=request.user).exists()

        serializer = ReviewUpsertSerializer(
            data=request.data,
            context={"request": request, "batch": batch},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            LessonPlanReviewSerializer(review).data,
            status=status.HTTP_200_OK if exists else status.HTTP_201_CREATED,
        )
