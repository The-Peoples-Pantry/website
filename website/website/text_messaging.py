import logging
import requests

from website.settings import TEXTLINE_API_KEY


logger = logging.getLogger(__name__)


class TextMessagingAPIException(Exception):
    pass


class TextMessagingAPI:
    API_BASE_URL = "https://application.textline.com/api"

    def __init__(self, api_key=TEXTLINE_API_KEY):
        self.api_key = api_key

    def send_text(self, phone_number, message):
        """Send a message to the phone number"""
        if self.api_key is None:
            raise TextMessagingAPIException("Textline API key is not set")

        try:
            response = requests.post(
                f"{self.API_BASE_URL}/conversations.json",
                json={
                    "phone_number": phone_number,
                    "comment": {
                        "body": message,
                    },
                },
                headers={
                    "X-TGP-ACCESS-TOKEN": self.api_key,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise TextMessagingAPIException from e


def send_text(phone_number: str, message: str, fail_silently=True):
    """Text the message to the phone number"""
    try:
        api = TextMessagingAPI()
        api.send_text(phone_number, message)
    except TextMessagingAPIException:
        logger.exception("Failed to send text message to %s", phone_number)
