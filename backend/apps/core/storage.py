import mimetypes
from datetime import datetime
from pathlib import PurePosixPath
from urllib.parse import urljoin

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.encoding import filepath_to_uri
from django.utils import timezone


class DatabaseMediaStorage(Storage):
    def _model(self):
        return apps.get_model("core", "StoredMediaFile")

    def _normalize_name(self, name: str) -> str:
        return PurePosixPath(name).as_posix().lstrip("/")

    def _open(self, name: str, mode: str = "rb"):
        stored_file = self._model().objects.get(name=self._normalize_name(name))
        return ContentFile(stored_file.content, name=stored_file.name)

    def _save(self, name: str, content):
        normalized_name = self._normalize_name(name)
        if hasattr(content, "seek"):
            content.seek(0)
        raw_content = content.read()
        content_type = getattr(content, "content_type", "") or mimetypes.guess_type(normalized_name)[0] or ""
        self._model().objects.update_or_create(
            name=normalized_name,
            defaults={
                "content": raw_content,
                "content_type": content_type,
                "size": len(raw_content),
            },
        )
        return normalized_name

    def delete(self, name: str):
        self._model().objects.filter(name=self._normalize_name(name)).delete()

    def exists(self, name: str) -> bool:
        return self._model().objects.filter(name=self._normalize_name(name)).exists()

    def size(self, name: str) -> int:
        return self._model().objects.get(name=self._normalize_name(name)).size

    def url(self, name: str) -> str:
        return urljoin(settings.MEDIA_URL, filepath_to_uri(self._normalize_name(name)))

    def get_modified_time(self, name: str) -> datetime:
        return self._model().objects.get(name=self._normalize_name(name)).updated_at

    def get_created_time(self, name: str) -> datetime:
        return self._model().objects.get(name=self._normalize_name(name)).created_at
