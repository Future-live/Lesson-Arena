from django.contrib import admin

from apps.lesson_plans.models import LessonPlanBatch, LessonPlanDocument


class LessonPlanDocumentInline(admin.TabularInline):
    model = LessonPlanDocument
    extra = 0
    readonly_fields = (
        "slot_number",
        "title",
        "original_filename",
        "file_extension",
        "parse_status",
        "display_mode",
        "page_count",
        "word_count",
    )


@admin.register(LessonPlanBatch)
class LessonPlanBatchAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subject",
        "grade_level",
        "uploader",
        "status",
        "review_count",
        "average_total_score",
        "created_at",
    )
    list_filter = ("status", "subject", "grade_level", "created_at")
    search_fields = ("title", "subject", "grade_level", "uploader__display_name")
    readonly_fields = ("average_total_score", "review_count", "ready_document_count")
    inlines = [LessonPlanDocumentInline]


@admin.register(LessonPlanDocument)
class LessonPlanDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "batch",
        "slot_number",
        "file_extension",
        "parse_status",
        "display_mode",
        "page_count",
        "word_count",
        "created_at",
    )
    list_filter = ("parse_status", "file_extension", "created_at")
    search_fields = ("title", "original_filename", "batch__title")
    readonly_fields = ("preview_file", "rendered_html", "extracted_text", "parse_error")
