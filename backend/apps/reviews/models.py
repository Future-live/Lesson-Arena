import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class LessonPlanReview(TimeStampedModel):
    class Recommendation(models.TextChoices):
        STRONG_RECOMMEND = "strong_recommend", "强烈推荐"
        RECOMMEND = "recommend", "建议采用"
        REVISE = "revise", "建议修改后再用"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        "lesson_plans.LessonPlanBatch",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="所属批次",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_plan_reviews",
        verbose_name="评价人",
    )
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="总分",
    )
    total_score_a = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="教案A总分",
    )
    total_score_b = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="教案B总分",
    )
    recommendation = models.CharField(
        max_length=30,
        choices=Recommendation.choices,
        verbose_name="结论建议",
    )
    overall_comment = models.TextField(verbose_name="总体评价")
    comparative_comment = models.TextField(blank=True, verbose_name="双教案比较")
    strengths = models.TextField(blank=True, verbose_name="优势亮点")
    improvement_suggestions = models.TextField(blank=True, verbose_name="改进建议")
    submitted_at = models.DateTimeField(auto_now=True, verbose_name="提交时间")

    class Meta:
        verbose_name = "教案评价"
        verbose_name_plural = "教案评价"
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "reviewer"],
                name="unique_review_per_batch_per_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.reviewer} - {self.batch}"

    def recalculate_total(self) -> Decimal:
        weighted_score_a = Decimal("0.00")
        weighted_score_b = Decimal("0.00")
        for item in self.dimension_scores.all():
            weighted_score_a += Decimal(item.score_a) * item.weight
            weighted_score_b += Decimal(item.score_b) * item.weight
        self.total_score_a = weighted_score_a.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.total_score_b = weighted_score_b.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.total_score = ((self.total_score_a + self.total_score_b) / Decimal("2")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        return self.total_score


class LessonPlanReviewDimensionScore(TimeStampedModel):
    review = models.ForeignKey(
        LessonPlanReview,
        on_delete=models.CASCADE,
        related_name="dimension_scores",
        verbose_name="所属评价",
    )
    dimension_key = models.CharField(max_length=64, verbose_name="维度标识")
    dimension_name = models.CharField(max_length=100, verbose_name="维度名称")
    weight = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="权重")
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="综合分数",
    )
    score_a = models.PositiveSmallIntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="教案A分数",
    )
    score_b = models.PositiveSmallIntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="教案B分数",
    )
    comment = models.TextField(blank=True, verbose_name="维度说明")

    class Meta:
        verbose_name = "维度评分"
        verbose_name_plural = "维度评分"
        ordering = ["dimension_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["review", "dimension_key"],
                name="unique_dimension_score_per_review",
            )
        ]

    def __str__(self) -> str:
        return f"{self.dimension_name} - {self.score}"
