import html2text
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def html_to_text(html_content):
    text_formatter = html2text.HTML2Text()
    text_formatter.ignore_tables = True
    return text_formatter.handle(html_content)


class Email:
    """Mimics Django's TemplateView but for defining emails based on templates"""
    template = None
    subject = None
    reply_to = None
    from_email = settings.DEFAULT_FROM_EMAIL
    include_unsubscribe_link = True

    def __init__(self, connection=None):
        self.connection = connection

    def get_context_data(self, **kwargs):
        base_context_data = {
            'subject': self.subject,
            'include_unsubscribe_link': self.include_unsubscribe_link,
        }
        return {**base_context_data, **kwargs}

    def render_content(self, context):
        html_content = render_to_string(self.template, context)
        text_content = html_to_text(html_content)
        return html_content, text_content

    def send(self, recipient, recipient_context={}):
        context = self.get_context_data(**recipient_context)
        html_content, text_content = self.render_content(context)
        mail = EmailMultiAlternatives(
            self.subject,
            text_content,
            self.from_email,
            [recipient],
            reply_to=[self.reply_to],
            connection=self.connection,
        )
        mail.attach_alternative(html_content, 'text/html')
        return mail.send()
