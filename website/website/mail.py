from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def custom_send_mail(
    subject,
    message,
    recipient_list,
    reply_to=None,
    connection=None,
    html_message=None
):
    """An opinionated variant of Django's built-in send_mail"""
    from_email = settings.DEFAULT_FROM_EMAIL
    reply_to = reply_to or settings.PUBLIC_RELATIONS_EMAIL
    mail = EmailMultiAlternatives(
        subject,
        message,
        from_email,
        recipient_list,
        reply_to=[reply_to],
        connection=connection
    )
    if html_message:
        mail.attach_alternative(html_message, 'text/html')
    return mail.send()
