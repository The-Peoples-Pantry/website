from django import template
from django.utils.html import mark_safe
import hashlib

register = template.Library()


@register.simple_tag()
def profile_image(user):
    """
    Displays a profile photo for the mentioned user
    Pulls from Gravatar based on the user's email address
    The "d" query param configures the fallback when no profile image is found

    See http://en.gravatar.com/site/implement/images/
    """
    if user.is_anonymous:
        return None

    email_hash = hashlib.md5(user.email.encode('utf8')).hexdigest()
    gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=mp"
    html = f'<img class="profile-image" alt="Profile image" src="{gravatar_url}">'
    return mark_safe(html)
