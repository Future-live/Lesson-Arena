from pathlib import Path

from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction

from apps.lesson_plans.models import LessonPlanDocument
from apps.lesson_plans.services import parse_document


def parse_document_safely(document_id: str, *, raise_errors: bool = False) -> None:
    document = LessonPlanDocument.objects.select_related("batch").get(pk=document_id)
    document.parse_status = LessonPlanDocument.ParseStatus.PROCESSING
    document.parse_error = ""
    document.save(update_fields=["parse_status", "parse_error", "updated_at"])

    try:
        result = parse_document(document)
    except Exception as exc:
        document.parse_status = LessonPlanDocument.ParseStatus.FAILED
        document.parse_error = str(exc)
        document.save(update_fields=["parse_status", "parse_error", "updated_at"])
        document.batch.refresh_processing_status(save=True)
        if raise_errors:
            raise
        return

    with transaction.atomic():
        document.parse_status = LessonPlanDocument.ParseStatus.READY
        document.display_mode = result.display_mode
        document.extracted_text = result.extracted_text
        document.rendered_html = result.rendered_html
        document.word_count = result.word_count
        document.page_count = result.page_count
        document.parse_error = ""
        if result.preview_pdf_bytes:
            preview_name = f"{Path(document.original_filename).stem}.pdf"
            document.preview_file.save(preview_name, ContentFile(result.preview_pdf_bytes), save=False)
        elif document.preview_file:
            document.preview_file.delete(save=False)
        if result.display_mode == LessonPlanDocument.DisplayMode.PDF and not result.preview_pdf_bytes:
            document.rendered_html = ""
        document.save(
            update_fields=[
                "parse_status",
                "display_mode",
                "preview_file",
                "extracted_text",
                "rendered_html",
                "word_count",
                "page_count",
                "parse_error",
                "updated_at",
            ]
        )
        document.batch.refresh_processing_status(save=True)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def parse_document_task(document_id: str) -> None:
    parse_document_safely(document_id, raise_errors=True)
