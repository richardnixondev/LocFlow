from django.db import connection, migrations


def enable_pg_trgm(apps, schema_editor):
    if connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")


class Migration(migrations.Migration):

    dependencies = [
        ("translations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(enable_pg_trgm, migrations.RunPython.noop),
    ]
