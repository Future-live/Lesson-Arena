from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="StoredMediaFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("name", models.CharField(max_length=500, unique=True, verbose_name="文件路径")),
                ("content", models.BinaryField(verbose_name="文件内容")),
                ("content_type", models.CharField(blank=True, max_length=100, verbose_name="内容类型")),
                ("size", models.BigIntegerField(default=0, verbose_name="文件大小")),
            ],
            options={
                "verbose_name": "存储文件",
                "verbose_name_plural": "存储文件",
                "ordering": ["-updated_at"],
            },
        ),
    ]
