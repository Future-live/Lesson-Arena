from django.contrib import admin

from apps.reviews.models import LessonPlanReview, LessonPlanReviewDimensionScore


class LessonPlanReviewDimensionScoreInline(admin.TabularInline):
    model = LessonPlanReviewDimensionScore
    extra = 0


@admin.register(LessonPlanReview)
class LessonPlanReviewAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "reviewer",
        "total_score",
        "recommendation",
        "submitted_at",
    )
    list_filter = ("recommendation", "submitted_at")
    search_fields = ("batch__title", "reviewer__display_name", "overall_comment")
    inlines = [LessonPlanReviewDimensionScoreInline]


@admin.register(LessonPlanReviewDimensionScore)
class LessonPlanReviewDimensionScoreAdmin(admin.ModelAdmin):
    list_display = ("review", "dimension_name", "score_a", "score_b", "score", "weight")
    list_filter = ("dimension_key",)
    search_fields = ("review__batch__title", "dimension_name", "comment")
