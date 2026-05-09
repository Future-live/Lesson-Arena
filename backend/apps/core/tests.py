from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase


DATABASE_MEDIA_STORAGES = {
    "default": {
        "BACKEND": "apps.core.storage.DatabaseMediaStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


class HealthCheckTests(APITestCase):
    def test_health_check(self):
        response = self.client.get("/api/system/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")


@override_settings(MEDIA_URL="/media/", SERVE_MEDIA_FILES=True, STORAGES=DATABASE_MEDIA_STORAGES)
class MediaFileServingTests(APITestCase):
    def test_media_file_is_served_from_default_storage_without_frame_blocking_header(self):
        default_storage.save("lesson-plans/test/previews/1.pdf", ContentFile(b"%PDF-1.4\n"))

        response = self.client.get("/api/media/lesson-plans/test/previews/1.pdf")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertNotIn("X-Frame-Options", response)
