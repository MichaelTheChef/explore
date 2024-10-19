import os
import uuid

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    TextContentItem,
    ImageContentItem,
    ImageUrl,
    ImageDetailLevel,
)
from azure.core.credentials import AzureKeyCredential
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # To download ChromeDriver automatically

from explore.src.main import logging


def describe_image(query, image_file: str, image_format: str):
    """
    Describe an image using the ML model.

    Args:
        query (str): The query to send to the ML model.
        image_file (str): The path to the image file.
        image_format (str): The format of the image file.

    Returns:
        str: The description of the image.
    """
    token = os.getenv("GITHUB_TOKEN")
    endpoint = "https://models.inference.ai.azure.com"
    model_name = "gpt-4o-mini"

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    response = client.complete(
        messages=[
            SystemMessage(
                content="QUERY_OF_IMAGE: '<the query related to the image>' Extract the necessary text from the image that helps answer the QUERY_OF_IMAGE and return it separately as well-structured, readable text."
            ),
            UserMessage(
                content=[
                    TextContentItem(text=f"QUERY_OF_IMAGE: {query}"),
                    ImageContentItem(
                        image_url=ImageUrl.load(
                            image_file=image_file,
                            image_format=image_format,
                            detail=ImageDetailLevel.LOW,
                        ),
                    ),
                ],
            ),
        ],
        model=model_name,
    )

    return response.choices[0].message.content


def take_ss(url, save_path):
    """
    Take a screenshot of a webpage and save it to the specified path.

    Args:
        url (str): The URL of the webpage to take a screenshot of.
        save_path (str): The path to save the screenshot image.
    """
    screenshot_taker = Screenshot(headless=True)
    screenshot_taker.take_screenshot(url, save_path)
    screenshot_taker.close()


def handle_screenshot_and_request(link, query):
    """
    Handle taking a screenshot of a webpage and sending it to the ML model for processing.

    Args:
        link (str): The URL of the webpage to take a screenshot of.
        query (str): The query to send to the ML model.
    """
    uid = uuid.uuid4()
    screenshot_dir = os.path.abspath("screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)  # Create directory if it doesn't exist
    screenshot_path = os.path.join(screenshot_dir, f"screenshot-{uid}.png")

    take_ss(link, screenshot_path)
    response = describe_image(query, screenshot_path, "png")
    os.remove(screenshot_path)

    return response


class Screenshot:
    def __init__(self, headless: bool = True):
        """
        Initialize the Screenshot class.

        Args:
            headless (bool): Whether to run the browser in headless mode (default: True).
        """
        self.headless = headless
        self.driver = None

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def take_screenshot(self, url: str, save_path: str):
        """
        Takes a screenshot of the specified webpage.

        Args:
            url (str): The URL of the webpage to take a screenshot of.
            save_path (str): The path to save the screenshot image.
        """
        try:
            self.driver.get(url)

            self.driver.save_screenshot(save_path)
            logging.info(f"Screenshot saved to {save_path}")

        except Exception as e:
            logging.error(f"Error taking screenshot: {e}")

    def close(self):
        """
        Closes the browser instance.
        """
        if self.driver:
            self.driver.quit()