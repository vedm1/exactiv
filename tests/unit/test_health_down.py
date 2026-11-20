import httpx
from exaktiv_api.main import app
from exaktiv_core.settings import Settings, get_settings

PASSWORD = "pw-sentinel-9f3a"


def dead_settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        postgres_host="127.0.0.1",
        postgres_port=1,
        postgres_password=PASSWORD,  # type: ignore[arg-type]
        minio_endpoint="http://127.0.0.1:1",
        minio_access_key="ak-sentinel",  # type: ignore[arg-type]
        minio_secret_key="sk-sentinel",  # type: ignore[arg-type]
    )


async def test_health_reports_down() -> None:
    app.dependency_overrides[get_settings] = dead_settings
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            response = await client.get("/health")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    body = response.json()
    assert body["postgres"] == body["minio"] == body["dbos"] == "down"
    for leak in (PASSWORD, "sk-sentinel", "ak-sentinel", "127.0.0.1"):
        assert leak not in response.text
