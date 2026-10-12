"""Run one safe proactive SMS cycle; scheduler/container repeats this command."""

from engine.bootstrap import build_container
from engine.config import Settings
from integrations.database.sms_admin_repository import PostgresSMSAdminRepository
from services.proactive_alert_source import KnowledgeBackedProactiveAlertSource
from services.proactive_alerts import ProactiveAlertService


def main() -> None:
    settings = Settings.from_env()
    container = build_container(settings)
    repository = (
        PostgresSMSAdminRepository(container.database.sessions)
        if container.database is not None
        else None
    )
    summary = ProactiveAlertService(
        KnowledgeBackedProactiveAlertSource(container.knowledge),
        repository,
        container.sms,
        enabled=settings.proactive_sms_enabled,
    ).run_once()
    print(f"sent={summary.sent} failed={summary.failed} skipped={summary.skipped}")


if __name__ == "__main__":
    main()
