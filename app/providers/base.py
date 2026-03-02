from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProductResult:
    name: str
    url: str
    price: float
    currency: str = "BRL"


class SiteProvider:
    def find_product(self, wine_name: str) -> ProductResult | None:
        raise NotImplementedError

    def read_price(self, product_url: str) -> ProductResult:
        raise NotImplementedError
