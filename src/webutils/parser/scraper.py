from typing import Optional, List, Dict, Any

import requests
from bs4 import BeautifulSoup

from webutils.parser.save_strategies import Writer


class WebScraper:
    """A simple web scraper that fetches HTML, parses data, and saves results."""

    def __init__(self, save_strategy: Writer) -> None:
        """
        Initialize the WebScraper with a save strategy.

        :param save_strategy: An instance of SaveStrategy to save parsed data.
        :raises TypeError: If save_strategy is not an instance of SaveStrategy.
        """
        if not isinstance(save_strategy, Writer):
            raise TypeError("save_strategy must be an instance of SaveStrategy")
        self.save_strategy: Writer = save_strategy
        self.soup: Optional[BeautifulSoup] = None
        self.data: List[Dict[str, Any]] = []

    def fetch(self, url: str) -> None:
        """
        Fetch the HTML content from a URL and parse it with BeautifulSoup.

        :param url: The URL to fetch.
        :raises HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        response = requests.get(url)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.text, "html.parser")

    def parse(self, item_selector: str, fields: Dict[str, str]) -> None:
        """
        Parse HTML content to extract data based on CSS selectors.

        :param item_selector: CSS selector for each item block (e.g., '.product_pod').
        :param fields: Mapping of field names to selectors relative to each item.
        :raises RuntimeError: If HTML has not been fetched before parsing.
        """
        if self.soup is None:
            raise RuntimeError("HTML content is not loaded. Call fetch() before parse().")

        self.data = []
        for item in self.soup.select(item_selector):
            parsed_item: Dict[str, List] = {}
            for field_name, selector in fields.items():
                parsed_item[field_name] = []
                elements = item.select(selector)
                for element in elements:
                    if element is None:
                        parsed_item[field_name] = None
                    elif field_name == "title" and element.has_attr("title"):
                        parsed_item[field_name].append(element["title"])
                    else:
                        parsed_item[field_name].append(element.get_text(separator=";", strip=True))
            self.data.append(parsed_item)

    def save(self, filename: str) -> None:
        """
        Save the parsed data to a file using the provided save strategy.

        :param filename: The name of the output file.
        :raises RuntimeError: If there is no data to save.
        """
        if not self.data:
            raise RuntimeError("No data available to save.")
        self.save_strategy.write(self.data, filename)
