# Generated by Django 3.1.2 on 2020-11-17 01:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('volunteers', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='volunteer',
            name='is_chef',
        ),
        migrations.RemoveField(
            model_name='volunteer',
            name='is_coordinator',
        ),
        migrations.RemoveField(
            model_name='volunteer',
            name='is_driver',
        ),
        migrations.RemoveField(
            model_name='volunteer',
            name='training_complete',
        ),
    ]