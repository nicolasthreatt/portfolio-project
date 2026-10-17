from django.db import migrations, models


def populate_slugs(apps, schema_editor):
    Experience = apps.get_model("pages", "Experience")
    records = Experience.objects.using(schema_editor.connection.alias)
    for experience in records.iterator():
        experience.slug = f"experience-{experience.pk}"
        experience.save(update_fields=["slug"], using=schema_editor.connection.alias)


class Migration(migrations.Migration):
    dependencies = [("pages", "0003_add_experience")]

    operations = [
        migrations.AddField(
            model_name="experience",
            name="slug",
            field=models.SlugField(null=True, unique=True),
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="experience",
            name="slug",
            field=models.SlugField(unique=True),
        ),
    ]
