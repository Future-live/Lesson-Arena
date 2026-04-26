from pathlib import Path

from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.lesson_plans.models import LessonPlanBatch, LessonPlanDocument
from apps.lesson_plans.policies import can_view_batch_review_summary
from apps.lesson_plans.services import dispatch_document_parse


class UploaderSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ("id", "username", "display_name", "organization", "title")


class LessonPlanDocumentSerializer(serializers.ModelSerializer):
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = LessonPlanDocument
        fields = (
            "id",
            "slot_number",
            "title",
            "original_file",
            "original_filename",
            "file_extension",
            "file_size",
            "parse_status",
            "display_mode",
            "preview_file",
            "preview_url",
            "rendered_html",
            "extracted_text",
            "parse_error",
            "page_count",
            "word_count",
        )
        read_only_fields = fields

    def get_preview_url(self, obj):
        if obj.display_mode == LessonPlanDocument.DisplayMode.PDF:
            if obj.preview_file:
                return obj.preview_file.url
            if obj.original_file:
                return obj.original_file.url
        return None


class LessonPlanBatchListSerializer(serializers.ModelSerializer):
    uploader = UploaderSerializer(read_only=True)
    review_count = serializers.SerializerMethodField()
    average_total_score = serializers.SerializerMethodField()
    can_current_user_review = serializers.SerializerMethodField()
    current_user_reviewed = serializers.SerializerMethodField()
    can_view_review_summary = serializers.SerializerMethodField()

    class Meta:
        model = LessonPlanBatch
        fields = (
            "id",
            "title",
            "subject",
            "grade_level",
            "academic_year",
            "teaching_theme",
            "cover_summary",
            "review_deadline",
            "status",
            "ready_document_count",
            "review_count",
            "average_total_score",
            "created_at",
            "uploader",
            "can_current_user_review",
            "current_user_reviewed",
            "can_view_review_summary",
        )
        read_only_fields = fields

    def get_can_current_user_review(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.status == LessonPlanBatch.Status.READY

    def get_current_user_reviewed(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.reviews.filter(reviewer=request.user).exists()

    def get_can_view_review_summary(self, obj) -> bool:
        request = self.context.get("request")
        if not request:
            return False
        return can_view_batch_review_summary(request.user, obj)

    def get_review_count(self, obj):
        if self.get_can_view_review_summary(obj):
            return obj.review_count
        return None

    def get_average_total_score(self, obj):
        if self.get_can_view_review_summary(obj):
            return float(obj.average_total_score)
        return None


class LessonPlanBatchDetailSerializer(LessonPlanBatchListSerializer):
    documents = LessonPlanDocumentSerializer(many=True, read_only=True)
    review_summary = serializers.SerializerMethodField()
    current_user_review = serializers.SerializerMethodField()

    class Meta(LessonPlanBatchListSerializer.Meta):
        fields = LessonPlanBatchListSerializer.Meta.fields + (
            "documents",
            "review_summary",
            "current_user_review",
        )

    def get_review_summary(self, obj):
        from apps.reviews.services import build_batch_review_summary

        request = self.context.get("request")
        if not request or not can_view_batch_review_summary(request.user, obj):
            return None
        return build_batch_review_summary(obj)

    def get_current_user_review(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        from apps.reviews.serializers import LessonPlanReviewSerializer

        review = obj.reviews.filter(reviewer=request.user).prefetch_related("dimension_scores").first()
        if not review:
            return None
        return LessonPlanReviewSerializer(review).data


class LessonPlanBatchCreateSerializer(serializers.ModelSerializer):
    documents = serializers.ListField(
        child=serializers.FileField(),
        min_length=2,
        max_length=2,
        write_only=True,
    )

    class Meta:
        model = LessonPlanBatch
        fields = (
            "title",
            "subject",
            "grade_level",
            "academic_year",
            "teaching_theme",
            "cover_summary",
            "review_deadline",
            "documents",
        )

    def validate_documents(self, value):
        if len(value) != 2:
            raise serializers.ValidationError("每次必须上传恰好 2 个教案文件。")

        for file in value:
            extension = Path(file.name).suffix.lower()
            if extension not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
                raise serializers.ValidationError(
                    f"{file.name} 格式不受支持。当前支持：{', '.join(sorted(settings.ALLOWED_DOCUMENT_EXTENSIONS))}"
                )
            if file.size > settings.MAX_UPLOAD_SIZE_BYTES:
                raise serializers.ValidationError(
                    f"{file.name} 超过大小限制，单文件不得超过 {settings.MAX_UPLOAD_SIZE_MB}MB。"
                )
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        documents = validated_data.pop("documents")
        batch = LessonPlanBatch.objects.create(
            uploader=request.user,
            status=LessonPlanBatch.Status.PROCESSING,
            **validated_data,
        )
        document_ids: list[str] = []

        for index, file in enumerate(documents, start=1):
            document = LessonPlanDocument.objects.create(
                batch=batch,
                slot_number=index,
                title=Path(file.name).stem,
                original_file=file,
                original_filename=file.name,
                file_extension=Path(file.name).suffix.lower(),
                file_size=file.size,
                parse_status=LessonPlanDocument.ParseStatus.PENDING,
            )
            document_ids.append(str(document.id))

        transaction.on_commit(lambda: [dispatch_document_parse(document_id) for document_id in document_ids])

        return batch
