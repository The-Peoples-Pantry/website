# Copy the data in MealDeliveryComments into the associated MealRequest
# We will shortly be deprecating the MealDelivery model
from django.db import migrations


def copy_data_from_meal_delivery_comments_to_meal_request_comments(apps, schema_editor):
    MealDeliveryComment = apps.get_model('recipients', 'MealDeliveryComment')
    db_alias = schema_editor.connection.alias

    for meal_delivery_comment in MealDeliveryComment.objects.using(db_alias).all():
        meal_delivery = meal_delivery_comment.subject
        meal_request = meal_delivery.request
        meal_request.comments.create(
            author=meal_delivery_comment.author,
            comment=meal_delivery_comment.comment,
            created_at=meal_delivery_comment.created_at,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0069_transfer_meal_delivery_to_meal_request'),
    ]

    operations = [
        migrations.RunPython(copy_data_from_meal_delivery_comments_to_meal_request_comments),
    ]
