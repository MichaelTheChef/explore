import os
import uuid

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # To download ChromeDriver automatically

from explore.src.main import request_mlxai, logging


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
    response = request_mlxai("gpt-4o-mini", f"QUERY_OF_IMAGE: {query}", screenshot_path)

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

handle_screenshot_and_request("https://www.google.com", "what is google?")