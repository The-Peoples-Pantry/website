# Generated by Django 3.1.2 on 2021-01-01 22:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volunteers', '0015_volunteerapplication_organizer_teams'),
    ]

    operations = [
        migrations.AddField(
            model_name='volunteer',
            name='organizer_teams',
            field=models.CharField(blank=True, max_length=256, verbose_name='Organizer teams'),
        ),
    ]
