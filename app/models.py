from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class Tracker:
    id: str
    wine_name: str
    site: str
    start_date: date
    end_date: date
    product_url: str | None = None
    product_name: str | None = None
    last_price: float | None = None
    currency: str = "BRL"
    active: bool = True

    def is_active_on(self, today: date) -> bool:
        return self.active and self.start_date <= today <= self.end_date


@dataclass
class Observation:
    tracker_id: str
    checked_at: datetime
    price: float
    currency: str
    product_url: str
    product_name: str | None = None


@dataclass
class DropAlert:
    tracker: Tracker
    previous_price: float
    current_price: float
    checked_at: datetime

    @property
    def drop_percent(self) -> float:
        if self.previous_price <= 0:
            return 0.0
        return (self.previous_price - self.current_price) / self.previous_price * 100


@dataclass
class State:
    trackers: list[Tracker] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "State":
        trackers = []
        for item in raw.get("trackers", []):
            trackers.append(
                Tracker(
                    id=item["id"],
                    wine_name=item["wine_name"],
                    site=item["site"],
                    start_date=date.fromisoformat(item["start_date"]),
                    end_date=date.fromisoformat(item["end_date"]),
                    product_url=item.get("product_url"),
                    product_name=item.get("product_name"),
                    last_price=item.get("last_price"),
                    currency=item.get("currency", "BRL"),
                    active=item.get("active", True),
                )
            )

        observations = []
        for item in raw.get("observations", []):
            observations.append(
                Observation(
                    tracker_id=item["tracker_id"],
                    checked_at=datetime.fromisoformat(item["checked_at"]),
                    price=item["price"],
                    currency=item["currency"],
                    product_url=item["product_url"],
                    product_name=item.get("product_name"),
                )
            )

        return State(trackers=trackers, observations=observations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trackers": [
                {
                    "id": t.id,
                    "wine_name": t.wine_name,
                    "site": t.site,
                    "start_date": t.start_date.isoformat(),
                    "end_date": t.end_date.isoformat(),
                    "product_url": t.product_url,
                    "product_name": t.product_name,
                    "last_price": t.last_price,
                    "currency": t.currency,
                    "active": t.active,
                }
                for t in self.trackers
            ],
            "observations": [
                {
                    "tracker_id": o.tracker_id,
                    "checked_at": o.checked_at.isoformat(),
                    "price": o.price,
                    "currency": o.currency,
                    "product_url": o.product_url,
                    "product_name": o.product_name,
                }
                for o in self.observations
            ],
        }
