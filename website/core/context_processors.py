from django.conf import settings as django_settings


# Expose Django settings through the settings context in templates
def settings(request):
    # For safety purposes, we don't expose the entire settings object
    # It has privileged information in it like API keys and passwords which we don't want exposed
    # If someone made a programming mistake, or an attacker found an XSS vulnerability, they could potentially expose those settings
    # This context processor is intended as a convenience, but we want to make sure it is still safe
    SETTINGS_ALLOWED_LIST = (
        'PUBLIC_RELATIONS_EMAIL',
        'REQUEST_COORDINATORS_EMAIL',
        'DELIVERY_COORDINATORS_EMAIL',
        'VOLUNTEER_COORDINATORS_EMAIL',
        'MAX_CHEF_DISTANCE',
        'MEALS_LIMIT',
        'GROCERIES_LIMIT',
    )
    return {
        'settings': {name: getattr(django_settings, name) for name in SETTINGS_ALLOWED_LIST}
    }
