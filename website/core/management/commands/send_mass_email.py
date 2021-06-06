from django.core.management.base import BaseCommand

from volunteers.emails import VolunteerOutreachChefSignupsEmail


class Command(BaseCommand):
    help = 'Send mass email'

    def handle(self, *args, **options):
        self.stdout.write('Sending volunteer outreach chef signup mass email')
        results = VolunteerOutreachChefSignupsEmail().mass_send()
        self.stdout.write('Sent to:')
        for result in results:
            for email in result.to:
                self.stdout.write(email)
