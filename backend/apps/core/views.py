from django.db.models import Avg, Count, F, Q
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lesson_plans.models import LessonPlanBatch
from apps.lesson_plans.policies import is_admin_user
from apps.reviews.models import LessonPlanReview


class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "lesson-plan-review-system",
                "version": "1.0.0",
            }
        )


class DashboardStatsAPIView(APIView):
    def get(self, request):
        user = request.user
        admin_view = is_admin_user(user)
        ready_batches = LessonPlanBatch.objects.filter(status=LessonPlanBatch.Status.READY)
        my_uploads = LessonPlanBatch.objects.filter(uploader=user)
        pending_reviews = ready_batches.exclude(reviews__reviewer=user).exclude(uploader=user)

        overview = {
            "total_batches": LessonPlanBatch.objects.count(),
            "ready_batches": ready_batches.count(),
            "my_upload_count": my_uploads.count(),
            "my_review_count": LessonPlanReview.objects.filter(reviewer=user).count(),
            "pending_review_count": pending_reviews.count(),
            "my_upload_average_score": round(
                my_uploads.aggregate(value=Avg("average_total_score"))["value"] or 0,
                2,
            ),
        }

        ranking_source = ready_batches if admin_view else my_uploads
        latest_batches = (
            ranking_source.select_related("uploader")
            .order_by("-created_at")[:5]
            .values(
                "id",
                "title",
                "subject",
                "grade_level",
                "average_total_score",
                "review_count",
                uploader_name=F("uploader__display_name"),
            )
        )
        high_score_batches = (
            ranking_source.filter(review_count__gt=0)
            .order_by("-average_total_score", "-review_count")[:5]
            .values("id", "title", "average_total_score", "review_count")
        )
        if admin_view:
            recommendation_totals = LessonPlanReview.objects.aggregate(
                strong_recommend=Count(
                    "id",
                    filter=Q(recommendation=LessonPlanReview.Recommendation.STRONG_RECOMMEND),
                ),
                recommend=Count(
                    "id",
                    filter=Q(recommendation=LessonPlanReview.Recommendation.RECOMMEND),
                ),
                revise=Count("id", filter=Q(recommendation=LessonPlanReview.Recommendation.REVISE)),
            )
        else:
            recommendation_totals = {}

        return Response(
            {
                "overview": overview,
                "can_view_global_rankings": admin_view,
                "latest_batches": list(latest_batches),
                "high_score_batches": list(high_score_batches),
                "recommendation_totals": recommendation_totals,
            }
        )
