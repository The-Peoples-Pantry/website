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


class MealRequestLotterySelectedEmail(Email):
    subject = "Your meal request for The People's Pantry has been selected"
    template = "emails/meals/lottery/selected.html"
    reply_to = settings.REQUEST_COORDINATORS_EMAIL
    include_unsubscribe_link = False


class MealRequestLotteryNotSelectedEmail(Email):
    subject = "Your meal request for The People's Pantry was not selected"
    template = "emails/meals/lottery/not_selected.html"
    reply_to = settings.REQUEST_COORDINATORS_EMAIL
    include_unsubscribe_link = False
