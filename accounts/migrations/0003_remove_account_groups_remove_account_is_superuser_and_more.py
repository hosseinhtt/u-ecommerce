# Generated by Django 4.2.5 on 2023-09-23 13:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_account_groups_account_is_superuser_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="account",
            name="groups",
        ),
        migrations.RemoveField(
            model_name="account",
            name="is_superuser",
        ),
        migrations.RemoveField(
            model_name="account",
            name="user_permissions",
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("address_line_1", models.CharField(blank=True, max_length=100)),
                ("address_line_2", models.CharField(blank=True, max_length=100)),
                (
                    "profile_picture",
                    models.ImageField(blank=True, upload_to="userprofile"),
                ),
                ("city", models.CharField(blank=True, max_length=20)),
                ("state", models.CharField(blank=True, max_length=20)),
                ("country", models.CharField(blank=True, max_length=20)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
