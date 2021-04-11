# Generated by Django 3.1.2 on 2021-04-08 19:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0066_auto_20210402_1019'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groceryrequest',
            name='gift_card',
            field=models.CharField(choices=[('Walmart', 'Walmart (Digital)'), ("President's Choice", "President's Choice (Physical)")], help_text='We offer both physical (mailed to you) and digital (emailed to you) gift cards. What type of gift card would you want?', max_length=256, verbose_name='Gift card'),
        ),
    ]