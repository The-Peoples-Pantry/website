# Generated by Django 3.1.2 on 2021-02-05 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("volunteers", "0017_volunteer_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="volunteer",
            name="short_name",
            field=models.CharField(
                blank=True,
                help_text="(Optional) A short version of your name that we will use for your privacy when contacting recipients",
                max_length=256,
                null=True,
                verbose_name="Short name",
            ),
        ),
    ]
