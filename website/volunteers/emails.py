from django.conf import settings
from website.emails import Email


class VolunteerApplicationConfirmationEmail(Email):
    subject = "Confirming your The People's Pantry volunteer application"
    template = "emails/volunteer_applications/confirmation.html"
    reply_to = settings.VOLUNTEER_COORDINATORS_EMAIL
    include_unsubscribe_link = False


class VolunteerApplicationApprovalEmail(Email):
    subject = "Your volunteer application for The People's Pantry has been approved!"
    template = "emails/volunteer_applications/approval.html"
    reply_to = settings.VOLUNTEER_COORDINATORS_EMAIL
    include_unsubscribe_link = False