from django.db import migrations, models

import easyshard.encrypted_fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ShardConfig",
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
                (
                    "shard_id",
                    models.CharField(db_index=True, max_length=64, unique=True, verbose_name="shard ID"),
                ),
                (
                    "db_alias",
                    models.CharField(max_length=64, unique=True, verbose_name="database alias"),
                ),
                (
                    "engine",
                    models.CharField(
                        default="django.db.backends.postgresql",
                        max_length=128,
                        verbose_name="engine",
                    ),
                ),
                ("name", models.CharField(max_length=128, verbose_name="database name")),
                ("host", models.CharField(max_length=256, verbose_name="host")),
                ("port", models.IntegerField(verbose_name="port")),
                ("user", models.CharField(max_length=128, verbose_name="user")),
                (
                    "password",
                    easyshard.encrypted_fields.EncryptedCharField(max_length=256, verbose_name="password"),
                ),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="active")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "shard config",
                "verbose_name_plural": "shard configs",
                "db_table": "easyshard_shardconfig",
                "ordering": ["shard_id"],
            },
        ),
    ]
