import requests

from utils.constants import HEADERS

def request_html(url: str) -> str | None:
    """Extracts/requests HTML data from a website/url.

    Args:
        URL (str): The website to do a GET request from.

    Returns:
        str: The HTML in Python's readable format, else None if fails.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        return response.text

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None