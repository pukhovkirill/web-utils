from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError

from parser.save_strategies import Writer
from parser.scraper import WebScraper


class DummyWriter(Writer):
    """A writer that does nothing."""

    def write(self, data, filename):
        """Do nothing."""
        pass


class SpyWriter(DummyWriter):
    """A writer that records write calls."""

    def __init__(self):
        """Initialize call history."""
        super().__init__()
        self.calls = []

    def write(self, data, filename):
        """Record the data and filename."""
        self.calls.append((data, filename))


def test_init_with_invalid_strategy():
    """
    WebScraper initialization should raise TypeError
    when provided with an invalid save_strategy.
    """
    with pytest.raises(TypeError) as exc_info:
        WebScraper(save_strategy=object())
    assert "save_strategy" in str(exc_info.value)


def test_fetch_sets_soup(monkeypatch):
    """
    fetch() should set the `soup` attribute to a BeautifulSoup instance
    and parse the HTML content correctly.
    """
    mock_response = MagicMock()
    mock_response.text = (
        "<html><body><div id='test'>OK</div></body></html>"
    )
    mock_response.raise_for_status.return_value = None
    monkeypatch.setattr(
        "parser.scraper.requests.get",
        lambda url: mock_response
    )

    scraper = WebScraper(save_strategy=DummyWriter())
    scraper.fetch("https://example.com")

    assert isinstance(scraper.soup, BeautifulSoup)
    assert scraper.soup.find(id="test").text == "OK"


def test_fetch_raises_http_error(monkeypatch):
    """
    fetch() should propagate HTTPError if the response status is bad.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError
    monkeypatch.setattr(
        "parser.scraper.requests.get",
        lambda url: mock_response
    )

    scraper = WebScraper(save_strategy=DummyWriter())
    with pytest.raises(HTTPError):
        scraper.fetch("https://example.com")


def test_parse_without_fetch_raises():
    """
    parse() should raise RuntimeError if called before fetch().
    """
    scraper = WebScraper(save_strategy=DummyWriter())
    with pytest.raises(RuntimeError) as exc_info:
        scraper.parse(".item", {"field": "span"})
    assert "fetch" in str(exc_info.value).lower()


def test_parse_extracts_data(monkeypatch):
    """
    parse() should extract data according to the given CSS selectors.
    """
    html = (
        "<html><body>"
        "<div class='product_pod'>"
        "<a class='title' title='Book One'>Link</a>"
        "<p class='price_color'>£10.00</p>"
        "</div>"
        "<div class='product_pod'>"
        "<a class='title' title='Book Two'>Link</a>"
        "<p class='price_color'>£20.00</p>"
        "</div>"
        "</body></html>"
    )
    mock_response = MagicMock()
    mock_response.text = html
    mock_response.raise_for_status.return_value = None
    monkeypatch.setattr(
        "parser.scraper.requests.get",
        lambda url: mock_response
    )

    scraper = WebScraper(save_strategy=DummyWriter())
    scraper.fetch("https://example.com")
    scraper.parse(
        item_selector=".product_pod",
        fields={
            "title": "a.title",
            "price": "p.price_color",
        },
    )

    expected = [
        {"title": ["Book One"], "price": ["£10.00"]},
        {"title": ["Book Two"], "price": ["£20.00"]},
    ]
    assert scraper.data == expected


def test_save_without_data_raises():
    """
    save() should raise RuntimeError if no data is present.
    """
    scraper = WebScraper(save_strategy=DummyWriter())
    with pytest.raises(RuntimeError) as exc_info:
        scraper.save("output.json")
    assert "no data" in str(exc_info.value).lower()


def test_save_calls_writer_write():
    """
    save() should call the writer's write() method with
    the current data and the provided filename.
    """
    spy = SpyWriter()
    scraper = WebScraper(save_strategy=spy)
    scraper.data = [{"foo": "bar"}]

    filename = "output.json"
    scraper.save(filename)

    assert len(spy.calls) == 1
    data, name = spy.calls[0]
    assert data == [{"foo": "bar"}]
    assert name == filename
