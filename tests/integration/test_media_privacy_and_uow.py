from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from api.app import create_app
from engine.config import Settings
from integrations.database.uow import DatabaseUnitOfWork, repository_session


class _Base(DeclarativeBase):
    pass


class _Item(_Base):
    __tablename__ = "uow_test_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


def _client(tmp_path: Path) -> TestClient:
    settings = Settings(
        environment="development",
        knowledge_path=Path("knowledge"),
        auth_required=True,
        auth_secret="test-secret-that-is-long-enough",
        auth_store_path=tmp_path / "users.json",
        media_storage_path=tmp_path / "media",
        admin_password="change-me-now",
    )
    return TestClient(create_app(settings))


def _register(client: TestClient, username: str) -> dict[str, str]:
    password = "a-secure-password"
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_controlled_media_upload_read_and_ownership(tmp_path: Path) -> None:
    client = _client(tmp_path)
    farmer_headers = _register(client, "farmer-1")
    other_headers = _register(client, "farmer-2")
    image = b"\xff\xd8\xff" + b"controlled-evidence"

    uploaded = client.post(
        "/api/v1/media/images",
        headers=farmer_headers,
        data={"farmer_id": "farmer-1", "crop_id": "tomato"},
        files={"file": ("field.jpg", image, "image/jpeg")},
    )
    assert uploaded.status_code == 201
    image_id = uploaded.json()["image_id"]
    assert not (tmp_path / "media" / "field.jpg").exists()

    response = client.get(f"/api/v1/media/images/{image_id}", headers=farmer_headers)
    assert response.status_code == 200
    assert response.content == image
    assert response.headers["cache-control"] == "private, no-store"

    forbidden = client.get(f"/api/v1/media/images/{image_id}", headers=other_headers)
    assert forbidden.status_code == 403


def test_mobile_rejects_uncontrolled_image_reference(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = _register(client, "farmer-1")
    payload = {
        "farmer_id": "farmer-1",
        "crop_id": "tomato",
        "question": "How should I care for this tomato crop?",
        "region": "West",
        "evidence": {"image_references": ["not-uploaded-image"]},
    }
    response = client.post("/api/v1/advisory/mobile", headers=headers, json=payload)
    assert response.status_code == 400


def test_privacy_delete_invalidates_farmer_account(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = _register(client, "farmer-1")
    summary = client.get("/api/v1/privacy/me", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["retention_days"]["image"] == 180

    deleted = client.delete("/api/v1/privacy/me?confirm=DELETE", headers=headers)
    assert deleted.status_code == 200
    assert client.get("/api/v1/privacy/me", headers=headers).status_code == 401


def test_database_uow_rolls_back_all_repository_sessions(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'uow.db'}")
    _Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    uow = DatabaseUnitOfWork(sessions)

    try:
        with uow.transaction():
            with repository_session(sessions, write=True) as session:
                session.add(_Item(id=1, name="first"))
            with repository_session(sessions, write=True) as session:
                session.add(_Item(id=2, name="second"))
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass

    with sessions() as session:
        assert session.scalars(select(_Item)).all() == []

    with uow.transaction(), repository_session(sessions, write=True) as session:
        session.add(_Item(id=3, name="committed"))

    with sessions() as session:
        assert [item.name for item in session.scalars(select(_Item)).all()] == ["committed"]


def test_media_metadata_and_delete(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = _register(client, "farmer-3")
    image = b"\x89PNG\r\n\x1a\n" + b"png-evidence"
    uploaded = client.post(
        "/api/v1/media/images",
        headers=headers,
        data={"farmer_id": "farmer-3"},
        files={"file": ("soil.png", image, "image/png")},
    )
    image_id = uploaded.json()["image_id"]
    metadata = client.get(f"/api/v1/media/images/{image_id}/metadata", headers=headers)
    assert metadata.status_code == 200
    assert metadata.json()["mime_type"] == "image/png"
    removed = client.delete(f"/api/v1/media/images/{image_id}", headers=headers)
    assert removed.status_code == 204
    assert client.get(f"/api/v1/media/images/{image_id}", headers=headers).status_code == 404


def test_readiness_reports_in_memory_runtime(tmp_path: Path) -> None:
    client = _client(tmp_path)
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] is True
    assert body["migration"]["ready"] is True
