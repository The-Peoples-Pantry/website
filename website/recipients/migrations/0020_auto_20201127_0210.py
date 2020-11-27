# Generated by Django 3.1.2 on 2020-11-27 02:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0019_auto_20201125_2206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='delivery',
            name='status',
            field=models.CharField(choices=[('Unconfirmed', 'Unconfirmed'), ('Chef Assigned', 'Chef Assigned'), ('Delivery Date Confirmed', 'Delivery Date Confirmed'), ('Driver Assigned', 'Driver Assigned'), ('Recipient Rescheduled', 'Recipient Rescheduled'), ('Delivered', 'Delivered')], default='Unconfirmed', max_length=256, verbose_name='Status'),
        ),
    ]