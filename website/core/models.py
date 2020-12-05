from django.contrib.auth import get_user_model


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]


def has_group(user, group_name: str):
    """Test whether the user is in a group with the given name"""
    return user.groups.filter(name=group_name).exists()


def group_names(user):
    """Returns a list of group names for the user"""
    return list(user.groups.all().values_list('name', flat=True))
