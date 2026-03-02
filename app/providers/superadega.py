from __future__ import annotations

from app.providers.generic_css import GenericCssProvider


def build_superadega_provider() -> GenericCssProvider:
    return GenericCssProvider(
        base_url="https://www.superadega.com.br",
        search_url_template="https://www.superadega.com.br/busca?q={query}",
        card_selector="li.shelf-item",
        card_name_selector=".shelf-item__title, .product-name, h2 a",
        card_link_selector="a",
        card_price_selector=".best-price, .shelf-item__price, .price",
        product_price_selector=".best-price, .price-best-price, .skuBestPrice",
    )
