from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def _file_name(file_field) -> str:
    return file_field.name if file_field else ""


def _build_dimension_payloads(review, DimensionScore) -> tuple[dict, dict]:
    scores_a = {}
    scores_b = {}
    for item in DimensionScore.objects.filter(review=review):
        base_payload = {
            "dimension_name": item.dimension_name,
            "weight": str(item.weight),
            "comment": item.comment,
        }
        scores_a[item.dimension_key] = {**base_payload, "score": item.score_a}
        scores_b[item.dimension_key] = {**base_payload, "score": item.score_b}
    return scores_a, scores_b


def backfill_file_snapshots(apps, schema_editor):
    Review = apps.get_model("reviews", "LessonPlanReview")
    DimensionScore = apps.get_model("reviews", "LessonPlanReviewDimensionScore")
    FileSnapshot = apps.get_model("reviews", "LessonPlanReviewFileSnapshot")
    Document = apps.get_model("lesson_plans", "LessonPlanDocument")

    for review in Review.objects.select_related("batch", "reviewer").iterator():
        document_a = Document.objects.filter(batch=review.batch, slot_number=1).first()
        document_b = Document.objects.filter(batch=review.batch, slot_number=2).first()
        scores_a, scores_b = _build_dimension_payloads(review, DimensionScore)

        FileSnapshot.objects.update_or_create(
            review=review,
            defaults={
                "batch": review.batch,
                "reviewer": review.reviewer,
                "document_a": document_a,
                "document_b": document_b,
                "original_file_a": _file_name(document_a.original_file) if document_a else "",
                "original_file_b": _file_name(document_b.original_file) if document_b else "",
                "preview_file_a": _file_name(document_a.preview_file) if document_a else "",
                "preview_file_b": _file_name(document_b.preview_file) if document_b else "",
                "original_filename_a": document_a.original_filename if document_a else "",
                "original_filename_b": document_b.original_filename if document_b else "",
                "dimension_scores_a": scores_a,
                "dimension_scores_b": scores_b,
            },
        )


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("lesson_plans", "0002_lessonplandocument_display_mode_and_more"),
        ("reviews", "0002_lessonplanreview_total_score_a_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="LessonPlanReviewFileSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("original_file_a", models.FileField(blank=True, max_length=500, verbose_name="教案A原始文件")),
                ("original_file_b", models.FileField(blank=True, max_length=500, verbose_name="教案B原始文件")),
                ("preview_file_a", models.FileField(blank=True, max_length=500, verbose_name="教案A PDF预览文件")),
                ("preview_file_b", models.FileField(blank=True, max_length=500, verbose_name="教案B PDF预览文件")),
                ("original_filename_a", models.CharField(blank=True, max_length=255, verbose_name="教案A原始文件名")),
                ("original_filename_b", models.CharField(blank=True, max_length=255, verbose_name="教案B原始文件名")),
                ("dimension_scores_a", models.JSONField(default=dict, verbose_name="教案A各维度评分")),
                ("dimension_scores_b", models.JSONField(default=dict, verbose_name="教案B各维度评分")),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="review_file_snapshots",
                        to="lesson_plans.lessonplanbatch",
                        verbose_name="所属批次",
                    ),
                ),
                (
                    "document_a",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="lesson_plans.lessonplandocument",
                        verbose_name="教案A文档",
                    ),
                ),
                (
                    "document_b",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="lesson_plans.lessonplandocument",
                        verbose_name="教案B文档",
                    ),
                ),
                (
                    "review",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="file_snapshot",
                        to="reviews.lessonplanreview",
                        verbose_name="所属评价",
                    ),
                ),
                (
                    "reviewer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lesson_plan_review_file_snapshots",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="评价人",
                    ),
                ),
            ],
            options={
                "verbose_name": "评价文件评分快照",
                "verbose_name_plural": "评价文件评分快照",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.RunPython(backfill_file_snapshots, noop_reverse),
    ]
