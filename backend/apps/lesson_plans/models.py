import uuid
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Avg, Count

from apps.core.models import TimeStampedModel


def lesson_plan_upload_path(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    return f"lesson-plans/{instance.batch_id}/{instance.slot_number}{extension}"


def lesson_plan_preview_path(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower() or ".pdf"
    return f"lesson-plans/{instance.batch_id}/previews/{instance.slot_number}{extension}"


class LessonPlanBatch(TimeStampedModel):
    class Status(models.TextChoices):
        PROCESSING = "processing", "解析中"
        READY = "ready", "可评价"
        FAILED = "failed", "解析失败"
        ARCHIVED = "archived", "已归档"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="批次标题")
    subject = models.CharField(max_length=100, verbose_name="学科")
    grade_level = models.CharField(max_length=100, verbose_name="适用学段/年级")
    academic_year = models.CharField(max_length=50, blank=True, verbose_name="学年")
    teaching_theme = models.CharField(max_length=200, blank=True, verbose_name="教学主题")
    cover_summary = models.TextField(blank=True, verbose_name="批次说明")
    review_deadline = models.DateField(null=True, blank=True, verbose_name="评价截止日期")
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_batches",
        verbose_name="上传人",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
        verbose_name="状态",
    )
    ready_document_count = models.PositiveSmallIntegerField(default=0, verbose_name="已完成解析文档数")
    review_count = models.PositiveIntegerField(default=0, verbose_name="评价数")
    average_total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="平均总分",
    )

    class Meta:
        verbose_name = "教案批次"
        verbose_name_plural = "教案批次"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_review_open(self) -> bool:
        return self.status == self.Status.READY

    def refresh_processing_status(self, save: bool = True) -> None:
        ready_count = self.documents.filter(parse_status=LessonPlanDocument.ParseStatus.READY).count()
        failed_count = self.documents.filter(parse_status=LessonPlanDocument.ParseStatus.FAILED).count()

        self.ready_document_count = ready_count
        if ready_count == 2:
            self.status = self.Status.READY
        elif failed_count > 0 and ready_count + failed_count == 2:
            self.status = self.Status.FAILED
        else:
            self.status = self.Status.PROCESSING

        if save:
            self.save(update_fields=["ready_document_count", "status", "updated_at"])

    def refresh_review_summary(self, save: bool = True) -> None:
        summary = self.reviews.aggregate(avg_score=Avg("total_score"), total=Count("id"))
        average = summary["avg_score"] or Decimal("0.00")
        self.average_total_score = Decimal(average).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.review_count = summary["total"] or 0
        if save:
            self.save(update_fields=["average_total_score", "review_count", "updated_at"])


class LessonPlanDocument(TimeStampedModel):
    class DisplayMode(models.TextChoices):
        HTML = "html", "HTML 渲染"
        PDF = "pdf", "版式预览"

    class ParseStatus(models.TextChoices):
        PENDING = "pending", "待解析"
        PROCESSING = "processing", "解析中"
        READY = "ready", "已完成"
        FAILED = "failed", "失败"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        LessonPlanBatch,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="所属批次",
    )
    slot_number = models.PositiveSmallIntegerField(verbose_name="组内顺序")
    title = models.CharField(max_length=200, verbose_name="教案标题")
    original_file = models.FileField(upload_to=lesson_plan_upload_path, verbose_name="原始文件")
    original_filename = models.CharField(max_length=255, verbose_name="原始文件名")
    file_extension = models.CharField(max_length=20, verbose_name="文件扩展名")
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小")
    parse_status = models.CharField(
        max_length=20,
        choices=ParseStatus.choices,
        default=ParseStatus.PENDING,
        verbose_name="解析状态",
    )
    display_mode = models.CharField(
        max_length=20,
        choices=DisplayMode.choices,
        default=DisplayMode.HTML,
        verbose_name="展示方式",
    )
    preview_file = models.FileField(
        upload_to=lesson_plan_preview_path,
        blank=True,
        null=True,
        verbose_name="预览文件",
    )
    extracted_text = models.TextField(blank=True, verbose_name="抽取文本")
    rendered_html = models.TextField(blank=True, verbose_name="渲染 HTML")
    parse_error = models.TextField(blank=True, verbose_name="解析错误")
    page_count = models.PositiveIntegerField(default=0, verbose_name="页数")
    word_count = models.PositiveIntegerField(default=0, verbose_name="字数")

    class Meta:
        verbose_name = "教案文档"
        verbose_name_plural = "教案文档"
        ordering = ["slot_number", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "slot_number"],
                name="unique_document_slot_per_batch",
            )
        ]

    def __str__(self) -> str:
        return f"{self.batch.title} - 教案{self.slot_number}"
