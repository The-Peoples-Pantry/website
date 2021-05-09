import html2text
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class Email:
    def __init__(self, subject, template, context, reply_to, include_unsubscribe_link=True, connection=None):
        self.subject = subject
        self.template = template
        self.context = context
        self.reply_to = reply_to
        self.include_unsubscribe_link = include_unsubscribe_link
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.connection = connection

    def get_context_data(self, **kwargs):
        return {
            'subject': self.subject,
            'include_unsubscribe_link': self.include_unsubscribe_link,
            **self.context,
            **kwargs,
        }

    def render_text_content(self, content):
        formatter = html2text.HTML2Text()
        formatter.ignore_tables = True
        return formatter.handle(content)

    def render_html_content(self, context):
        return render_to_string(self.template, context)

    def send(self, recipient):
        context = self.get_context_data()
        html_content = self.render_html_content(context)
        text_content = self.render_text_content(html_content)
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
