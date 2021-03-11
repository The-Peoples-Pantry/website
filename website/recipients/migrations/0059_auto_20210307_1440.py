# Generated by Django 3.1.2 on 2021-03-07 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0058_auto_20210305_1905'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groceryrequest',
            name='num_adults',
            field=models.PositiveSmallIntegerField(help_text='We consider anyone 13 years of age or older to be an adult', verbose_name='Number of adults in the household'),
        ),
        migrations.AlterField(
            model_name='groceryrequest',
            name='num_children',
            field=models.PositiveSmallIntegerField(help_text='Children under the age of 13', verbose_name='Number of children in the household'),
        ),
    ]