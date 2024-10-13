import os

import httpx
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv("../../.env")

class Search:
    def __init__(self, api_key: str = os.getenv("SEARCH_TOKEN"),
                 search_engine_id: str = os.getenv("SEARCH_ID"), **kwargs):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.endpoint = "https://www.googleapis.com/customsearch/v1"

        self.additional_prompt = kwargs.get("additional_prompt")
        self.query = kwargs.get("query")

    def search(self, query: str):
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query
        }
        try:
            with httpx.Client() as client:
                response = client.get(self.endpoint, params=params)
                response.raise_for_status()
                data = response.json()
                links = []
                for item in data.get("items", []):
                    links.append(item.get("link"))
                return links
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
        except httpx.RequestError as e:
            print(f"Request error occurred: {e}")

    @staticmethod
    def retrieve(links):
        texts = []

        for link in links:
            try:
                response = requests.get(link)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                page_text = soup.get_text(separator=' ', strip=True)
                texts.append(page_text)

            except requests.exceptions.RequestException as e:
                texts.append(f"Error fetching {link}: {e}")

        return texts

    def review(self):
        to_review = Search.retrieve(self.search(self.query))

        result = f"QUERY: {self.query}, TEXT_LIST: ["
        for text in to_review:
            result += f"'{text[:3000]}...', "
        result += "]"

        from explore.src.main import request_mlxai
        response = request_mlxai("gpt-4o-mini", f"Additional Prompt: {self.additional_prompt}, " + result)
        return response

s = Search(query="top news", additional_prompt="What are the top news articles today?")
print(s.review())