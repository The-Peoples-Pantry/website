# Generated by Django 3.1.2 on 2021-07-05 16:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0080_groceryrequest_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groceryrequest',
            name='completed',
        ),
    ]
