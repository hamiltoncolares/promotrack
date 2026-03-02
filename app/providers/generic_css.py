from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.providers.base import ProductResult, SiteProvider


_PRICE_RE = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})")


def _parse_brl_price(text: str) -> float:
    match = _PRICE_RE.search(text)
    if not match:
        raise ValueError(f"Nao foi possivel extrair preco de: {text!r}")
    raw = match.group(1).replace(".", "").replace(",", ".")
    return float(raw)


class GenericCssProvider(SiteProvider):
    def __init__(
        self,
        base_url: str,
        search_url_template: str,
        card_selector: str,
        card_name_selector: str,
        card_link_selector: str,
        card_price_selector: str,
        product_price_selector: str,
        timeout_seconds: int = 20,
    ):
        self.base_url = base_url
        self.search_url_template = search_url_template
        self.card_selector = card_selector
        self.card_name_selector = card_name_selector
        self.card_link_selector = card_link_selector
        self.card_price_selector = card_price_selector
        self.product_price_selector = product_price_selector
        self.timeout_seconds = timeout_seconds

    def _get_soup(self, url: str) -> BeautifulSoup:
        response = requests.get(
            url,
            timeout=self.timeout_seconds,
            headers={"User-Agent": "Mozilla/5.0 PromoTrack/1.0"},
        )
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def find_product(self, wine_name: str) -> ProductResult | None:
        url = self.search_url_template.format(query=wine_name.replace(" ", "+"))
        soup = self._get_soup(url)

        for card in soup.select(self.card_selector):
            name_el = card.select_one(self.card_name_selector)
            link_el = card.select_one(self.card_link_selector)
            price_el = card.select_one(self.card_price_selector)
            if not name_el or not link_el or not price_el:
                continue

            href = link_el.get("href")
            if not href:
                continue

            return ProductResult(
                name=name_el.get_text(" ", strip=True),
                url=urljoin(self.base_url, href),
                price=_parse_brl_price(price_el.get_text(" ", strip=True)),
            )
        return None

    def read_price(self, product_url: str) -> ProductResult:
        soup = self._get_soup(product_url)
        price_el = soup.select_one(self.product_price_selector)
        if not price_el:
            raise ValueError(f"Seletor de preco nao encontrado em {product_url}")

        name = soup.title.get_text(strip=True) if soup.title else product_url
        return ProductResult(
            name=name,
            url=product_url,
            price=_parse_brl_price(price_el.get_text(" ", strip=True)),
        )
