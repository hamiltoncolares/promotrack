from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from app.models import DropAlert


class Emailer:
    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASS")
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_to = os.getenv("EMAIL_TO")

    def is_configured(self) -> bool:
        required = [self.host, self.user, self.password, self.email_from, self.email_to]
        return all(required)

    def send_drop_alerts(self, alerts: list[DropAlert]) -> None:
        if not alerts:
            return
        if not self.is_configured():
            raise RuntimeError("Variaveis SMTP/EMAIL nao configuradas")

        lines = ["Foram detectadas quedas de preco:", ""]
        for alert in alerts:
            lines.append(
                f"- {alert.tracker.wine_name} ({alert.tracker.site}) | "
                f"R$ {alert.previous_price:.2f} -> R$ {alert.current_price:.2f} "
                f"(-{alert.drop_percent:.2f}%)"
            )
            if alert.tracker.product_url:
                lines.append(f"  URL: {alert.tracker.product_url}")

        msg = EmailMessage()
        msg["Subject"] = f"[PromoTrack] {len(alerts)} queda(s) de preco"
        msg["From"] = self.email_from
        msg["To"] = self.email_to
        msg.set_content("\n".join(lines))

        with smtplib.SMTP(self.host, self.port) as server:
            server.starttls()
            server.login(self.user, self.password)
            server.send_message(msg)
