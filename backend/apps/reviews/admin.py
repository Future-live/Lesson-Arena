from django.contrib import admin

from apps.reviews.models import LessonPlanReview, LessonPlanReviewDimensionScore, LessonPlanReviewFileSnapshot


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


@admin.register(LessonPlanReviewFileSnapshot)
class LessonPlanReviewFileSnapshotAdmin(admin.ModelAdmin):
    list_display = ("batch", "reviewer", "document_a", "document_b", "updated_at")
    list_filter = ("updated_at",)
    search_fields = (
        "batch__title",
        "reviewer__display_name",
        "original_filename_a",
        "original_filename_b",
    )
    readonly_fields = (
        "review",
        "batch",
        "reviewer",
        "document_a",
        "document_b",
        "original_file_a",
        "original_file_b",
        "preview_file_a",
        "preview_file_b",
        "original_filename_a",
        "original_filename_b",
        "dimension_scores_a",
        "dimension_scores_b",
        "created_at",
        "updated_at",
    )
