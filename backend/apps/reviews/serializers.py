from django.db import transaction
from rest_framework import serializers

from apps.reviews.models import LessonPlanReview, LessonPlanReviewDimensionScore
from apps.reviews.rubric import DIMENSION_MAP, REVIEW_DIMENSIONS
from apps.reviews.services import calculate_pair_total_scores


class ReviewDimensionDefinitionSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    weight = serializers.FloatField()


class LessonPlanReviewDimensionScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonPlanReviewDimensionScore
        fields = (
            "dimension_key",
            "dimension_name",
            "weight",
            "score",
            "score_a",
            "score_b",
            "comment",
        )
        read_only_fields = fields


class LessonPlanReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.display_name", read_only=True)
    dimension_scores = LessonPlanReviewDimensionScoreSerializer(many=True, read_only=True)

    class Meta:
        model = LessonPlanReview
        fields = (
            "id",
            "reviewer",
            "reviewer_name",
            "total_score",
            "total_score_a",
            "total_score_b",
            "recommendation",
            "overall_comment",
            "comparative_comment",
            "strengths",
            "improvement_suggestions",
            "submitted_at",
            "dimension_scores",
        )
        read_only_fields = fields


class ReviewDimensionScoreInputSerializer(serializers.Serializer):
    dimension_key = serializers.CharField()
    score = serializers.IntegerField(min_value=1, max_value=10, required=False)
    score_a = serializers.IntegerField(min_value=1, max_value=10, required=False)
    score_b = serializers.IntegerField(min_value=1, max_value=10, required=False)
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        has_pair_scores = "score_a" in attrs and "score_b" in attrs
        has_legacy_score = "score" in attrs
        if not has_pair_scores and not has_legacy_score:
            raise serializers.ValidationError("每个维度必须提交教案 A 与教案 B 的分数。")
        if not has_pair_scores and has_legacy_score:
            attrs["score_a"] = attrs["score"]
            attrs["score_b"] = attrs["score"]
        if "score" not in attrs:
            attrs["score"] = (attrs["score_a"] + attrs["score_b"] + 1) // 2
        return attrs


class ReviewUpsertSerializer(serializers.Serializer):
    recommendation = serializers.ChoiceField(choices=LessonPlanReview.Recommendation.choices)
    overall_comment = serializers.CharField()
    comparative_comment = serializers.CharField(required=False, allow_blank=True)
    strengths = serializers.CharField(required=False, allow_blank=True)
    improvement_suggestions = serializers.CharField(required=False, allow_blank=True)
    dimension_scores = ReviewDimensionScoreInputSerializer(many=True)

    def validate_dimension_scores(self, value):
        submitted_keys = [item["dimension_key"] for item in value]
        expected_keys = [item["key"] for item in REVIEW_DIMENSIONS]
        if sorted(submitted_keys) != sorted(expected_keys):
            raise serializers.ValidationError("维度评分必须完整覆盖全部评价维度，且不能重复。")
        return value

    @transaction.atomic
    def save(self, **kwargs):
        batch = self.context["batch"]
        reviewer = self.context["request"].user
        validated_data = self.validated_data
        dimension_scores = validated_data.pop("dimension_scores")

        review, _ = LessonPlanReview.objects.get_or_create(
            batch=batch,
            reviewer=reviewer,
            defaults=validated_data,
        )

        for field, value in validated_data.items():
            setattr(review, field, value)
        review.save()
        review.dimension_scores.all().delete()

        payload_for_total = []
        for item in dimension_scores:
            dimension = DIMENSION_MAP[item["dimension_key"]]
            combined_score = (item["score_a"] + item["score_b"] + 1) // 2
            score_item = LessonPlanReviewDimensionScore.objects.create(
                review=review,
                dimension_key=dimension["key"],
                dimension_name=dimension["label"],
                weight=dimension["weight"],
                score=combined_score,
                score_a=item["score_a"],
                score_b=item["score_b"],
                comment=item.get("comment", ""),
            )
            payload_for_total.append(
                {
                    "score_a": score_item.score_a,
                    "score_b": score_item.score_b,
                    "weight": score_item.weight,
                }
            )

        review.total_score_a, review.total_score_b, review.total_score = calculate_pair_total_scores(payload_for_total)
        review.save(update_fields=["total_score", "total_score_a", "total_score_b", "submitted_at", "updated_at"])
        batch.refresh_review_summary(save=True)
        return review
