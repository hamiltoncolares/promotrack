from __future__ import annotations

from datetime import date, datetime, timezone

from app.config import build_provider
from app.models import DropAlert, Observation, State


class MonitorService:
    def __init__(self, sites_config: dict):
        self.sites_config = sites_config

    def check(self, state: State, today: date | None = None) -> list[DropAlert]:
        today = today or date.today()
        checked_at = datetime.now(timezone.utc)
        alerts: list[DropAlert] = []

        for tracker in state.trackers:
            if not tracker.is_active_on(today):
                continue

            provider = build_provider(tracker.site, self.sites_config)

            if not tracker.product_url:
                found = provider.find_product(tracker.wine_name)
                if not found:
                    continue
                tracker.product_url = found.url
                tracker.product_name = found.name
                current_price = found.price
                currency = found.currency
            else:
                result = provider.read_price(tracker.product_url)
                tracker.product_name = result.name
                current_price = result.price
                currency = result.currency

            if tracker.last_price is not None and current_price < tracker.last_price:
                alerts.append(
                    DropAlert(
                        tracker=tracker,
                        previous_price=tracker.last_price,
                        current_price=current_price,
                        checked_at=checked_at,
                    )
                )

            tracker.last_price = current_price
            tracker.currency = currency
            state.observations.append(
                Observation(
                    tracker_id=tracker.id,
                    checked_at=checked_at,
                    price=current_price,
                    currency=currency,
                    product_url=tracker.product_url or "",
                    product_name=tracker.product_name,
                )
            )

        return alerts
