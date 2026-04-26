from collections import Counter
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg

from apps.reviews.models import LessonPlanReview
from apps.reviews.rubric import REVIEW_DIMENSIONS


def calculate_total_score(dimension_scores: list[dict]) -> Decimal:
    total = Decimal("0.00")
    for item in dimension_scores:
        score = Decimal(str(item["score"]))
        weight = Decimal(str(item["weight"]))
        total += score * weight
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_pair_total_scores(dimension_scores: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
    total_a = Decimal("0.00")
    total_b = Decimal("0.00")
    for item in dimension_scores:
        weight = Decimal(str(item["weight"]))
        total_a += Decimal(str(item["score_a"])) * weight
        total_b += Decimal(str(item["score_b"])) * weight
    total_a = total_a.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_b = total_b.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = ((total_a + total_b) / Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return total_a, total_b, total


def build_batch_review_summary(batch) -> dict:
    reviews = list(batch.reviews.prefetch_related("dimension_scores", "reviewer"))
    dimension_averages: list[dict] = []

    for dimension in REVIEW_DIMENSIONS:
        average = (
            batch.reviews.filter(dimension_scores__dimension_key=dimension["key"])
            .aggregate(value=Avg("dimension_scores__score"))
            .get("value")
        )
        average_a = (
            batch.reviews.filter(dimension_scores__dimension_key=dimension["key"])
            .aggregate(value=Avg("dimension_scores__score_a"))
            .get("value")
        )
        average_b = (
            batch.reviews.filter(dimension_scores__dimension_key=dimension["key"])
            .aggregate(value=Avg("dimension_scores__score_b"))
            .get("value")
        )
        dimension_averages.append(
            {
                "key": dimension["key"],
                "label": dimension["label"],
                "weight": dimension["weight"],
                "average_score": round(average or 0, 2),
                "average_score_a": round(average_a or 0, 2),
                "average_score_b": round(average_b or 0, 2),
            }
        )

    recommendation_counter = Counter(review.recommendation for review in reviews)
    recent_reviews = [
        {
            "id": str(review.id),
            "reviewer_name": review.reviewer.display_name,
            "recommendation": review.recommendation,
            "total_score": float(review.total_score),
            "total_score_a": float(review.total_score_a),
            "total_score_b": float(review.total_score_b),
            "submitted_at": review.submitted_at,
        }
        for review in reviews[:5]
    ]

    return {
        "review_count": batch.review_count,
        "average_total_score": float(batch.average_total_score),
        "recommendation_distribution": {
            LessonPlanReview.Recommendation.STRONG_RECOMMEND: recommendation_counter.get(
                LessonPlanReview.Recommendation.STRONG_RECOMMEND,
                0,
            ),
            LessonPlanReview.Recommendation.RECOMMEND: recommendation_counter.get(
                LessonPlanReview.Recommendation.RECOMMEND,
                0,
            ),
            LessonPlanReview.Recommendation.REVISE: recommendation_counter.get(
                LessonPlanReview.Recommendation.REVISE,
                0,
            ),
        },
        "dimension_averages": dimension_averages,
        "recent_reviews": recent_reviews,
    }
