from apps.lesson_plans.models import LessonPlanBatch


def is_admin_user(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return bool(
        getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
        or getattr(user, "role", "") == "admin"
    )


def can_view_batch_review_summary(user, batch: LessonPlanBatch) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return is_admin_user(user) or batch.uploader_id == user.id
