import requests

from website.settings import TEXTLINE_API_KEY


class TextMessagingAPIException(Exception):
    pass


class TextMessagingAPI:
    API_BASE_URL = "https://application.textline.com/api"

    def __init__(self, api_key=TEXTLINE_API_KEY):
        self.api_key = api_key

    def send_text(self, phone_number, message):
        """Send a message to the phone number"""
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
