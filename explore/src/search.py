import os

import requests
from bs4 import BeautifulSoup
from cachetools import cached, TTLCache
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from explore.src.main import logging
from explore.src.screenshot import handle_screenshot_and_request

load_dotenv("../../.env")

class Search:
    def __init__(self, api_key: str = os.getenv("SEARCH_TOKEN"),
                 search_engine_id: str = os.getenv("SEARCH_ID"), **kwargs):
        """
        Initialize Search object with API key and search engine ID

        Args:
            api_key (str): Google Custom Search API key
            search_engine_id (str): Google Custom Search Engine ID
            **kwargs: Additional parameters
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.endpoint = "https://www.googleapis.com/customsearch/v1"
        self.cache = TTLCache(maxsize=100, ttl=300)

        self.additional_prompt = kwargs.get("additional_prompt") or "None"
        self.query = kwargs["query"]

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def search(self, query: str):
        """
        Search for query using Google Custom Search API

        Args:
            query (str): Search query
        """
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query
        }

        try:
            response = requests.get(self.endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            links = [item.get("link") for item in data.get("items", [])][:5]
            logging.info(f"Search results for {query}: {links}")
            return links
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error occurred during search: {e}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error occurred during search: {e}")

        return []

    def retrieve(self, links):
        """
        Retrieve text content from a list of links

        Args:
            links (list): List of URLs to retrieve text content
        """
        texts = []

        # Set up retry strategy
        session = requests.Session()
        retries = Retry(total=0, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        timeout = (5, 10)  # (connect timeout, read timeout)

        for link in links:
            try:
                logging.info(f"Fetching {link}")
                response = session.get(link, timeout=timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                page_text = soup.get_text(separator=' ', strip=True)
                texts.append(page_text)


            except requests.exceptions.RequestException as e:
                logging.error(f"HTTP error fetching {link}, attempting to take screenshot: {e}")
                response = handle_screenshot_and_request(link, self.query)

                if response:
                    texts.append(response)
                    continue

                texts.append(f"Error fetching {link}: HTTP error {response.status_code}")

        return texts

    def review(self):
        """
        Review search results and additional prompt

        Returns:
            str: Response from ML model
        """
        to_review = self.retrieve(self.search(self.query))

        result = f"QUERY: {self.query}, TEXT_LIST: ["
        for text in to_review:
            result += f"'{text[:3000]}...', "
        result += "]"

        from explore.src.main import request_mlxai
        response = request_mlxai("gpt-4o-mini", f"Additional Prompt: {self.additional_prompt}, " + result)
        return response