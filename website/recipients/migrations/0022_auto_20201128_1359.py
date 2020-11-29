# Generated by Django 3.1.2 on 2020-11-28 18:59

from django.db import migrations, models
import django.db.models.deletion


# It's possible for there to be two deliveries on a meal request
# One for the food delivery and one for the container
# Delete the container one
# Because we are adding a unique constraint to this column
def delete_container_deliveries(apps, schema_editor):
    Delivery = apps.get_model('recipients', 'Delivery')
    db_alias = schema_editor.connection.alias
    Delivery.objects.using(db_alias).filter(container_delivery=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0021_auto_20201128_0900'),
    ]

    operations = [
        migrations.RunPython(delete_container_deliveries),
        migrations.AlterField(
            model_name='delivery',
            name='request',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='recipients.mealrequest'),
        ),
    ]