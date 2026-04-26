from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.lesson_plans.models import LessonPlanBatch, LessonPlanDocument
from apps.reviews.models import LessonPlanReview
from apps.reviews.rubric import REVIEW_DIMENSIONS


class ReviewApiTests(APITestCase):
    def setUp(self):
        self.uploader = User.objects.create_user(
            username="uploader_1",
            email="uploader_1@example.com",
            password="StrongPass123!",
            display_name="上传者",
        )
        self.reviewer = User.objects.create_user(
            username="reviewer_1",
            email="reviewer_1@example.com",
            password="StrongPass123!",
            display_name="评价者",
            role="reviewer",
        )
        self.batch = LessonPlanBatch.objects.create(
            title="数学双教案",
            subject="数学",
            grade_level="八年级",
            uploader=self.uploader,
            status=LessonPlanBatch.Status.READY,
            ready_document_count=2,
        )
        for index in (1, 2):
            LessonPlanDocument.objects.create(
                batch=self.batch,
                slot_number=index,
                title=f"教案{index}",
                original_file=f"lesson-plans/demo/{index}.txt",
                original_filename=f"{index}.txt",
                file_extension=".txt",
                file_size=128,
                parse_status=LessonPlanDocument.ParseStatus.READY,
                extracted_text="内容",
                rendered_html="<p>内容</p>",
                page_count=1,
                word_count=2,
            )

        self.authenticate_as("reviewer_1", "StrongPass123!")

    def authenticate_as(self, username: str, password: str):
        login_response = self.client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    def build_payload(self):
        return {
            "recommendation": "recommend",
            "overall_comment": "整体设计完整，活动较为扎实。",
            "comparative_comment": "第二份教案的活动展开更丰富。",
            "strengths": "目标明确，环节流畅。",
            "improvement_suggestions": "可加强形成性评价证据设计。",
            "dimension_scores": [
                {"dimension_key": item["key"], "score_a": 7, "score_b": 9, "comment": f"{item['label']}表现稳定"}
                for item in REVIEW_DIMENSIONS
            ],
        }

    def test_submit_review_updates_batch_summary(self):
        response = self.client.post(
            f"/api/reviews/batches/{self.batch.id}/my-review/",
            self.build_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.batch.refresh_from_db()
        review = LessonPlanReview.objects.get(batch=self.batch, reviewer=self.reviewer)
        self.assertEqual(review.total_score_a, Decimal("7.00"))
        self.assertEqual(review.total_score_b, Decimal("9.00"))
        self.assertEqual(review.total_score, Decimal("8.00"))
        self.assertEqual(self.batch.review_count, 1)
        self.assertEqual(self.batch.average_total_score, Decimal("8.00"))

    def test_uploader_can_submit_self_review(self):
        self.authenticate_as("uploader_1", "StrongPass123!")

        response = self.client.post(
            f"/api/reviews/batches/{self.batch.id}/my-review/",
            self.build_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(LessonPlanReview.objects.filter(batch=self.batch, reviewer=self.uploader).exists())

    def test_non_uploader_cannot_view_summary_for_other_users_batch(self):
        self.client.post(
            f"/api/reviews/batches/{self.batch.id}/my-review/",
            self.build_payload(),
            format="json",
        )

        response = self.client.get(f"/api/batches/{self.batch.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["can_view_review_summary"])
        self.assertIsNone(response.data["review_summary"])
        self.assertIsNone(response.data["average_total_score"])
        self.assertIsNone(response.data["review_count"])

    def test_uploader_can_view_summary_for_own_batch(self):
        self.client.post(
            f"/api/reviews/batches/{self.batch.id}/my-review/",
            self.build_payload(),
            format="json",
        )
        self.authenticate_as("uploader_1", "StrongPass123!")

        response = self.client.get(f"/api/batches/{self.batch.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["can_view_review_summary"])
        self.assertIsNotNone(response.data["review_summary"])
