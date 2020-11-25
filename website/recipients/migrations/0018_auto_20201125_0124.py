# Generated by Django 3.1.2 on 2020-11-25 01:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0017_auto_20201125_0017'),
    ]

    operations = [
        migrations.AddField(
            model_name='groceryrequest',
            name='baked_goods',
            field=models.BooleanField(default=False, help_text='Sometimes we have baked goods to offer in our bundles, would you want baked goods?', verbose_name='Baked goods'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='groceryrequest',
            name='hygiene_products',
            field=models.CharField(blank=True, help_text='Sometimes we are able to include personal hygiene products in our bundles, what personal hygiene products would you want? For example: sanitary pads, shampoo, etc.', max_length=1024, verbose_name='Hygiene products'),
        ),
        migrations.AddField(
            model_name='groceryrequest',
            name='kid_snacks',
            field=models.BooleanField(default=False, help_text="Sometimes we have kid snacks to offer in our bundles, would you want kids' snacks?", verbose_name='Kid snacks'),
            preserve_default=False,
        ),
    ]