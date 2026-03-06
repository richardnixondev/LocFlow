from django.db import connection, migrations


def create_trgm_index(apps, schema_editor):
    if connection.vendor == "postgresql":
        schema_editor.execute(
            "CREATE INDEX IF NOT EXISTS idx_source_text_trgm "
            "ON resources_translatablestring "
            "USING gin (source_text gin_trgm_ops);"
        )


def drop_trgm_index(apps, schema_editor):
    if connection.vendor == "postgresql":
        schema_editor.execute("DROP INDEX IF EXISTS idx_source_text_trgm;")


class Migration(migrations.Migration):

    dependencies = [
        ("translations", "0002_enable_pg_trgm"),
        ("resources", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_trgm_index, drop_trgm_index),
    ]
