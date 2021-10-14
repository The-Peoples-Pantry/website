# This module is used for overriding settings when running tests
# We re-export all the usual settings values, but override some specific ones
from .settings import *  # noqa: F401,F403

# Disable HTTPS redirect when testing
# This prevents TestCase#client.get from redirecting to https://
SECURE_SSL_REDIRECT = False
