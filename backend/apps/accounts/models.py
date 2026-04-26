from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "系统管理员"
        TEACHER = "teacher", "教师"
        REVIEWER = "reviewer", "评价成员"

    email = models.EmailField(unique=True, verbose_name="邮箱")
    display_name = models.CharField(max_length=100, verbose_name="显示名称")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TEACHER,
        verbose_name="角色",
    )
    organization = models.CharField(max_length=150, blank=True, verbose_name="学校/单位")
    title = models.CharField(max_length=100, blank=True, verbose_name="职称/岗位")
    bio = models.TextField(blank=True, verbose_name="个人简介")

    REQUIRED_FIELDS = ["email", "display_name"]

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        ordering = ["username"]

    def __str__(self) -> str:
        return self.display_name or self.username
