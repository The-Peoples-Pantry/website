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

    def mass_send(self):
        # Avoid circular imports
        from recipients.models import MealRequest
        from volunteers.models import Volunteer, VolunteerRoles

        num_requests = MealRequest.active_requests()
        chefs = Volunteer.group_for_role(VolunteerRoles.CHEFS).user_set.all()
        return [
            self.send(chef.email, {"user": chef, "num_requests": num_requests})
            for chef in chefs
        ]
