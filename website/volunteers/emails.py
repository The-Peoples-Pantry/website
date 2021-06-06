from django.conf import settings
from django.urls import reverse
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


class VolunteerOutreachChefSignupsEmail(Email):
    subject = "Chefs needed for The People's Pantry!"
    template = "emails/volunteer_outreach/chef_signups.html"
    reply_to = settings.VOLUNTEER_COORDINATORS_EMAIL
    include_unsubscribe_link = True

    @property
    def extra_context(self):
        return {
            'call_to_action_url': f"https://www.thepeoplespantryto.com{reverse('volunteers:chef_signup_list')}",
        }
