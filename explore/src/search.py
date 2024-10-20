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
    def search(self, query: str, max_results: int = 100, start: int = None):
        """
        Search for query using Google Custom Search API and retrieve up to max_results links.

        Args:
            query (str): Search query
            max_results (int): Maximum number of results to fetch (default: 1000)
            start (int): Start index for search (default: None)
        """
        links = []

        def fetch_links(start):
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "start": start
            }
            try:
                response = requests.get(self.endpoint, params=params)
                response.raise_for_status()
                data = response.json()
                links.extend([item.get("link") for item in data.get("items", [])])
                logging.info(f"Fetched {len(data.get('items', []))} results starting from {start}")
                return len(data.get("items", []))
            except requests.exceptions.HTTPError as e:
                logging.error(f"HTTP error occurred during search: {e}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error occurred during search: {e}")
            return 0

        if start is None:
            for start in range(1, max_results, 10):
                if fetch_links(start) < 10:
                    break
        else:
            fetch_links(start)

        return links[:max_results]

    def retrieve(self, links):
        """
        Retrieve text content from a list of links

        Args:
            links (list): List of URLs to retrieve text content
        """
        texts = []
        already_fetched = set()
        session = requests.Session()
        retries = Retry(total=0, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        timeout = (5, 10)

        for link in links:
            try:
                logging.info(f"Fetching {link}")
                if link in already_fetched:
                    continue
                already_fetched.add(link)
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
                else:
                    texts.append(f"Error fetching {link}")

        return texts

    def review(self, **kwargs):
        """
        Review search results and additional prompt

        Returns:
            str: Response from ML model
        """
        to_review = self.retrieve(self.search(self.query, kwargs.get("max_results", 10), kwargs.get("page", 1)))
        result = f"QUERY: {self.query}, TEXT_LIST: ["
        for text in to_review:
            result += f"'{text[:3000]}...', "
        result += "]"
        from explore.src.main import request_mlxai
        response = request_mlxai("gpt-4o-mini", f"Additional Prompt: {self.additional_prompt}, " + result)
        return response.replace("#", "")