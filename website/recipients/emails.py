from django.conf import settings

from website.emails import Email


class MealRequestConfirmationEmail(Email):
    subject = "Confirming your The People's Pantry request"
    template = ("emails/meals/confirmation.html",)
    reply_to = settings.REQUEST_COORDINATORS_EMAIL
    include_unsubscribe_link = False


class GroceryRequestConfirmationEmail(Email):
    subject = "Confirming your The People's Pantry request"
    template = ("emails/groceries/confirmation.html",)
    reply_to = settings.REQUEST_COORDINATORS_EMAIL
    include_unsubscribe_link = False
