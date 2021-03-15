import logging
import requests

from django.conf import settings


logger = logging.getLogger(__name__)


class TextMessagingAPIException(Exception):
    pass


class TextMessagingAPI:
    API_BASE_URL = "https://application.textline.com/api"
    GROUPS = {
        "default": "a3019415-c4d3-4de9-8374-103e8ba690b9",
        "groceries": "0d427662-aba2-4e4c-9bfb-0bb846f2353a",
    }

    def __init__(self, access_token=settings.TEXTLINE_ACCESS_TOKEN):
        self.access_token = access_token

    def send_text(self, phone_number, message, group_name):
        """Send a message to the phone number"""
        if self.access_token is None:
            raise TextMessagingAPIException("Textline access token is not set")

        try:
            group_uuid = self.GROUPS[group_name]
        except KeyError:
            raise TextMessagingAPIException("Invalid group_name")

        try:
            response = requests.post(
                f"{self.API_BASE_URL}/conversations.json",
                json={
                    "group_uuid": group_uuid,
                    "phone_number": phone_number,
                    "comment": {
                        "body": message,
                    },
                },
                headers={
                    "X-TGP-ACCESS-TOKEN": self.access_token,
                },
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise TextMessagingAPIException from e


def send_text(phone_number: str, message: str, group_name: str = "default"):
    """Text the message to the phone number"""
    try:
        api = TextMessagingAPI()
        api.send_text(phone_number, message, group_name)
    except TextMessagingAPIException:
        logger.exception("Failed to send text message to %s", phone_number)
