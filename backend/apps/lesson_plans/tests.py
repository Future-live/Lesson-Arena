import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.lesson_plans.models import LessonPlanBatch


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, MEDIA_ROOT=tempfile.gettempdir())
class LessonPlanBatchApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="uploader",
            email="uploader@example.com",
            password="StrongPass123!",
            display_name="上传教师",
        )
        login_response = self.client.post(
            "/api/auth/login/",
            {"username": "uploader", "password": "StrongPass123!"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    def test_create_batch_with_two_documents(self):
        document_a = SimpleUploadedFile("lesson-a.txt", "教案A内容".encode("utf-8"), content_type="text/plain")
        document_b = SimpleUploadedFile("lesson-b.md", "# 教案B\n\n内容".encode("utf-8"), content_type="text/markdown")

        response = self.client.post(
            "/api/batches/",
            {
                "title": "测试批次",
                "subject": "语文",
                "grade_level": "七年级",
                "documents": [document_a, document_b],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["documents"]), 2)
        self.assertEqual(response.data["status"], "processing")

        batch = LessonPlanBatch.objects.get(pk=response.data["id"])
        self.assertEqual(batch.status, LessonPlanBatch.Status.PROCESSING)
        self.assertEqual(batch.documents.count(), 2)
