from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.providers.base import SiteProvider
from app.providers.generic_css import GenericCssProvider
from app.providers.superadega import build_superadega_provider


DEFAULT_SITES = {
    "superadega": {
        "provider": "superadega",
        "enabled": True,
    }
}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        return {}
    raw = yaml.safe_load(content)
    return raw or {}


def ensure_sites_file(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(DEFAULT_SITES, allow_unicode=True, sort_keys=False), encoding="utf-8")


def build_provider(site_name: str, sites_config: dict[str, Any]) -> SiteProvider:
    site_cfg = sites_config.get(site_name)
    if not site_cfg:
        raise ValueError(f"Site '{site_name}' nao configurado")

    provider_name = site_cfg.get("provider")
    if provider_name == "superadega":
        return build_superadega_provider()

    if provider_name == "generic_css":
        return GenericCssProvider(
            base_url=site_cfg["base_url"],
            search_url_template=site_cfg["search_url_template"],
            card_selector=site_cfg["card_selector"],
            card_name_selector=site_cfg["card_name_selector"],
            card_link_selector=site_cfg["card_link_selector"],
            card_price_selector=site_cfg["card_price_selector"],
            product_price_selector=site_cfg["product_price_selector"],
            timeout_seconds=site_cfg.get("timeout_seconds", 20),
        )

    raise ValueError(f"Provider desconhecido para '{site_name}': {provider_name}")
