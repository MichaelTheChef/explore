import httpx
import requests
from bs4 import BeautifulSoup

class Search:
    def __init__(self, api_key: str, search_engine_id: str, **kwargs):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.endpoint = "https://www.googleapis.com/customsearch/v1"

        self.action = kwargs.get("action")
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
        assert type(to_review) == list, "The output should be a list"

        for i, text in enumerate(to_review):
            from explore.src.main import request_mlxai
            print(f"Reviewing link {i + 1}...")
            print(request_mlxai("gpt-4o", text))


"""
# Example usage

if __name__ == "__main__":

    api_key = "YOUR_API_KEY"
    search_engine_id = "YOUR_SEARCH_ENGINE_ID"
    client = GoogleClient(api_key, search_engine_id)
    query = "Python programming"
    links = client.search(query)

    # Print the links
    for i in range(len(links)):
        print(f"Link {i + 1}: {links[i]}")
"""