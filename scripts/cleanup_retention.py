"""Run configured retention policies as an operational maintenance command."""

from api.app import create_app


def main() -> None:
    app = create_app()
    result = app.state.retention_service.cleanup()
    print(
        {
            "media": result.media,
            "traces": result.traces,
            "history": result.history,
            "sms": result.sms,
            "audit": result.audit,
        }
    )
    container = app.state.container
    if container.database is not None:
        container.database.close()


if __name__ == "__main__":
    main()
