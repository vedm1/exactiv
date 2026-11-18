import httpx
import pytest
from exaktiv_api.main import app
from exaktiv_core.settings import Settings

pytestmark = pytest.mark.integration


async def test_health(stack_settings: Settings) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert (body["postgres"], body["minio"], body["temporal"]) == ("ok", "ok", "ok")
