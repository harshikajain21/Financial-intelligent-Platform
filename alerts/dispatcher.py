"""
Alert Dispatcher — evaluates fusion results and dispatches alerts via
configured channels (email, Slack, webhook, database).
"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from typing import Any

import requests

from config.settings import Settings
from utils.logger import get_logger

logger = get_logger("AlertDispatcher")


_SEVERITY_THRESHOLDS = {
    "strong_sell": "CRITICAL",
    "sell": "WARNING",
    "hold": "INFO",
    "buy": "INFO",
    "strong_buy": "INFO",
}


class AlertDispatcher:
    """Evaluates recommendations and dispatches alerts through configured channels."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate_and_dispatch(self, fusion_result: dict[str, Any]) -> list[dict[str, Any]]:
        """Check each ticker's recommendation and fire alerts where needed.

        Args:
            fusion_result: Output of DecisionFusion.fuse().

        Returns:
            List of dispatched alert dicts.
        """
        dispatched: list[dict[str, Any]] = []

        for ticker, analysis in fusion_result.items():
            rec = analysis.get("recommendation", "hold")
            confidence = analysis.get("confidence", 0.0)
            score = analysis.get("composite_score", 0.0)
            severity = _SEVERITY_THRESHOLDS.get(rec, "INFO")

            # Only alert on actionable signals with sufficient confidence
            if rec in ("strong_buy", "strong_sell") or (
                rec in ("buy", "sell") and confidence >= 0.6
            ):
                alert = {
                    "ticker": ticker,
                    "recommendation": rec,
                    "confidence": confidence,
                    "composite_score": score,
                    "severity": severity,
                    "message": self._format_message(ticker, rec, confidence, score),
                }
                self._dispatch(alert)
                dispatched.append(alert)

        return dispatched

    # ------------------------------------------------------------------
    # Dispatch channels
    # ------------------------------------------------------------------

    def _dispatch(self, alert: dict[str, Any]) -> None:
        """Route alert to all enabled channels."""
        self._log_alert(alert)
        self._save_to_db(alert)

        if self.settings.slack_webhook_url:
            self._send_slack(alert)

        if self.settings.alert_email_to:
            self._send_email(alert)

        if self.settings.alert_webhook_url:
            self._send_webhook(alert)

    def _log_alert(self, alert: dict[str, Any]) -> None:
        msg = alert["message"]
        sev = alert["severity"]
        if sev == "CRITICAL":
            logger.critical(msg)
        elif sev == "WARNING":
            logger.warning(msg)
        else:
            logger.info(msg)

    def _save_to_db(self, alert: dict[str, Any]) -> None:
        try:
            from database.connection import get_db_session
            from database.models import Alert

            with get_db_session() as session:
                record = Alert(
                    ticker=alert["ticker"],
                    alert_type=alert["recommendation"],
                    severity=alert["severity"],
                    message=alert["message"],
                    metadata={
                        "confidence": alert["confidence"],
                        "composite_score": alert["composite_score"],
                    },
                )
                session.add(record)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to save alert to database: %s", exc)

    def _send_slack(self, alert: dict[str, Any]) -> None:
        try:
            payload = {"text": f"*[{alert['severity']}]* {alert['message']}"}
            requests.post(self.settings.slack_webhook_url, json=payload, timeout=10)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Slack alert failed: %s", exc)

    def _send_email(self, alert: dict[str, Any]) -> None:
        try:
            msg = MIMEText(alert["message"])
            msg["Subject"] = f"[FIP Alert] {alert['ticker']} — {alert['recommendation'].upper()}"
            msg["From"] = self.settings.alert_email_from
            msg["To"] = self.settings.alert_email_to

            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.starttls()
                server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Email alert failed: %s", exc)

    def _send_webhook(self, alert: dict[str, Any]) -> None:
        try:
            requests.post(self.settings.alert_webhook_url, json=alert, timeout=10)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Webhook alert failed: %s", exc)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _format_message(ticker: str, rec: str, confidence: float, score: float) -> str:
        return (
            f"[{rec.upper()}] {ticker} — "
            f"Composite score: {score:.4f}, Confidence: {confidence:.1%}"
        )

    def get_recent_alerts(self, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve recent alerts from the database."""
        try:
            from database.connection import get_db_session
            from database.models import Alert

            with get_db_session() as session:
                records = (
                    session.query(Alert)
                    .order_by(Alert.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return [
                    {
                        "id": r.id,
                        "ticker": r.ticker,
                        "alert_type": r.alert_type,
                        "severity": r.severity,
                        "message": r.message,
                        "created_at": r.created_at.isoformat(),
                    }
                    for r in records
                ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to retrieve alerts: %s", exc)
            return []

    def dismiss(self, alert_id: int) -> None:
        """Mark an alert as dismissed in the database."""
        try:
            from database.connection import get_db_session
            from database.models import Alert

            with get_db_session() as session:
                record = session.query(Alert).filter(Alert.id == alert_id).first()
                if record:
                    record.dispatched = 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to dismiss alert %d: %s", alert_id, exc)
