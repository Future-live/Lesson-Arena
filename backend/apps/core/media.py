import mimetypes
from pathlib import PurePosixPath

from django.core.files.storage import default_storage
from django.http import FileResponse, Http404


def serve_media_file(request, path: str):
    normalized_path = PurePosixPath(path).as_posix().lstrip("/")
    is_unsafe_path = (
        not normalized_path
        or normalized_path == "."
        or normalized_path.startswith("../")
        or "/../" in f"/{normalized_path}"
    )
    if is_unsafe_path:
        raise Http404("Media file not found")

    if not default_storage.exists(normalized_path):
        raise Http404("Media file not found")

    content_type = mimetypes.guess_type(normalized_path)[0] or "application/octet-stream"
    response = FileResponse(default_storage.open(normalized_path, "rb"), content_type=content_type)
    response["Content-Disposition"] = f'inline; filename="{normalized_path.rsplit("/", 1)[-1]}"'
    return response
