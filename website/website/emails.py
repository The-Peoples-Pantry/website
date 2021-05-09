from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class Email:
    def __init__(self, subject, template, context, reply_to, connection=None):
        self.subject = subject
        self.template = template
        self.context = context
        self.reply_to = reply_to
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.connection = connection

    @property
    def html_template(self):
        return f"{self.template}.html"

    @property
    def text_template(self):
        return f"{self.template}.txt"

    def get_context_data(self, **kwargs):
        if self.context is not None:
            kwargs.update(self.context)
        return kwargs

    def render_text_content(self, context):
        return render_to_string(self.text_template, context)

    def render_html_content(self, context):
        return render_to_string(self.html_template, context)

    def send(self, recipient):
        context = self.get_context_data(subject=self.subject)
        text_content = self.render_text_content(context)
        html_content = self.render_html_content(context)
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
